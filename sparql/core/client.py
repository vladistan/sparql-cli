"""SPARQL endpoint client using httpx."""

import re
from collections.abc import Iterator

import httpx
import sentry_sdk

from sparql.core.exceptions import NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.logging import get_logger
from sparql.core.models import BindingValue, QueryResult, UpdateResult


def _is_rdf_query(query: str) -> bool:
    """Detect if query is CONSTRUCT or DESCRIBE (returns RDF graph)."""
    query_upper = query.strip().upper()
    # Match CONSTRUCT or DESCRIBE at start (after optional PREFIX declarations)
    return bool(re.search(r"\b(CONSTRUCT|DESCRIBE)\b", query_upper))


class SPARQLClient:
    """Executes SPARQL queries against remote endpoints.

    Supports both GET and POST methods. GET is required for some endpoints
    (e.g., Virtuoso), while POST is standard for most SPARQL endpoints.
    """

    def __init__(
        self,
        endpoint_url: str,
        timeout: float,
        user_agent: str,
        username: str | None = None,
        password: str | None = None,
        digest_auth: bool = False,
        http_method: str = "POST",
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.user_agent = user_agent
        self.http_method = http_method
        self._logger = get_logger("client")
        self.auth: httpx.DigestAuth | tuple[str, str] | None = None
        if username and password:
            if digest_auth:
                self.auth = httpx.DigestAuth(username, password)
            else:
                self.auth = (username, password)

    def _http_error_message(self, e: httpx.HTTPStatusError) -> str:
        """Build diagnostic context from HTTP status, redirects, and response body."""
        msg = f"HTTP {e.response.status_code} from {self.endpoint_url}"
        if e.response.status_code == 302:
            location = e.response.headers.get("Location", "")
            if location:
                msg += f"\nRedirect to: {location[:200]}"
                msg += "\n(Endpoint redirected - may not support this query)"
        elif e.response.status_code in (400, 500):
            body = e.response.text[:500] if e.response.text else ""
            if body:
                msg += f"\nResponse: {body}"
        return msg

    def execute(self, query: str) -> Iterator[QueryResult]:
        """Execute SELECT/ASK query returning tabular results.

        Yields QueryResult objects with bindings. First result includes
        variable ordering from head.vars. Subsequent results omit variables.
        """
        self._logger.debug(
            "query.execute",
            endpoint=self.endpoint_url,
            query_bytes=len(query),
            http_method=self.http_method,
        )
        try:
            with sentry_sdk.start_span(op="http.client", name="SPARQL SELECT/ASK"):
                with httpx.Client(timeout=self.timeout, auth=self.auth) as client:
                    headers = {
                        "Accept": "application/sparql-results+json",
                        "User-Agent": self.user_agent,
                    }

                    if self.http_method == "GET":
                        response = client.get(
                            self.endpoint_url,
                            params={"query": query},
                            headers=headers,
                        )
                    else:
                        response = client.post(
                            self.endpoint_url,
                            data={"query": query},
                            headers=headers,
                        )
                    response.raise_for_status()

                    data = response.json()

                    # ASK queries return {"head": {}, "boolean": true/false}
                    # per SPARQL 1.1 Results JSON spec — no "results" key.
                    if "boolean" in data:
                        value = "true" if data["boolean"] else "false"
                        bv = BindingValue(type="literal", value=value)
                        yield QueryResult(
                            bindings={"boolean": bv},
                            variables=["boolean"],
                        )
                        return

                    variables = data.get("head", {}).get("vars", [])

                    for idx, result_row in enumerate(data["results"]["bindings"]):
                        bindings = {
                            var: BindingValue(**value_dict)
                            for var, value_dict in result_row.items()
                        }
                        # Include variable order only in first result
                        if idx == 0:
                            yield QueryResult(bindings=bindings, variables=variables)
                        else:
                            yield QueryResult(bindings=bindings)

        except httpx.TimeoutException as e:
            raise SPARQLTimeoutError(
                f"Query timed out after {self.timeout}s: {self.endpoint_url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise NetworkError(self._http_error_message(e)) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to connect to {self.endpoint_url}: {e}") from e

    def execute_update(
        self, update: str, update_endpoint: str
    ) -> UpdateResult:
        """Execute a SPARQL UPDATE operation (INSERT, DELETE, LOAD, etc.).

        Uses POST with Content-Type: application/sparql-update.
        Returns UpdateResult instead of raising on HTTP 4xx errors,
        since update failures are expected operational outcomes.
        """
        self._logger.debug(
            "update.execute",
            endpoint=update_endpoint,
            update_bytes=len(update),
        )
        try:
            with sentry_sdk.start_span(
                op="http.client", name="SPARQL UPDATE"
            ):
                with httpx.Client(
                    timeout=self.timeout, auth=self.auth
                ) as client:
                    headers = {
                        "Content-Type": "application/sparql-update",
                        "User-Agent": self.user_agent,
                    }
                    response = client.post(
                        update_endpoint,
                        content=update,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return UpdateResult(
                        success=True,
                        status_code=response.status_code,
                        message=response.text,
                    )
        except httpx.HTTPStatusError as e:
            return UpdateResult(
                success=False,
                status_code=e.response.status_code,
                message=e.response.text[:500],
            )
        except httpx.TimeoutException as e:
            raise SPARQLTimeoutError(
                f"Update timed out after {self.timeout}s: "
                f"{update_endpoint}"
            ) from e
        except httpx.RequestError as e:
            raise NetworkError(
                f"Failed to connect to {update_endpoint}: {e}"
            ) from e

    def execute_rdf(self, query: str, accept_header: str) -> str:
        """Execute CONSTRUCT/DESCRIBE query returning server-serialized RDF graph."""
        self._logger.debug(
            "query.execute_rdf",
            endpoint=self.endpoint_url,
            accept=accept_header,
            query_bytes=len(query),
            http_method=self.http_method,
        )
        try:
            with sentry_sdk.start_span(
                op="http.client", name="SPARQL CONSTRUCT/DESCRIBE"
            ):
                with httpx.Client(timeout=self.timeout, auth=self.auth) as client:
                    headers = {
                        "Accept": accept_header,
                        "User-Agent": self.user_agent,
                    }

                    if self.http_method == "GET":
                        response = client.get(
                            self.endpoint_url,
                            params={"query": query},
                            headers=headers,
                        )
                    else:
                        response = client.post(
                            self.endpoint_url,
                            data={"query": query},
                            headers=headers,
                        )
                    response.raise_for_status()
                    return response.text

        except httpx.TimeoutException as e:
            raise SPARQLTimeoutError(
                f"Query timed out after {self.timeout}s: {self.endpoint_url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise NetworkError(self._http_error_message(e)) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to connect to {self.endpoint_url}: {e}") from e

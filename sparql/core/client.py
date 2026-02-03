"""SPARQL endpoint client using httpx."""

from collections.abc import Iterator

import httpx

from sparql.core.exceptions import NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.models import BindingValue, QueryResult


class SPARQLClient:
    """HTTP client for SPARQL endpoints.

    Uses httpx for HTTP requests and parses SPARQL 1.1 JSON results format.
    Converts httpx exceptions to domain-specific exceptions.
    """

    def __init__(
        self,
        endpoint_url: str,
        timeout: float,
        user_agent: str,
        username: str | None = None,
        password: str | None = None,
        digest_auth: bool = False,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.user_agent = user_agent
        self.auth: httpx.DigestAuth | tuple[str, str] | None = None
        if username and password:
            if digest_auth:
                self.auth = httpx.DigestAuth(username, password)
            else:
                self.auth = (username, password)

    def execute(self, query: str) -> Iterator[QueryResult]:
        """Raises NetworkError on HTTP/connection errors, TimeoutError on timeout."""
        try:
            with httpx.Client(timeout=self.timeout, auth=self.auth) as client:
                response = client.post(
                    self.endpoint_url,
                    data={"query": query},
                    headers={
                        "Accept": "application/sparql-results+json",
                        "User-Agent": self.user_agent,
                    },
                )
                response.raise_for_status()

                data = response.json()

                # Get variable order from head.vars (SPARQL 1.1 JSON format)
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
            msg = f"HTTP {e.response.status_code} from {self.endpoint_url}"
            # Add diagnostic details for common error codes
            if e.response.status_code == 302:
                location = e.response.headers.get("Location", "")
                if location:
                    msg += f"\nRedirect to: {location[:200]}"
                    msg += "\n(Endpoint redirected - may not support this query)"
            elif e.response.status_code == 400:
                body = e.response.text[:500] if e.response.text else ""
                if body:
                    msg += f"\nResponse: {body}"
            elif e.response.status_code == 500:
                body = e.response.text[:500] if e.response.text else ""
                if body:
                    msg += f"\nResponse: {body}"
            raise NetworkError(msg) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to connect to {self.endpoint_url}: {e}") from e

"""Pydantic models for SPARQL query results.

Models follow SPARQL 1.1 Query Results JSON Format specification.
See: https://www.w3.org/TR/sparql11-results-json/
"""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

BindingType = Literal["uri", "literal", "bnode", "typed-literal"]


class BindingValue(BaseModel):
    """SPARQL binding value with type discrimination.

    Type determines which optional fields are populated:
    - uri: only value (the URI reference)
    - literal: value + optional xml_lang
    - typed-literal: value + datatype
    - bnode: only value (blank node identifier)
    """

    type: BindingType
    value: str
    datatype: str | None = None
    xml_lang: str | None = Field(default=None, alias="xml:lang")

    model_config = {"populate_by_name": True}


class QueryResult(BaseModel):
    """Single row of SPARQL query results.

    Contains bindings mapping variable names to their values.
    The variables field preserves SELECT order from the first result.
    """

    bindings: dict[str, BindingValue]
    # Variable order from head.vars (only set on first result)
    variables: list[str] | None = None


class EndpointConfig(BaseModel):
    """Configuration for a SPARQL endpoint connection."""

    url: HttpUrl
    timeout: float = Field(default=30.0, gt=0)
    user_agent: str = "sparql-cli/1.0"

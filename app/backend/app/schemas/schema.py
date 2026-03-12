from pydantic import BaseModel


class SchemaScoreRequest(BaseModel):
    image_id: int


class SchemaMatchOut(BaseModel):
    schema: str
    score: float
    missing: list[str]
    conflicts: list[str]


class SchemaScoreResponse(BaseModel):
    top_matches: list[SchemaMatchOut]


class SchemaAssign(BaseModel):
    schema_name: str

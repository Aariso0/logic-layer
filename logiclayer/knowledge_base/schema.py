from pydantic import BaseModel, Field
from typing import Optional

class Source(BaseModel):
    source_id: str = Field(..., description="Unique identifier for the source")
    name: str = Field(..., description="The title of the source document or website")
    url: Optional[str] = Field(None, description="The web link to the source, if applicable")
    domain: Optional[str] = Field(None, description="The domain name")
    category: Optional[str] = Field(None, description="The category designation")
    retrieved_at: Optional[str] = Field(None, description="When the data was fetched")

class Fact(BaseModel):
    # Updated keys to match your fact files exactly!
    fact_id: str = Field(..., description="Unique identifier for the fact")
    claim: str = Field(..., description="The claim statement text")
    value: str = Field(..., description="The factual description or detail value")
    source_id: str = Field(..., description="The ID of the Source this fact belongs to.")
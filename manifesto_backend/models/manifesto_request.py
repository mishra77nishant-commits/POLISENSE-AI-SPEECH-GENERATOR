from pydantic import BaseModel, Field
from typing import List, Optional


class ManifestoRequest(BaseModel):
    leader_name: str = Field(..., min_length=2)
    party_name: str = Field(..., min_length=2)

    party_tagline: Optional[str] = None

    election_type: str
    state: str
    constituency: Optional[str] = None

    language: str = "English"
    page_count: int = Field(default=3, ge=2, le=3)

    vision: str
    key_issues: List[str] = Field(..., min_length=1)

    education: Optional[str] = None
    healthcare: Optional[str] = None
    employment: Optional[str] = None
    infrastructure: Optional[str] = None
    women_empowerment: Optional[str] = None
    agriculture: Optional[str] = None
    environment: Optional[str] = None

    primary_color: str = "#174A35"
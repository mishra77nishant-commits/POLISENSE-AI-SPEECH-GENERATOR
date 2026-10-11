from pydantic import BaseModel, Field


class SpeechRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Topic of the speech"
    )

    language: str = Field(
        default="English",
        description="Language of the speech"
    )

    audience: str = Field(
        default="General Public",
        description="Target audience"
    )

    tone: str = Field(
        default="Formal",
        description="Tone of the speech"
    )

    duration_minutes: int = Field(
        default=3,
        ge=1,
        le=15,
        description="Desired speech duration in minutes"
    )

    key_points: list[str] = Field(
        default_factory=list,
        description="Important points to include"
    )


class SpeechResponse(BaseModel):
    title: str
    language: str
    speech: str
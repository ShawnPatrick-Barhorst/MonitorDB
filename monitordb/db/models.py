from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    user_id: int = 1
    is_active: int = Field(default=1, ge=0, le=1)
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: int | None = None
    height_cm: int | None = None
    weight_lb: int | None = None
    prescriptions: str | None = None
    profession: str | None = None
    relationship_status: str | None = None
    sexual_orientation: str | None = None
    nationality: str | None = None
    address: str | None = None


class UserConfig(BaseModel):
    user_id: int = 1
    is_active: int = 1
    profile: UserProfile
    integrations: dict = Field(default_factory=dict)

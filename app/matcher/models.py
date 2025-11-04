from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class JobIn(BaseModel):
    title: str
    location: Optional[str] = None
    min_exp: Optional[int] = Field(default=None, ge=0)
    description: str

class ResumeIn(BaseModel):
    name: str
    email: EmailStr
    location: str
    years_experience: int = Field(ge=0)
    skills: str
    summary: str

class MatchRequest(BaseModel):
    description: str
    top_k: int = 10
    location: Optional[str] = None
    min_exp: Optional[int] = None

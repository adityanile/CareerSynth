from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    techStack: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    description: str
    tags: list[str] = Field(default_factory=list)


class ProjectPatch(BaseModel):
    name: Optional[str] = None
    techStack: Optional[list[str]] = None
    urls: Optional[list[str]] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class ExperienceCreate(BaseModel):
    companyName: str
    startDate: str
    endDate: Optional[str] = None
    position: str
    description: str
    location: str


class ExperiencePatch(BaseModel):
    companyName: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class AchievementCreate(BaseModel):
    name: str
    link: str
    organisation: str
    date: str


class AchievementPatch(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None
    organisation: Optional[str] = None
    date: Optional[str] = None

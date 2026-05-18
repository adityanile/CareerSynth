from typing import Optional

from pydantic import BaseModel, Field


class ProjectState(BaseModel):
    id: int
    name: str
    techStack: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    description: str
    tags: list[str] = Field(default_factory=list)
    createdAt: str
    updatedAt: str


class ExperienceState(BaseModel):
    id: int
    companyName: str
    startDate: str
    endDate: Optional[str] = None
    position: str
    description: str
    location: str
    createdAt: str
    updatedAt: str


class AchievementState(BaseModel):
    id: int
    name: str
    link: str
    organisation: str
    date: str
    createdAt: str
    updatedAt: str


class EducationState(BaseModel):
    id: int
    degreeName: str
    location: str
    startYear: str
    endYear: Optional[str] = None
    cgpaOrPercentage: str
    createdAt: str
    updatedAt: str


class ResumeRecordState(BaseModel):
    id: int
    resumeName: str
    resumeDescription: str
    resume: str
    createdOn: str
    updatedAt: str


class ProfileState(BaseModel):
    name: str = ""
    role: str = ""
    contact: str = ""
    location: str = ""
    linkedinUrl: str = ""
    additionalUrls: list[str] = Field(default_factory=list)


class ResumeState(BaseModel):
    projects: list[ProjectState] = Field(default_factory=list)
    experiences: list[ExperienceState] = Field(default_factory=list)
    achievements: list[AchievementState] = Field(default_factory=list)
    educations: list[EducationState] = Field(default_factory=list)
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    profile: ProfileState = Field(default_factory=ProfileState)


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


class EducationCreate(BaseModel):
    degreeName: str
    location: str
    startYear: str
    endYear: Optional[str] = None
    cgpaOrPercentage: str


class EducationPatch(BaseModel):
    degreeName: Optional[str] = None
    location: Optional[str] = None
    startYear: Optional[str] = None
    endYear: Optional[str] = None
    cgpaOrPercentage: Optional[str] = None


class ResumeCreate(BaseModel):
    resumeName: str
    resumeDescription: str
    resume: str


class ResumePatch(BaseModel):
    resumeName: Optional[str] = None
    resumeDescription: Optional[str] = None
    resume: Optional[str] = None


class ResumeParseTextRequest(BaseModel):
    text: str


class ParsedProject(BaseModel):
    projectName: str
    description: str
    techStack: list[str] = Field(default_factory=list)


class ParsedExperience(BaseModel):
    companyName: str
    position: str
    description: str
    startDate: str
    endDate: Optional[str] = None
    pursuing: bool = False
    location: str


class ParsedAchievement(BaseModel):
    name: str
    organisation: str
    date: str
    link: str


class ParsedEducation(BaseModel):
    degreeName: str
    location: str
    startYear: str
    endYear: Optional[str] = None
    pursuing: bool = False
    cgpaOrPercentage: str


class ParsedResumeOutput(BaseModel):
    projects: list[ParsedProject] = Field(default_factory=list)
    experiences: list[ParsedExperience] = Field(default_factory=list)
    achievements: list[ParsedAchievement] = Field(default_factory=list)
    educations: list[ParsedEducation] = Field(default_factory=list)

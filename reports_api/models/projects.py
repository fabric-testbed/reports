from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class ProjectUsers(BaseModel):
    total: Optional[int] = None
    data: Optional[list] = None


class Project(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    active: Optional[bool] = None
    created_date: Optional[str] = None
    expires_on: Optional[str] = None
    retired_date: Optional[str] = None
    last_updated: Optional[str] = None
    users: Optional[ProjectUsers] = None


class Projects(PaginatedResponse[Project]):
    type: Optional[str] = "projects"


class ProjectMember(BaseModel):
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    active: Optional[bool] = None
    user_name: Optional[str] = None
    affiliation: Optional[str] = None
    registered_on: Optional[str] = None
    last_updated: Optional[str] = None
    google_scholar: Optional[str] = None
    scopus: Optional[str] = None
    bastion_login: Optional[str] = None
    membership_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ProjectMembership(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    active: Optional[bool] = None
    created_date: Optional[str] = None
    expires_on: Optional[str] = None
    retired_date: Optional[str] = None
    last_updated: Optional[str] = None
    members: Optional[list[ProjectMember]] = None


class ProjectMemberships(PaginatedResponse[ProjectMembership]):
    type: Optional[str] = "projectMemberships"

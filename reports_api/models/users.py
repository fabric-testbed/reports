from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class UserSlices(BaseModel):
    total: Optional[int] = None
    data: Optional[list] = None


class User(BaseModel):
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
    slices: Optional[UserSlices] = None


class Users(PaginatedResponse[User]):
    type: Optional[str] = "users"


class UserMembershipProject(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    active: Optional[bool] = None
    created_date: Optional[str] = None
    expires_on: Optional[str] = None
    retired_date: Optional[str] = None
    last_updated: Optional[str] = None
    membership_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class UserMembership(BaseModel):
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    active: Optional[bool] = None
    user_name: Optional[str] = None
    affiliation: Optional[str] = None
    registered_on: Optional[str] = None
    last_updated: Optional[str] = None
    google_scholar: Optional[str] = None
    scopus: Optional[str] = None
    projects: Optional[list[UserMembershipProject]] = None


class UserMemberships(PaginatedResponse[UserMembership]):
    type: Optional[str] = "userMemberships"

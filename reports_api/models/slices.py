from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class SliceSlivers(BaseModel):
    total: Optional[int] = None
    data: Optional[list] = None


class Slice(BaseModel):
    slice_id: Optional[str] = None
    slice_name: Optional[str] = None
    state: Optional[str] = None
    lease_start: Optional[str] = None
    lease_end: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    slivers: Optional[SliceSlivers] = None


class Slices(PaginatedResponse[Slice]):
    type: Optional[str] = "slices"

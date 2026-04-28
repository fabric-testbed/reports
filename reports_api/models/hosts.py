from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class Host(BaseModel):
    name: Optional[str] = None


class HostSite(BaseModel):
    name: Optional[str] = None
    hosts: Optional[list[Host]] = None


class Hosts(PaginatedResponse[HostSite]):
    type: Optional[str] = "hosts"

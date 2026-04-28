from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class Site(BaseModel):
    name: Optional[str] = None
    hosts: Optional[list] = None


class Sites(PaginatedResponse[Site]):
    type: Optional[str] = "sites"

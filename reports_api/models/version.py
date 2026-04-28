from typing import Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class VersionData(BaseModel):
    reference: Optional[str] = None
    version: Optional[str] = None


class Version(PaginatedResponse[VersionData]):
    type: Optional[str] = "version"

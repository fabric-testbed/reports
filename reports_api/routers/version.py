from fastapi import APIRouter

from reports_api import __version__, __API_REFERENCE__
from reports_api.models.version import Version, VersionData

router = APIRouter(prefix="/reports", tags=["version"])


@router.get("/version", response_model=Version, response_model_exclude_none=True)
async def version_get():
    version = VersionData(reference=__API_REFERENCE__, version=__version__)
    return Version(data=[version], size=1, status=200, type="version")

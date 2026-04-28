from typing import Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.common import NoContentData, NoContentResponse
from reports_api.models.hosts import HostSite, Hosts
from reports_api.security.dependencies import get_current_auth, require_bearer_token_only
from reports_api.security.fabric_token import FabricToken

router = APIRouter(prefix="/reports", tags=["hosts"])


@router.get("/hosts", response_model=Hosts, response_model_exclude_none=True)
async def hosts_get(
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
    site: Optional[list[str]] = Query(None),
    exclude_site: Optional[list[str]] = Query(None),
):
    db_mgr = get_db_manager()
    result = await db_mgr.get_hosts(session=session, site=site, exclude_site=exclude_site)
    data = [HostSite(**h) for h in result]
    return Hosts(data=data, size=len(data), type="hosts")


@router.post("/hosts/{host_name}/capacity", response_model=NoContentResponse, response_model_exclude_none=True)
async def hosts_host_name_capacity_post(
    host_name: str,
    body: dict,
    session: AsyncSession = Depends(get_session),
    auth: dict = Depends(require_bearer_token_only),
):
    db_mgr = get_db_manager()
    await db_mgr.add_or_update_host_capacity(
        session=session,
        host_name=host_name,
        site_name=body.get("site"),
        cores=body.get("cores_capacity", 0),
        ram=body.get("ram_capacity", 0),
        disk=body.get("disk_capacity", 0),
        components=body.get("components"),
    )
    return NoContentResponse(
        data=[NoContentData(message="Host capacity updated successfully")],
    )

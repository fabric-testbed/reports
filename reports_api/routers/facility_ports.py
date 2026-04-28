from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.common import NoContentData, NoContentResponse
from reports_api.security.dependencies import require_bearer_token_only

router = APIRouter(prefix="/reports", tags=["facility_ports"])


@router.post("/facility-ports/capacity", response_model=NoContentResponse, response_model_exclude_none=True)
async def facility_ports_capacity_post(
    body: dict,
    session: AsyncSession = Depends(get_session),
    auth: dict = Depends(require_bearer_token_only),
):
    db_mgr = get_db_manager()
    await db_mgr.add_or_update_facility_port_capacity(
        session=session,
        port_name=body.get("name"),
        site_name=body.get("site"),
        device_name=body.get("device_name"),
        local_name=body.get("local_name"),
        vlan_range=body.get("vlan_range"),
        total_vlans=body.get("total_vlans", 0),
    )
    return NoContentResponse(
        data=[NoContentData(message="Facility port capacity updated successfully")],
    )

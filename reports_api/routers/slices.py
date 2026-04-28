from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.common import NoContentData, NoContentResponse
from reports_api.models.slices import Slice as SliceModel
from reports_api.models.slices import Slices
from reports_api.response_code.slice_sliver_states import SliceState, SliverStates
from reports_api.security.dependencies import get_current_auth, require_bearer_token_only
from reports_api.security.fabric_token import FabricToken

router = APIRouter(prefix="/reports", tags=["slices"])


@router.get("/slices", response_model=Slices, response_model_exclude_none=True)
async def slices_get(
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    user_id: Optional[list[str]] = Query(None),
    user_email: Optional[list[str]] = Query(None),
    project_id: Optional[list[str]] = Query(None),
    slice_id: Optional[list[str]] = Query(None),
    slice_state: Optional[list[str]] = Query(None),
    sliver_id: Optional[list[str]] = Query(None),
    sliver_type: Optional[list[str]] = Query(None),
    sliver_state: Optional[list[str]] = Query(None),
    component_type: Optional[list[str]] = Query(None),
    component_model: Optional[list[str]] = Query(None),
    bdf: Optional[list[str]] = Query(None),
    vlan: Optional[list[str]] = Query(None),
    ip_subnet: Optional[list[str]] = Query(None),
    ip_v4: Optional[list[str]] = Query(None),
    ip_v6: Optional[list[str]] = Query(None),
    site: Optional[list[str]] = Query(None),
    host: Optional[list[str]] = Query(None),
    facility: Optional[list[str]] = Query(None),
    exclude_user_id: Optional[list[str]] = Query(None),
    exclude_user_email: Optional[list[str]] = Query(None),
    exclude_project_id: Optional[list[str]] = Query(None),
    exclude_site: Optional[list[str]] = Query(None),
    exclude_host: Optional[list[str]] = Query(None),
    exclude_slice_state: Optional[list[str]] = Query(None),
    exclude_sliver_state: Optional[list[str]] = Query(None),
    page: Optional[int] = Query(None),
    per_page: Optional[int] = Query(None),
):
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    sliver_states = [SliverStates.translate(s) for s in sliver_state] if sliver_state else None
    slice_states = [SliceState.translate(s) for s in slice_state] if slice_state else None
    exclude_sliver_states = [SliverStates.translate(s) for s in exclude_sliver_state] if exclude_sliver_state else None
    exclude_slice_states = [SliceState.translate(s) for s in exclude_slice_state] if exclude_slice_state else None

    db_mgr = get_db_manager()
    result = await db_mgr.get_slices(
        session=session, start_time=start, end_time=end, user_email=user_email,
        user_id=user_id, vlan=vlan, sliver_id=sliver_id, sliver_type=sliver_type,
        slice_id=slice_id, bdf=bdf, sliver_state=sliver_states, site=site,
        ip_v4=ip_v4, ip_v6=ip_v6, host=host, project_id=project_id,
        component_model=component_model, slice_state=slice_states, facility=facility,
        component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        exclude_project_id=exclude_project_id, exclude_site=exclude_site,
        exclude_host=exclude_host, exclude_sliver_state=exclude_sliver_states,
        exclude_slice_state=exclude_slice_states,
    )
    data = [SliceModel(**s) for s in result["slices"]]
    return Slices(data=data, size=len(data), type="slices", total=result.get("total"))


@router.post("/slices/{slice_id}", response_model=NoContentResponse, response_model_exclude_none=True)
async def slices_slice_id_post(
    slice_id: str,
    body: SliceModel,
    session: AsyncSession = Depends(get_session),
    auth: dict = Depends(require_bearer_token_only),
):
    db_mgr = get_db_manager()

    p_id = await db_mgr.add_or_update_project(
        session=session, project_uuid=body.project_id, project_name=body.project_name,
    )
    u_id = await db_mgr.add_or_update_user(
        session=session, user_uuid=body.user_id, user_email=body.user_email,
    )
    await db_mgr.add_or_update_slice(
        session=session, project_id=p_id, user_id=u_id, slice_guid=body.slice_id,
        slice_name=body.slice_name, state=SliceState.translate(body.state),
        lease_start=body.lease_start, lease_end=body.lease_end,
    )

    return NoContentResponse(
        data=[NoContentData(details=f"Slice '{slice_id}' has been successfully created/updated")],
    )

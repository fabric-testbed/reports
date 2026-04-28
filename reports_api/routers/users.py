from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.users import User, UserMembership, UserMemberships, Users
from reports_api.response_code.slice_sliver_states import SliceState, SliverStates
from reports_api.security.dependencies import get_current_auth, require_bearer_token_only
from reports_api.security.fabric_token import FabricToken

router = APIRouter(prefix="/reports", tags=["users"])


@router.get("/users", response_model=Users, response_model_exclude_none=True)
async def users_get(
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
    exclude_user_id: Optional[list[str]] = Query(None),
    exclude_user_email: Optional[list[str]] = Query(None),
    exclude_project_id: Optional[list[str]] = Query(None),
    exclude_site: Optional[list[str]] = Query(None),
    exclude_host: Optional[list[str]] = Query(None),
    exclude_slice_state: Optional[list[str]] = Query(None),
    exclude_sliver_state: Optional[list[str]] = Query(None),
    facility: Optional[list[str]] = Query(None),
    project_type: Optional[list[str]] = Query(None),
    exclude_project_type: Optional[list[str]] = Query(None),
    user_active: Optional[bool] = Query(None),
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
    result = await db_mgr.get_users(
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
        project_type=project_type, exclude_project_type=exclude_project_type,
        user_active=user_active,
    )
    data = [User(**u) for u in result["users"]]
    return Users(data=data, size=len(data), type="users", total=result.get("total"))


@router.get("/users/memberships", response_model=UserMemberships, response_model_exclude_none=True)
async def users_memberships_get(
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    user_id: Optional[list[str]] = Query(None),
    user_email: Optional[list[str]] = Query(None),
    exclude_user_id: Optional[list[str]] = Query(None),
    exclude_user_email: Optional[list[str]] = Query(None),
    project_type: Optional[list[str]] = Query(None),
    exclude_project_type: Optional[list[str]] = Query(None),
    project_active: Optional[bool] = Query(None),
    project_expired: Optional[bool] = Query(None),
    project_retired: Optional[bool] = Query(None),
    user_active: Optional[bool] = Query(None),
    page: Optional[int] = Query(None),
    per_page: Optional[int] = Query(None),
):
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    db_mgr = get_db_manager()
    result = await db_mgr.get_user_memberships(
        session=session, start_time=start, end_time=end, user_email=user_email,
        user_id=user_id, exclude_user_id=exclude_user_id,
        exclude_user_email=exclude_user_email,
        project_type=project_type, exclude_project_type=exclude_project_type,
        project_active=project_active, project_expired=project_expired,
        project_retired=project_retired, user_active=user_active,
        page=page, per_page=per_page,
    )
    data = [UserMembership(**u) for u in result["users"]]
    return UserMemberships(data=data, size=len(data), type="userMemberships", total=result.get("total"))


@router.get("/users/{uuid}", response_model=Users, response_model_exclude_none=True)
async def users_uuid_get(
    uuid: str,
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
):
    db_mgr = get_db_manager()
    result = await db_mgr.get_users(session=session, user_id=[uuid])
    data = [User(**u) for u in result["users"]]
    return Users(data=data, size=len(data), type="users", total=result.get("total"))


@router.post("/users/{user_uuid}", response_model_exclude_none=True)
async def users_post(
    user_uuid: str,
    session: AsyncSession = Depends(get_session),
    auth: dict = Depends(require_bearer_token_only),
    user_email: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    name: Optional[str] = Query(None),
    affiliation: Optional[str] = Query(None),
    registered_on: Optional[str] = Query(None),
    last_updated: Optional[str] = Query(None),
    google_scholar: Optional[str] = Query(None),
    scopus: Optional[str] = Query(None),
):
    reg_time = datetime.fromisoformat(registered_on) if registered_on else None
    update_time = datetime.fromisoformat(last_updated) if last_updated else None

    db_mgr = get_db_manager()
    user_id = await db_mgr.add_or_update_user(
        session=session, user_uuid=user_uuid, user_email=user_email,
        active=active, name=name, affiliation=affiliation,
        registered_on=reg_time, last_updated=update_time,
        google_scholar=google_scholar, scopus=scopus,
    )
    return user_id

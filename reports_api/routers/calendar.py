from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.calendar import FindSlotRequest
from reports_api.security.dependencies import get_current_auth
from reports_api.security.fabric_token import FabricToken

router = APIRouter(prefix="/reports", tags=["calendar"])


@router.get("/calendar")
async def calendar_get(
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    interval: Optional[str] = Query(None),
    site: Optional[list[str]] = Query(None),
    host: Optional[list[str]] = Query(None),
    exclude_site: Optional[list[str]] = Query(None),
    exclude_host: Optional[list[str]] = Query(None),
):
    if not start_time or not end_time:
        raise HTTPException(status_code=400, detail="start_time and end_time are required")

    start_time = start_time.replace(" ", "+")
    end_time = end_time.replace(" ", "+")

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    if start >= end:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    if interval and interval not in ("hour", "day", "week"):
        raise HTTPException(status_code=400, detail="interval must be 'hour', 'day', or 'week'")

    db_mgr = get_db_manager()
    result = await db_mgr.get_calendar(
        session=session, start_time=start, end_time=end,
        interval=interval or "day", site=site, host=host,
        exclude_site=exclude_site, exclude_host=exclude_host,
    )
    return JSONResponse(content=result)


@router.post("/calendar/find-slot")
async def calendar_find_slot(
    body: FindSlotRequest,
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
):
    start = datetime.fromisoformat(body.start)
    end = datetime.fromisoformat(body.end)

    if start >= end:
        raise HTTPException(status_code=400, detail="'start' must be before 'end'")

    range_hours = (end - start).total_seconds() / 3600
    if range_hours > 30 * 24:
        raise HTTPException(status_code=400, detail="Search range must not exceed 30 days")
    if body.duration > range_hours:
        raise HTTPException(status_code=400, detail="'duration' exceeds the search range")
    if body.max_results < 1 or body.max_results > 50:
        raise HTTPException(status_code=400, detail="'max_results' must be an integer between 1 and 50")

    valid_types = {"compute", "link", "facility_port"}
    for i, r in enumerate(body.resources):
        if r.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"resources[{i}].type must be one of: {', '.join(valid_types)}")
        if r.type == "link":
            if not r.site_a or not r.site_b or r.bandwidth is None:
                raise HTTPException(status_code=400, detail=f"resources[{i}] (link): 'site_a', 'site_b', and 'bandwidth' are required")
        elif r.type == "facility_port":
            if not r.name or not r.site or r.vlans is None:
                raise HTTPException(status_code=400, detail=f"resources[{i}] (facility_port): 'name', 'site', and 'vlans' are required")

    resources_dicts = [r.model_dump(exclude_none=True) for r in body.resources]

    db_mgr = get_db_manager()
    result = await db_mgr.find_slot(
        session=session, start_time=start, end_time=end,
        duration=body.duration, resources=resources_dicts,
        max_results=body.max_results,
    )
    return JSONResponse(content=result)

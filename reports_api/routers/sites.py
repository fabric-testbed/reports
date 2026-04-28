from typing import Union

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.sites import Site, Sites
from reports_api.security.dependencies import get_current_auth
from reports_api.security.fabric_token import FabricToken

router = APIRouter(prefix="/reports", tags=["sites"])


@router.get("/sites", response_model=Sites, response_model_exclude_none=True)
async def sites_get(
    session: AsyncSession = Depends(get_session),
    auth: Union[FabricToken, dict] = Depends(get_current_auth),
):
    db_mgr = get_db_manager()
    result = await db_mgr.get_sites(session=session)
    data = [Site(**s) for s in result]
    return Sites(data=data, size=len(data), type="sites")

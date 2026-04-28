from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database.db_manager import get_db_manager
from reports_api.database.session import get_session
from reports_api.models.common import NoContentData, NoContentResponse
from reports_api.security.dependencies import require_bearer_token_only

router = APIRouter(prefix="/reports", tags=["links"])


@router.post("/links/capacity", response_model=NoContentResponse, response_model_exclude_none=True)
async def links_capacity_post(
    body: dict,
    session: AsyncSession = Depends(get_session),
    auth: dict = Depends(require_bearer_token_only),
):
    db_mgr = get_db_manager()
    await db_mgr.add_or_update_link_capacity(
        session=session,
        link_name=body.get("name"),
        site_a_name=body.get("site_a"),
        site_b_name=body.get("site_b"),
        layer=body.get("layer"),
        bandwidth=body.get("bandwidth_capacity", 0),
    )
    return NoContentResponse(
        data=[NoContentData(message="Link capacity updated successfully")],
    )

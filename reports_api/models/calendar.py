from typing import Optional

from pydantic import BaseModel


class FindSlotResource(BaseModel):
    type: str
    site: Optional[str] = None
    cores: Optional[int] = None
    ram: Optional[int] = None
    disk: Optional[int] = None
    components: Optional[dict] = None
    site_a: Optional[str] = None
    site_b: Optional[str] = None
    bandwidth: Optional[int] = None
    name: Optional[str] = None
    vlans: Optional[int] = None


class FindSlotRequest(BaseModel):
    start: str
    end: str
    duration: int
    resources: list[FindSlotResource]
    max_results: int = 1

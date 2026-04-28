from typing import Any, Optional

from pydantic import BaseModel

from reports_api.models.common import PaginatedResponse


class Component(BaseModel):
    component_guid: Optional[str] = None
    component_id: Optional[str] = None
    node_id: Optional[str] = None
    component_node_id: Optional[str] = None
    type: Optional[str] = None
    model: Optional[str] = None
    bdfs: Optional[list[str]] = None


class Interface(BaseModel):
    interface_guid: Optional[str] = None
    interface_id: Optional[str] = None
    bdf: Optional[str] = None
    vlan: Optional[str] = None
    local_name: Optional[str] = None
    device_name: Optional[str] = None
    name: Optional[str] = None


class SliverComponents(BaseModel):
    total: Optional[int] = None
    data: Optional[list[Component]] = None


class SliverInterfaces(BaseModel):
    total: Optional[int] = None
    data: Optional[list[Interface]] = None


class Sliver(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    slice_id: Optional[str] = None
    slice_name: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    host: Optional[str] = None
    site: Optional[str] = None
    sliver_id: Optional[str] = None
    node_id: Optional[str] = None
    state: Optional[str] = None
    sliver_type: Optional[str] = None
    ip_subnet: Optional[str] = None
    ip_v4: Optional[str] = None
    ip_v6: Optional[str] = None
    error: Optional[str] = None
    image: Optional[str] = None
    core: Optional[int] = None
    ram: Optional[int] = None
    disk: Optional[int] = None
    bandwidth: Optional[int] = None
    lease_start: Optional[str] = None
    lease_end: Optional[str] = None
    closed_at: Optional[str] = None
    components: Optional[SliverComponents] = None
    interfaces: Optional[SliverInterfaces] = None


class Slivers(PaginatedResponse[Sliver]):
    type: Optional[str] = "slivers"

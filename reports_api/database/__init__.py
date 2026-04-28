from datetime import datetime
from typing import Optional, Any

from sqlalchemy import DateTime, ForeignKey, Index, JSON, UniqueConstraint, func, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Sites(Base):
    __tablename__ = 'sites'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)


class Hosts(Base):
    __tablename__ = 'hosts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    site_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sites.id'), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    __table_args__ = (
        Index('idx_hosts_name_site', 'name', 'site_id'),
    )


class Projects(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    project_uuid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    project_name: Mapped[Optional[str]] = mapped_column(String, index=True)
    project_type: Mapped[Optional[str]] = mapped_column(String, index=True)
    active: Mapped[Optional[bool]] = mapped_column()
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    expires_on: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    retired_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index('idx_projects_uuid_name', 'project_uuid', 'project_name'),
    )


class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    user_uuid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    active: Mapped[Optional[bool]] = mapped_column()
    name: Mapped[Optional[str]] = mapped_column(String, index=True)
    affiliation: Mapped[Optional[str]] = mapped_column(String, index=True)
    registered_on: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    google_scholar: Mapped[Optional[str]] = mapped_column(String)
    scopus: Mapped[Optional[str]] = mapped_column(String)
    bastion_login: Mapped[Optional[str]] = mapped_column(String)

    __table_args__ = (
        Index('idx_users_uuid_email', 'user_uuid', 'user_email'),
    )


class Membership(Base):
    __tablename__ = 'membership'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    membership_type: Mapped[Optional[str]] = mapped_column(String)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', 'membership_type', 'start_time'),
    )


class Slices(Base):
    __tablename__ = 'slices'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), index=True)
    slice_guid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slice_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    state: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lease_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    lease_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('idx_slice_lease_range', 'lease_start', 'lease_end'),
        Index('idx_slices_user_project', 'user_id', 'project_id'),
        Index('idx_slices_state_project', 'state', 'project_id'),
    )


class Slivers(Base):
    __tablename__ = 'slivers'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), index=True)
    slice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('slices.id'), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), index=True)
    host_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('hosts.id'), index=True)
    site_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sites.id'), index=True)
    sliver_guid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    node_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    state: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sliver_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ip_subnet: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    ip_v4: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    ip_v6: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    core: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ram: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disk: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bandwidth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lease_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    lease_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('idx_sliver_lease_range', 'lease_start', 'lease_end'),
        Index('idx_slivers_user_project', 'user_id', 'project_id'),
        Index('idx_slivers_site_host', 'site_id', 'host_id'),
        Index('idx_slivers_project_slice', 'project_id', 'slice_id'),
        Index('idx_slivers_state_type', 'state', 'sliver_type'),
        Index('idx_slivers_ip_subnet', 'ip_subnet'),
        Index('idx_slivers_ip_v4', 'ip_v4'),
        Index('idx_slivers_ip_v6', 'ip_v6'),
    )


class Components(Base):
    __tablename__ = 'components'
    sliver_id: Mapped[int] = mapped_column(Integer, ForeignKey('slivers.id'), primary_key=True)
    component_guid: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    node_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    component_node_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    bdfs: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index('idx_components_type_model', 'type', 'model'),
        Index('idx_components_sliver', 'sliver_id'),
    )


class HostCapacities(Base):
    __tablename__ = 'host_capacities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey('hosts.id'), nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id'), nullable=False)
    cores_capacity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    ram_capacity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    disk_capacity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    components: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_host_capacities_host_id', 'host_id', unique=True),
        Index('ix_host_capacities_site_id', 'site_id'),
    )


class LinkCapacities(Base):
    __tablename__ = 'link_capacities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    site_a_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id'), nullable=False)
    site_b_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id'), nullable=False)
    layer: Mapped[str] = mapped_column(String, nullable=False)
    bandwidth_capacity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_link_capacities_name', 'name', unique=True),
        Index('ix_link_capacities_sites', 'site_a_id', 'site_b_id'),
    )


class FacilityPortCapacities(Base):
    __tablename__ = 'facility_port_capacities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    site_id: Mapped[int] = mapped_column(Integer, ForeignKey('sites.id'), nullable=False)
    device_name: Mapped[str] = mapped_column(String, nullable=False)
    local_name: Mapped[str] = mapped_column(String, nullable=False)
    vlan_range: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_vlans: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_facility_port_capacities_name_site_device_port', 'name', 'site_id', 'device_name', 'local_name', unique=True),
        Index('ix_facility_port_capacities_name_site', 'name', 'site_id'),
    )


class Interfaces(Base):
    __tablename__ = 'interfaces'
    sliver_id: Mapped[int] = mapped_column(Integer, ForeignKey('slivers.id'), primary_key=True, index=True)
    interface_guid: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    site_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sites.id'), index=True)
    vlan: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    bdf: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    local_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    device_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    __table_args__ = (
        Index('idx_interfaces_sliver_vlan', 'sliver_id', 'vlan'),
        Index('idx_interfaces_sliver_bdf', 'sliver_id', 'bdf'),
        Index('idx_interfaces_sliver_site', 'sliver_id', 'site_id'),
    )

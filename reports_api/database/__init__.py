from sqlalchemy import ForeignKey, TIMESTAMP, Index, JSON, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Integer, Sequence

Base = declarative_base()


class Sites(Base):
    __tablename__ = 'sites'
    id = Column(Integer, Sequence('sites.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class Hosts(Base):
    __tablename__ = 'hosts'
    id = Column(Integer, Sequence('hosts.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey('sites.id'), index=True)
    name = Column(String, nullable=False, index=True)
    __table_args__ = (
        Index('idx_hosts_name_site', 'name', 'site_id'),
    )


class Projects(Base):
    __tablename__ = 'projects'
    id = Column(Integer, Sequence('projects.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    project_uuid = Column(String, nullable=False, index=True)
    project_name = Column(String, index=True)
    project_type = Column(String, index=True)
    active = Column(Boolean)
    created_date = Column(TIMESTAMP(timezone=True), index=True)
    expires_on = Column(TIMESTAMP(timezone=True), index=True)
    retired_date = Column(TIMESTAMP(timezone=True), index=True)
    last_updated = Column(TIMESTAMP(timezone=True), index=True)

    #memberships = relationship("Membership", back_populates="project", cascade="all, delete-orphan")
    __table_args__ = (
        Index('idx_projects_uuid_name', 'project_uuid', 'project_name'),
    )


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('users.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    user_uuid = Column(String, nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    active = Column(Boolean)
    name = Column(String, index=True)
    affiliation = Column(String, index=True)
    registered_on = Column(TIMESTAMP(timezone=True), index=True)
    last_updated = Column(TIMESTAMP(timezone=True), index=True)
    google_scholar = Column(String)
    scopus = Column(String)
    bastion_login = Column(String)

    #memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    __table_args__ = (
        Index('idx_users_uuid_email', 'user_uuid', 'user_email'),
    )


class Membership(Base):
    __tablename__ = 'membership'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    membership_type = Column(String)
    active = Column(Boolean, default=True, nullable=False)

    #user = relationship("Users", back_populates="memberships")
    #project = relationship("Projects", back_populates="memberships")

    __table_args__ = (
        # Optional: enforce uniqueness of membership period if needed
        UniqueConstraint('user_id', 'project_id', 'membership_type', 'start_time',),
    )


class Slices(Base):
    __tablename__ = 'slices'
    id = Column(Integer, Sequence('slices.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    slice_guid = Column(String, nullable=False, index=True)
    slice_name = Column(String, nullable=True, index=True)
    state = Column(Integer, nullable=False, index=True)
    lease_start = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    lease_end = Column(TIMESTAMP(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('idx_slice_lease_range', 'lease_start', 'lease_end'),
        Index('idx_slices_user_project', 'user_id', 'project_id'),
        Index('idx_slices_state_project', 'state', 'project_id'),
    )


class Slivers(Base):
    __tablename__ = 'slivers'
    id = Column(Integer, Sequence('slivers.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), index=True)
    slice_id = Column(Integer, ForeignKey('slices.id'), index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    host_id = Column(Integer, ForeignKey('hosts.id'), index=True)
    site_id = Column(Integer, ForeignKey('sites.id'), index=True)
    sliver_guid = Column(String, nullable=False, index=True)
    node_id = Column(String, nullable=True, index=True)
    state = Column(Integer, nullable=False, index=True)
    sliver_type = Column(String, nullable=False, index=True)
    ip_subnet = Column(String, nullable=True, index=True)
    ip_v4 = Column(String, nullable=True, index=True)
    ip_v6 = Column(String, nullable=True, index=True)
    image = Column(String, nullable=True)
    core = Column(Integer, nullable=True)
    ram = Column(Integer, nullable=True)
    disk = Column(Integer, nullable=True)
    bandwidth = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    lease_start = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    lease_end = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    closed_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)

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
    sliver_id = Column(Integer, ForeignKey('slivers.id'), primary_key=True)
    component_guid = Column(String, primary_key=True, index=True)
    node_id = Column(String, nullable=True, index=True)
    component_node_id = Column(String, nullable=True, index=True)
    type = Column(String, nullable=True, index=True)
    model = Column(String, nullable=True, index=True)
    bdfs = Column(JSON, nullable=True)  # Store BDFs as a JSON list

    __table_args__ = (
        Index('idx_components_type_model', 'type', 'model'),
        Index('idx_components_sliver', 'sliver_id'),
    )


class HostCapacities(Base):
    __tablename__ = 'host_capacities'
    id = Column(Integer, Sequence('host_capacities_id_seq', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey('hosts.id'), nullable=False)
    site_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    cores_capacity = Column(Integer, default=0)
    ram_capacity = Column(Integer, default=0)
    disk_capacity = Column(Integer, default=0)
    components = Column(JSON, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_host_capacities_host_id', 'host_id', unique=True),
        Index('ix_host_capacities_site_id', 'site_id'),
    )


class LinkCapacities(Base):
    __tablename__ = 'link_capacities'
    id = Column(Integer, Sequence('link_capacities_id_seq', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    name = Column(String, nullable=False)
    site_a_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    site_b_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    layer = Column(String, nullable=False)
    bandwidth_capacity = Column(Integer, default=0)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_link_capacities_name', 'name', unique=True),
        Index('ix_link_capacities_sites', 'site_a_id', 'site_b_id'),
    )


class FacilityPortCapacities(Base):
    __tablename__ = 'facility_port_capacities'
    id = Column(Integer, Sequence('facility_port_capacities_id_seq', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    name = Column(String, nullable=False)
    site_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    device_name = Column(String, nullable=False)
    local_name = Column(String, nullable=False)
    vlan_range = Column(String, nullable=True)
    total_vlans = Column(Integer, default=0)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_facility_port_capacities_name_site_device_port', 'name', 'site_id', 'device_name', 'local_name', unique=True),
        Index('ix_facility_port_capacities_name_site', 'name', 'site_id'),
    )


class Interfaces(Base):
    __tablename__ = 'interfaces'
    sliver_id = Column(Integer, ForeignKey('slivers.id'), primary_key=True, index=True)
    interface_guid = Column(String, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey('sites.id'), index=True)
    vlan = Column(String, nullable=True, index=True)
    bdf = Column(String, nullable=True, index=True)
    local_name = Column(String, nullable=True, index=True)
    device_name = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True, index=True)

    __table_args__ = (
        Index('idx_interfaces_sliver_vlan', 'sliver_id', 'vlan'),
        Index('idx_interfaces_sliver_bdf', 'sliver_id', 'bdf'),
        Index('idx_interfaces_sliver_site', 'sliver_id', 'site_id'),
    )

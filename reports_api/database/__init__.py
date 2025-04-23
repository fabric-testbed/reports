from sqlalchemy import ForeignKey, TIMESTAMP, Index, JSON
from sqlalchemy.orm import declarative_base
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
    project_name = Column(String, nullable=True, index=True)
    __table_args__ = (
        Index('idx_projects_uuid_name', 'project_uuid', 'project_name'),
    )


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('users.id', start=1, increment=1), autoincrement=True, primary_key=True, index=True)
    user_uuid = Column(String, nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    __table_args__ = (
        Index('idx_users_uuid_email', 'user_uuid', 'user_email'),
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
    image = Column(String, nullable=True)
    core = Column(Integer, nullable=True)
    ram = Column(Integer, nullable=True)
    disk = Column(Integer, nullable=True)
    bandwidth = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    lease_start = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    lease_end = Column(TIMESTAMP(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index('idx_sliver_lease_range', 'lease_start', 'lease_end'),
        Index('idx_slivers_user_project', 'user_id', 'project_id'),
        Index('idx_slivers_site_host', 'site_id', 'host_id'),
        Index('idx_slivers_project_slice', 'project_id', 'slice_id'),
        Index('idx_slivers_state_type', 'state', 'sliver_type'),
        Index('idx_slivers_ip_subnet', 'ip_subnet'),
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

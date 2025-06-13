#!/usr/bin/env python3
# MIT License
#
# Copyright (component) 2025 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)
import json
import logging
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import List, Optional, Union

from sqlalchemy import create_engine, and_, or_, func, distinct
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta

from reports_api.database import Slices, Slivers, Hosts, Sites, Users, Projects, Components, Interfaces, Base, \
    Membership
from reports_api.response_code.slice_sliver_states import SliceState, SliverStates


@contextmanager
def session_scope(psql_db_engine):
    """Provide a transactional scope around a series of operations."""
    session = scoped_session(sessionmaker(psql_db_engine))
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseManager:
    DEFAULT_TIME_WINDOW_DAYS = 30

    def __init__(self, user: str, password: str, database: str, db_host: str, logger: logging.Logger):
        """
        Initializes the connection to the PostgreSQL database.
        """
        self.db_engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{db_host}/{database}")
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.sessions = {}
        self.logger = logger
        Base.metadata.create_all(self.db_engine)

    def get_session(self):
        thread_id = threading.get_ident()
        if thread_id in self.sessions:
            session = self.sessions.get(thread_id)
        else:
            session = scoped_session(self.session_factory)
            self.sessions[thread_id] = session
        return session

    # -------------------- DELETE DATA --------------------
    def delete_slice(self, slice_id):
        session = self.get_session()
        try:
            slice_object = session.query(Slices).filter(Slices.id == slice_id).first()
            if slice:
                session.delete(slice_object)
                session.commit()
                return True
            return False
        finally:
            session.rollback()

    def delete_project(self, project_id):
        session = self.get_session()
        try:
            project = session.query(Projects).filter(Projects.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.rollback()

    def delete_user(self, user_id):
        session = self.get_session()
        try:
            user = session.query(Users).filter(Users.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        finally:
            session.rollback()

    # -------------------- ADD OR UPDATE DATA --------------------
    def add_or_update_project(
            self,
            project_uuid: str,
            project_name: Optional[str] = None,
            project_type: Optional[str] = None,
            active: Optional[bool] = None,
            created_date: Optional[datetime] = None,
            expires_on: Optional[datetime] = None,
            retired_date: Optional[datetime] = None,
            last_updated: Optional[datetime] = None,
    ) -> int:
        """
        Adds a project if it doesn't exist, otherwise updates its fields.

        :param project_uuid: Unique identifier for the project.
        :param project_name: Name of the project.
        :param project_type: Type or category of the project.
        :param active: Boolean flag indicating whether the project is active.
        :param created_date: Datetime when the project was created.
        :param expires_on: Datetime when the project is set to expire.
        :param retired_date: Datetime when the project was retired.
        :param last_updated: Datetime of the last update. Defaults to current UTC time if not provided.
        :return: ID of the created or updated project.
        :rtype: int
        """

        session = self.get_session()
        try:
            project = session.query(Projects).filter(Projects.project_uuid == project_uuid).first()
            if project:
                if project_name is not None:
                    project.project_name = project_name
                if project_type is not None:
                    project.project_type = project_type
                if active is not None:
                    project.active = active
                if created_date is not None:
                    project.created_date = created_date
                if expires_on is not None:
                    project.expires_on = expires_on
                if retired_date is not None:
                    project.retired_date = retired_date
                project.last_updated = last_updated or datetime.utcnow()
            else:
                project = Projects(
                    project_uuid=project_uuid,
                    project_name=project_name,
                    project_type=project_type,
                    active=active,
                    created_date=created_date or datetime.utcnow(),
                    expires_on=expires_on,
                    retired_date=retired_date,
                    last_updated=last_updated or datetime.utcnow(),
                )
                session.add(project)

            session.commit()
            return project.id
        finally:
            session.rollback()

    def add_or_update_user(
            self,
            user_uuid: str,
            user_email: Optional[str] = None,
            active: Optional[bool] = None,
            name: Optional[str] = None,
            affiliation: Optional[str] = None,
            registered_on: Optional[datetime] = None,
            last_updated: Optional[datetime] = None,
            google_scholar: Optional[str] = None,
            scopus: Optional[str] = None,
    ) -> int:
        """
        Adds a user if it doesn't exist, otherwise updates its fields.

        :param user_uuid: Unique identifier for the user.
        :param user_email: Email address of the user.
        :param active: Boolean flag indicating whether the user is active.
        :param name: Full name of the user.
        :param affiliation: Institutional or organizational affiliation of the user.
        :param registered_on: Datetime when the user registered.
        :param last_updated: Datetime of the last update. Defaults to current UTC time if not provided.
        :param google_scholar: URL or identifier for the user's Google Scholar profile.
        :param scopus: URL or identifier for the user's Scopus profile.
        :return: ID of the created or updated user.
        :rtype: int
        """
        session = self.get_session()
        try:
            user = session.query(Users).filter(Users.user_uuid == user_uuid).first()
            if user:
                if user_email is not None:
                    user.user_email = user_email
                if active is not None:
                    user.active = active
                if name is not None:
                    user.name = name
                if affiliation is not None:
                    user.affiliation = affiliation
                if registered_on is not None:
                    user.registered_on = registered_on
                user.last_updated = last_updated or datetime.utcnow()
                if google_scholar is not None:
                    user.google_scholar = google_scholar
                if scopus is not None:
                    user.scopus = scopus
            else:
                user = Users(
                    user_uuid=user_uuid,
                    user_email=user_email,
                    active=active,
                    name=name,
                    affiliation=affiliation,
                    registered_on=registered_on or datetime.utcnow(),
                    last_updated=last_updated or datetime.utcnow(),
                    google_scholar=google_scholar,
                    scopus=scopus,
                )
                session.add(user)

            session.commit()
            return user.id
        finally:
            session.rollback()

    def add_or_update_membership(self, user_id, project_id, start_time, end_time, membership_type, active):
        """
        Add or update a user membership in a project.

        If a membership record with the same user, project, start time, and type exists, it will be updated.
        Otherwise, a new membership record is inserted.

        :param user_id: ID of the user (foreign key to Users table)
        :type user_id: int
        :param project_id: ID of the project (foreign key to Projects table)
        :type project_id: int
        :param start_time: When the user was added to the project
        :type start_time: datetime.datetime or None
        :param end_time: When the user was removed from the project, if applicable
        :type end_time: datetime.datetime or None
        :param membership_type: Role or type of membership (e.g., member, owner, creator, tokenholder)
        :type membership_type: str
        :param active: Whether the membership is currently active (i.e., not removed)
        :type active: bool

        :return: None
        """
        session = self.get_session()
        try:
            existing = session.query(Membership).filter_by(
                user_id=user_id,
                project_id=project_id,
                start_time=start_time,
                membership_type=membership_type
            ).first()

            if existing:
                existing.end_time = end_time
                existing.active = active
            else:
                membership = Membership(
                    user_id=user_id,
                    project_id=project_id,
                    start_time=start_time,
                    end_time=end_time,
                    membership_type=membership_type,
                    active=active
                )
                session.add(membership)
            session.commit()
        except Exception:
            session.rollback()
            raise

    # -------------------- ADD OR UPDATE SLICE --------------------
    def add_or_update_slice(
                self, project_id: int, user_id: int, slice_guid: str, slice_name: str, state: int,
                lease_start: Optional[datetime], lease_end: Optional[datetime]
        ) -> int:
        """
        Adds a slice if it doesn’t exist, otherwise updates its fields.
        """
        session = self.get_session()
        try:
            slice_obj = session.query(Slices).filter(Slices.slice_guid == slice_guid).first()
            if slice_obj:
                if project_id:
                    slice_obj.project_id = project_id
                if user_id:
                    slice_obj.user_id = user_id
                if slice_name:
                    slice_obj.slice_name = slice_name
                if state:
                    slice_obj.state = state
                if lease_start:
                    slice_obj.lease_start = lease_start
                if lease_end:
                    slice_obj.lease_end = lease_end
            else:
                slice_obj = Slices(
                    project_id=project_id,
                    user_id=user_id,
                    slice_guid=slice_guid,
                    slice_name=slice_name,
                    state=state,
                    lease_start=lease_start,
                    lease_end=lease_end
                )
                session.add(slice_obj)

            session.commit()
            return slice_obj.id
        finally:
            session.rollback()

    # -------------------- ADD OR UPDATE SLIVER --------------------
    def add_or_update_sliver(
        self,
        project_id: int,
        slice_id: int,
        user_id: int,
        host_id: int,
        site_id: int,
        sliver_guid: str,
        state: int,
        sliver_type: str,
        node_id: Optional[str] = None,
        ip_subnet: Optional[str] = None,
        image: Optional[str] = None,
        core: Optional[int] = None,
        ram: Optional[int] = None,
        disk: Optional[int] = None,
        bandwidth: Optional[int] = None,
        lease_start: Optional[datetime] = None,
        lease_end: Optional[datetime] = None,
        error: Optional[str] = None
    ) -> int:
        """
        Adds a sliver if it doesn’t exist, otherwise updates its fields.
        """
        session = self.get_session()
        try:
            sliver = session.query(Slivers).filter(Slivers.sliver_guid == sliver_guid).first()

            if sliver:
                sliver.project_id = project_id
                sliver.slice_id = slice_id
                sliver.user_id = user_id
                sliver.host_id = host_id
                sliver.site_id = site_id
                sliver.state = state
                sliver.sliver_type = sliver_type.lower()
                if ip_subnet:
                    sliver.ip_subnet = ip_subnet
                if image:
                    sliver.image = image
                if core:
                    sliver.core = core
                if ram:
                    sliver.ram = ram
                if disk:
                    sliver.disk = disk
                if bandwidth:
                    sliver.bandwidth = bandwidth
                if lease_start:
                    sliver.lease_start = lease_start
                if lease_end:
                    sliver.lease_end = lease_end
                if error:
                    sliver.error = error
                if node_id:
                    sliver.node_id = node_id
            else:
                sliver = Slivers(
                    project_id=project_id,
                    slice_id=slice_id,
                    user_id=user_id,
                    host_id=host_id,
                    site_id=site_id,
                    sliver_guid=sliver_guid,
                    node_id=node_id,
                    state=state,
                    sliver_type=sliver_type.lower(),
                    ip_subnet=ip_subnet,
                    image=image,
                    core=core,
                    ram=ram,
                    disk=disk,
                    bandwidth=bandwidth,
                    lease_start=lease_start,
                    lease_end=lease_end,
                    error=error
                )
                session.add(sliver)

            session.commit()
            return sliver.id
        finally:
            session.rollback()

    def add_or_update_component(
        self, sliver_id: int, component_guid: str, component_type: str, model: str, bdfs: List[str], node_id: str,
            component_node_id: str
    ) -> str:
        """
        Adds a Component if it doesn't exist, otherwise updates its fields.
        """
        session = self.get_session()
        try:
            component = session.query(Components).filter(
                Components.component_guid == component_guid, Components.sliver_id == sliver_id
            ).first()

            if component:
                if component_type:
                    component.type = component_type.lower()
                if model:
                    component.model = model.lower()
                if bdfs:
                    component.bdfs = bdfs  # Store as JSON
                if node_id:
                    component.node_id = node_id
                if component_node_id:
                    component.component_node_id = component_node_id
            else:
                component = Components(
                    sliver_id=sliver_id,
                    component_guid=component_guid,
                    type=component_type.lower() if component_type else None,
                    model=model.lower() if model else None,
                    bdfs=bdfs,
                    node_id=node_id,
                    component_node_id=component_node_id
                )
                session.add(component)

            session.commit()
            return component.component_guid
        finally:
            session.rollback()

    def add_or_update_interface(self, sliver_id: int, interface_guid: str, vlan: str,
                                bdf: str, local_name: str, device_name: str, name: str, site_id: int) -> str:
        """
        Adds an Interface if it doesn't exist, otherwise updates its fields.
        """
        session = self.get_session()
        try:
            interface = session.query(Interfaces).filter(
                Interfaces.interface_guid == interface_guid, Interfaces.sliver_id == sliver_id
            ).first()

            if interface:
                if local_name:
                    interface.local_name = local_name
                if vlan:
                    interface.vlan = vlan
                if bdf:
                    interface.bdf = bdf
                if device_name:
                    interface.device_name = device_name
                if name:
                    interface.name = name
                if site_id:
                    interface.site_id = site_id
            else:
                interface = Interfaces(
                    sliver_id=sliver_id,
                    interface_guid=interface_guid,
                    local_name=local_name,
                    device_name=device_name,
                    vlan=vlan,
                    bdf=bdf,
                    name=name,
                    site_id=site_id
                )
                session.add(interface)

            session.commit()
            return interface.interface_guid
        finally:
            session.rollback()

    # -------------------- ADD OR UPDATE HOST --------------------
    def add_or_update_host(self, host_name: str, site_id: int) -> int:
        """
        Adds a host if it doesn’t exist, otherwise updates the name.
        """
        session = self.get_session()
        try:
            host = session.query(Hosts).filter(Hosts.name == host_name).first()
            if not host:
                host = Hosts(name=host_name, site_id=site_id)
                session.add(host)

            session.commit()
            return host.id
        finally:
            session.rollback()

    # -------------------- ADD OR UPDATE SITE --------------------
    def add_or_update_site(self, site_name: str) -> int:
        """
        Adds a site if it doesn’t exist, otherwise updates the name.
        """
        session = self.get_session()
        try:
            site = session.query(Sites).filter(Sites.name == site_name).first()
            if not site:
                site = Sites(name=site_name)
                session.add(site)

            session.commit()
            return site.id
        finally:
            session.rollback()

    # -------------------- QUERY DATA --------------------
    @staticmethod
    def __build_time_filter(table: Union[Slices, Slivers], start: datetime = None, end: datetime = None):
        if start is not None or end is not None:
            lease_end_filter = True  # Initialize with True to avoid NoneType comparison
            if start is not None and end is not None:
                lease_end_filter = or_(
                    and_(start <= table.lease_end, table.lease_end <= end),
                    and_(start <= table.lease_start, table.lease_start <= end),
                    and_(table.lease_start <= start, table.lease_end >= end)
                )
            elif start is not None:
                lease_end_filter = start <= table.lease_end
            elif end is not None:
                lease_end_filter = table.lease_end <= end

            return lease_end_filter

    def get_sites(self):
        session = self.get_session()
        try:
            results = session.query(Sites).all()
            site_map = []
            for site in results:
                site_map.append({'name': site.name})
            return site_map
        finally:
            session.rollback()

    def get_hosts(self, site: list[str] = None, exclude_site: list[str] = None):
        session = self.get_session()
        try:
            rows = session.query(Hosts.name, Sites.name.label('site_name')).join(Sites, Hosts.site_id == Sites.id)
            if site:
                rows = rows.filter(Sites.name.in_(site))
            if exclude_site:
                rows = rows.filter(Sites.name.notin_(exclude_site))
            results = rows.all()

            site_map = defaultdict(list)
            for host_name, site_name in results:
                site_map[site_name].append({'name': host_name})

            return [
                {'name': site_name, 'hosts': host_list}
                for site_name, host_list in site_map.items()
            ]
        finally:
            session.rollback()

    def get_projects(self, start_time: datetime = None, end_time: datetime = None, user_email: list[str] = None,
                     user_id: list[str] = None, project_id: list[str] = None, component_type: list[str] = None,
                     slice_id: list[str] = None, slice_state: list[int] = None, component_model: list[str] = None,
                     sliver_type: list[str] = None, sliver_id: list[str] = None, sliver_state: list[int] = None,
                     site: list[str] = None, ip_subnet: list[str] = None, bdf: list[str] = None,
                     vlan: list[str] = None, host: list[str] = None, exclude_user_id: list[str] = None,
                     exclude_user_email: list[str] = None, exclude_project_id: list[str] = None,
                     exclude_site: list[str] = None, exclude_host: list[str] = None, facility: list[str] = None,
                     exclude_slice_state: list[int] = None, exclude_sliver_state: list[int] = None,
                     project_type: list[str] = None, exclude_project_type: list[str] = None, active: bool = None,
                     page: int = 0, per_page: int = 100) -> dict:
        """
        Retrieve a list of projects filtered by related slices, slivers, users, components, interface attributes, and time range.

        :param start_time: start time filter (inclusive).
        :type start_time: datetime, optional
        :param end_time: end time filter (inclusive).
        :type end_time: datetime, optional
        :param user_email: Filter projects by one or more user emails associated with related slices or slivers.
        :type user_email: list[str], optional
        :param user_id: Filter projects by one or more user IDs.
        :type user_id: list[str], optional
        :param project_id: Filter by one or more project IDs.
        :type project_id: list[str], optional
        :param component_type: Filter projects where slivers include components of any of these types.
        :type component_type: list[str], optional
        :param slice_id: Filter projects containing one or more specific slices.
        :type slice_id: list[str], optional
        :param slice_state: Filter projects by one or more slice states.
        :type slice_state: list[int], optional
        :param component_model: Filter projects where slivers include components of any of these models.
        :type component_model: list[str], optional
        :param sliver_type: Filter projects by the types of slivers they include (e.g., VM, Switch).
        :type sliver_type: list[str], optional
        :param sliver_id: Filter by one or more sliver IDs associated with the project.
        :type sliver_id: list[str], optional
        :param sliver_state: Filter projects by the states of their associated slivers.
        :type sliver_state: list[int], optional
        :param site: Filter projects by one or more site names where slivers are deployed.
        :type site: list[str], optional
        :param ip_subnet: Filter projects with slivers using any of the specified IP subnets.
        :type ip_subnet: list[str], optional
        :param bdf: Filter projects by one or more PCI BDFs (Bus:Device.Function) of interfaces or components.
        :type bdf: list[str], optional
        :param vlan: Filter projects by one or more VLANs associated with sliver interfaces.
        :type vlan: list[str], optional
        :param host: Filter projects by one or more hostnames where slivers are running.
        :type host: list[str], optional
        :param facility: Filter by facility
        :type facility: List[str]
        :param exclude_user_id: Exclude projects associated with these user IDs.
        :type exclude_user_id: list[str], optional
        :param exclude_user_email: Exclude projects associated with these user emails.
        :type exclude_user_email: list[str], optional
        :param exclude_project_id: Exclude these project IDs.
        :type exclude_project_id: list[str], optional
        :param exclude_site: Exclude projects deployed at these site names.
        :type exclude_site: list[str], optional
        :param exclude_host: Exclude projects running on these hostnames.
        :type exclude_host: list[str], optional
        :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type exclude_slice_state: List[int]
        :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type exclude_sliver_state: List[int]
        :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
        :type project_type: List[str]
        :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
        :type exclude_project_type: List[str]
        :param active:
        :type active: bool

        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of projects to return per page.
        :type per_page: int, optional

        :return: A dictionary containing the list of projects and associated metadata.
        :rtype: dict
        """
        # Detect if any fields that require Slice JOIN are used
        requires_slice = any([
            slice_id, slice_state, user_email, user_id,
            exclude_user_id, exclude_user_email,
            exclude_slice_state
        ])

        # Detect if any fields that require Sliver JOIN are used
        requires_sliver = any([
            sliver_id, sliver_type, sliver_state, ip_subnet,
            host, site, component_type, component_model, bdf, vlan, facility, exclude_site,
            exclude_host, exclude_sliver_state
        ])

        # Set proper time window if missing
        if requires_sliver:
            now = datetime.utcnow()

            if not start_time and not end_time:
                end_time = now
                start_time = now - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.warning(
                    f"Forcing default time window: {start_time.date()} to {end_time.date()} because sliver-related fields are used without time filter"
                )
            elif start_time and not end_time:
                end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(
                    f"Only start_time given. Setting end_time to 30 days from start_time: {end_time.isoformat()}"
                )
            elif end_time and not start_time:
                # If user only gives end_time, assume start from a default large range before
                start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(
                    f"Only end_time given. Setting start_time to {start_time.isoformat()}"
                )

        session = self.get_session()
        try:
            start_ts = time.time()

            # Base query for Projects
            query = session.query(Projects).distinct()

            if requires_slice or requires_sliver:
                query = query.join(Slices, Slices.project_id == Projects.id)\
                    .join(Users, Slices.user_id == Users.id)

            filters = []

            # Only join Slivers if any Sliver-related filter is used
            if requires_sliver:
                query = query.join(Slivers, Slivers.project_id == Projects.id)

                if host or site or exclude_host or exclude_site:
                    query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                 .outerjoin(Sites, Slivers.site_id == Sites.id)
                if component_type or component_model:
                    query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
                if bdf or vlan or facility:
                    query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            # Build filters
            if start_time or end_time:
                if requires_slice or requires_sliver:
                    time_filter = self.__build_time_filter(Slices, start_time, end_time)
                    if time_filter is not None:
                        filters.append(time_filter)
                else:
                    # Time filter directly on Projects (when no slices/slivers involved)
                    if start_time and end_time:
                        filters.append(or_(
                            and_(Projects.created_date is not None, Projects.created_date.between(start_time, end_time)),
                            and_(Projects.expires_on is not None, Projects.expires_on.between(start_time, end_time))
                        ))
                    elif start_time:
                        filters.append(or_(
                            and_(Projects.created_date is not None, Projects.created_date >= start_time),
                            and_(Projects.expires_on is not None, Projects.expires_on >= start_time)
                        ))
                    elif end_time:
                        filters.append(or_(
                            and_(Projects.created_date is not None, Projects.created_date <= end_time),
                            and_(Projects.expires_on is not None, Projects.expires_on <= end_time)
                        ))
            if project_id:
                filters.append(Projects.project_uuid.in_(project_id))

            if active:
                filters.append(Projects.active == active)

            if project_type:
                filters.append(Projects.project_type.in_(project_type))

            if slice_id:
                filters.append(Slices.slice_guid.in_(slice_id))
            if slice_state:
                filters.append(Slices.state.in_(slice_state))

            if user_id:
                filters.append(Users.user_uuid.in_(user_id))
            if user_email:
                filters.append(Users.user_email.in_(user_email))

            if sliver_id:
                filters.append(Slivers.sliver_guid.in_(sliver_id))
            if sliver_type:
                filters.append(Slivers.sliver_type.in_([t.lower() for t in sliver_type]))
            if sliver_state:
                filters.append(Slivers.state.in_(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet.in_(ip_subnet))

            if component_type:
                filters.append(Components.type.in_([t.lower() for t in component_type]))
            if component_model:
                filters.append(Components.model.in_([t.lower() for t in component_model]))

            if bdf:
                filters.append(Interfaces.bdf == bdf)
            if vlan:
                filters.append(Interfaces.vlan.in_(vlan))
            if facility:
                filters.append(or_(*[Interfaces.name.like(f"%{f}%") for f in facility]))

            if host:
                filters.append(Hosts.name.in_(host))
            if site:
                filters.append(Sites.name.in_(site))

            if exclude_project_id:
                filters.append(Projects.project_uuid.notin_(exclude_project_id))
            if exclude_project_type:
                filters.append(Projects.project_type.notin_(exclude_project_type))
            if exclude_user_id:
                filters.append(Users.user_uuid.notin_(exclude_user_id))
            if exclude_user_email:
                filters.append(Users.user_email.notin_(exclude_user_email))
            if exclude_site:
                filters.append(Sites.name.notin_(exclude_site))
            if exclude_host:
                filters.append(Hosts.name.notin_(exclude_host))
            if exclude_slice_state:
                filters.append(Slices.state.notin_(exclude_slice_state))
            if exclude_sliver_state:
                filters.append(Slivers.state.notin_(exclude_sliver_state))

            if filters:
                query = query.filter(and_(*filters))

            self.logger.info(f"Query Projects (building query) = {time.time() - start_ts:.2f}s")
            query_ts = time.time()

            # Separate lightweight count query
            count_query = session.query(func.count(distinct(Projects.id)))

            if requires_slice or requires_sliver:
                count_query = count_query.join(Slices, Slices.project_id == Projects.id) \
                    .join(Users, Slices.user_id == Users.id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            if requires_sliver:
                count_query = count_query.join(Slivers, Slivers.project_id == Projects.id)

                if host or site or exclude_host or exclude_site:
                    count_query = count_query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                             .outerjoin(Sites, Slivers.site_id == Sites.id)
                if component_type or component_model:
                    count_query = count_query.outerjoin(Components, Slivers.id == Components.sliver_id)
                if bdf or vlan or facility:
                    count_query = count_query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            total_projects = count_query.scalar()

            self.logger.info(f"Query Projects (count) = {time.time() - query_ts:.2f}s")
            fetch_ts = time.time()

            # Apply pagination and fetch results
            projects = query.offset(page * per_page).limit(per_page).all()

            self.logger.info(f"Query Projects (fetch rows) = {time.time() - fetch_ts:.2f}s")
            parse_ts = time.time()

            result = []
            for p in projects:
                project = DatabaseManager.project_to_dict(p)

                if project_id:
                    users = self.get_users(start_time=start_time, end_time=end_time, user_email=user_email,
                                           user_id=user_id, vlan=vlan, facility=facility,
                                           sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                           sliver_state=sliver_state, site=site, host=host,
                                           project_id=project_id, component_model=component_model,
                                           component_type=component_type, ip_subnet=ip_subnet, page=page,
                                           per_page=per_page, exclude_site=exclude_site, exclude_host=exclude_host,
                                           exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                                           exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                                           exclude_user_email=exclude_user_email)
                    project["users"] = {
                        "total": users.get("total"),
                        "data": users.get("users")
                    }
                else:
                    project["users"] = {
                        "total": self.__get_user_count_for_project(p.id)
                    }

                result.append(project)

            self.logger.info(f"Query Projects (dict building) = {time.time() - parse_ts:.2f}s")

            return {
                "total": total_projects,
                "projects": result
            }

        finally:
            session.close()

    def get_users(self, start_time: datetime = None, end_time: datetime = None, user_email: list[str] = None,
                  user_id: list[str] = None, project_id: list[str] = None, component_type: list[str] = None,
                  slice_id: list[str] = None, slice_state: list[int] = None, component_model: list[str] = None,
                  sliver_type: list[str] = None, sliver_id: list[str] = None, sliver_state: list[int] = None,
                  site: list[str] = None, ip_subnet: list[str] = None, bdf: list[str] = None,
                  vlan: list[str] = None, host: list[str] = None, exclude_user_id: list[str] = None,
                  exclude_user_email: list[str] = None, exclude_project_id: list[str] = None,
                  exclude_site: list[str] = None, exclude_host: list[str] = None, facility: list[str] = None,
                  exclude_slice_state: list[int] = None, exclude_sliver_state: list[int] = None,
                  project_type: list[str] = None, exclude_project_type: list[str] = None, active: bool = None,
                  page: int = 0, per_page: int = 100) -> dict:
        """
        Retrieve a list of users filtered by associated slices, slivers, components, network interfaces, and time range.

        :param start_time: Filter users with slivers that start on or after this time.
        :type start_time: datetime, optional
        :param end_time: Filter users with slivers that end on or before this time.
        :type end_time: datetime, optional

        :param user_email: Filter by one or more user email addresses.
        :type user_email: list[str], optional
        :param user_id: Filter by one or more user IDs.
        :type user_id: list[str], optional
        :param project_id: Filter users associated with one or more project IDs.
        :type project_id: list[str], optional
        :param component_type: Filter users whose slivers include components of any of these types.
        :type component_type: list[str], optional
        :param slice_id: Filter users who own one or more specific slices.
        :type slice_id: list[str], optional
        :param slice_state: Filter users by the state of their associated slices.
        :type slice_state: list[int], optional
        :param component_model: Filter users whose slivers include components of any of these models.
        :type component_model: list[str], optional
        :param sliver_type: Filter users by the types of their associated slivers (e.g., VM, Switch).
        :type sliver_type: list[str], optional
        :param sliver_id: Filter users associated with one or more specific sliver IDs.
        :type sliver_id: list[str], optional
        :param sliver_state: Filter users by the state of their associated slivers.
        :type sliver_state: list[int], optional
        :param site: Filter users based on the site names where their slivers are deployed.
        :type site: list[str], optional
        :param ip_subnet: Filter users whose slivers use any of the specified IP subnets.
        :type ip_subnet: list[str], optional
        :param bdf: Filter users based on PCI BDF (Bus:Device.Function) values of interfaces/components.
        :type bdf: list[str], optional
        :param vlan: Filter users by one or more VLANs associated with their sliver interfaces.
        :type vlan: list[str], optional
        :param host: Filter users by hostnames where their slivers are running.
        :type host: list[str], optional
        :param facility: Filter by facility
        :type facility: List[str]
        :param exclude_user_id: Exclude users with these user IDs.
        :type exclude_user_id: list[str], optional
        :param exclude_user_email: Exclude users with these email addresses.
        :type exclude_user_email: list[str], optional
        :param exclude_project_id: Exclude users associated with these project IDs.
        :type exclude_project_id: list[str], optional
        :param exclude_site: Exclude users whose slivers are deployed at these sites.
        :type exclude_site: list[str], optional
        :param exclude_host: Exclude users whose slivers are hosted on these hosts.
        :type exclude_host: list[str], optional
        :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type exclude_slice_state: List[int]
        :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type exclude_sliver_state: List[int]
        :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
        :type project_type: List[str]
        :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
        :type exclude_project_type: List[str]
        :param active:
        :type active: bool
        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of users to return per page.
        :type per_page: int, optional

        :return: A dictionary containing the list of users and pagination metadata.
        :rtype: dict
        """
        session = self.get_session()
        try:
            start_ts = time.time()

            requires_slice = any([
                slice_id, slice_state, user_email, user_id,
                exclude_user_id, exclude_user_email,
                exclude_slice_state
            ])

            # Detect if sliver-related fields are involved
            requires_sliver = any([
                sliver_id, sliver_type, sliver_state, ip_subnet,
                host, site, component_type, component_model, bdf, vlan, facility,
                exclude_site, exclude_sliver_state, exclude_host
            ])

            now = datetime.utcnow()

            # Auto-set missing time filters if needed
            if requires_sliver:
                if not start_time and not end_time:
                    end_time = now
                    start_time = now - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                    self.logger.warning(
                        f"Forcing default time window: {start_time.date()} to {end_time.date()} because sliver-related fields are used without time filter"
                    )
                elif start_time and not end_time:
                    end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                    self.logger.info(f"Only start_time given. Setting end_time to 30 days from start_time: {end_time.isoformat()}")
                elif end_time and not start_time:
                    start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                    self.logger.info(f"Only end_time given. Setting start_time to {start_time.isoformat()}")

            # Base query for Users
            query = session.query(Users).distinct()

            if requires_slice or requires_sliver:
                query = query.join(Slices, Users.id == Slices.user_id)

            # Determine whether to use Slices or Membership for joining Projects
            if project_id:
                if requires_slice or requires_sliver:
                    query = query.join(Projects, Slices.project_id == Projects.id)
                else:
                    query = query.join(Membership, Membership.user_id == Users.id) \
                        .join(Projects, Projects.id == Membership.project_id)

            # Only join Slivers if needed
            if requires_sliver:
                query = query.join(Slivers, Users.id == Slivers.user_id)

                if host or site or exclude_host or exclude_site:
                    query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id).outerjoin(Sites,
                                                                                          Slivers.site_id == Sites.id)

                if component_type or component_model:
                    query = query.outerjoin(Components, Slivers.id == Components.sliver_id)

                if bdf or vlan or facility:
                    query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time range filter
            if start_time or end_time:
                if requires_slice or requires_sliver:
                    time_filter = self.__build_time_filter(Slices, start_time, end_time)
                    if time_filter is not None:
                        filters.append(time_filter)
                else:
                    # Apply time-based filter on Membership if time window is specified
                    st = start_time or (end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS))
                    et = end_time or (start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS))
                    filters.append(
                        or_(
                            and_(Membership.start_time <= et, Membership.end_time >= st),  # overlapping window
                            and_(Membership.start_time <= et, Membership.end_time.is_(None))  # still active
                        )
                    )
            # User filters
            if user_email:
                filters.append(Users.user_email.in_(user_email))
            if user_id:
                filters.append(Users.user_uuid.in_(user_id))

            # Project filters
            if project_id:
                filters.append(Projects.project_uuid.in_(project_id))

            if project_type:
                filters.append(Projects.project_type.in_(project_type))

            if active:
                filters.append(Projects.active == active)

            # Slice filters
            if slice_id:
                filters.append(Slices.slice_guid.in_(slice_id))
            if slice_state:
                filters.append(Slices.state.in_(slice_state))

            # Sliver filters
            if sliver_id:
                filters.append(Slivers.sliver_guid.in_(sliver_id))
            if sliver_type:
                filters.append(Slivers.sliver_type.in_([t.lower() for t in sliver_type]))
            if sliver_state:
                filters.append(Slivers.state.in_(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet.in_(ip_subnet))

            if component_type:
                filters.append(Components.type.in_([t.lower() for t in component_type]))
            if component_model:
                filters.append(Components.model.in_([t.lower() for t in component_model]))

            if bdf:
                filters.append(Interfaces.bdf.in_(bdf))
            if vlan:
                filters.append(Interfaces.vlan.in_(vlan))
            if facility:
                filters.append(or_(*[Interfaces.name.like(f"%{f}%") for f in facility]))

            # Host and Site
            if site:
                filters.append(Sites.name.in_(site))
            if host:
                filters.append(Hosts.name.in_(host))

            # Exclusions
            if exclude_project_id:
                filters.append(Projects.project_uuid.notin_(exclude_project_id))
            if exclude_project_type:
                filters.append(Projects.project_type.notin_(exclude_project_type))
            if exclude_user_id:
                filters.append(Users.user_uuid.notin_(exclude_user_id))
            if exclude_user_email:
                filters.append(Users.user_email.notin_(exclude_user_email))
            if exclude_site:
                filters.append(Sites.name.notin_(exclude_site))
            if exclude_host:
                filters.append(Hosts.name.notin_(exclude_host))
            if exclude_slice_state:
                filters.append(Slices.state.notin_(exclude_slice_state))
            if exclude_sliver_state:
                filters.append(Slivers.state.notin_(exclude_sliver_state))

            self.logger.info(f"KOMAL --- {query}")
            # Apply filters
            if filters:
                query = query.filter(and_(*filters))

            self.logger.info(f"Query Users (building query) = {time.time() - start_ts:.2f}s")
            count_ts = time.time()

            # Use DISTINCT COUNT
            count_query = session.query(func.count(distinct(Users.id)))

            if requires_slice or requires_sliver:
                count_query = count_query.join(Slices, Users.id == Slices.user_id)

            if project_id:
                if requires_slice or requires_sliver:
                    count_query = count_query.join(Projects, Slices.project_id == Projects.id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            if requires_sliver:
                count_query = count_query.join(Slivers, Users.id == Slivers.user_id)

                if host or site or exclude_host or exclude_site:
                    count_query = count_query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                             .outerjoin(Sites, Slivers.site_id == Sites.id)

                if component_type or component_model:
                    count_query = count_query.outerjoin(Components, Slivers.id == Components.sliver_id)

                if bdf or vlan or facility:
                    count_query = count_query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            total_users = count_query.scalar()

            self.logger.info(f"Query Users (count) = {time.time() - count_ts:.2f}s")
            fetch_ts = time.time()

            # Apply pagination and fetch results
            users = query.offset(page * per_page).limit(per_page).all()

            self.logger.info(f"Query Users (fetch rows) = {time.time() - fetch_ts:.2f}s")
            parse_ts = time.time()

            result = []
            for u in users:
                user = DatabaseManager.user_to_dict(u)

                if project_id or user_id or user_email:
                    slices = self.get_slices(
                        start_time=start_time, end_time=end_time, user_email=[u.user_email],
                        user_id=[u.user_uuid], vlan=vlan, sliver_id=sliver_id, sliver_type=sliver_type,
                        slice_id=slice_id, bdf=bdf, sliver_state=sliver_state, site=site, host=host,
                        project_id=project_id, component_model=component_model, component_type=component_type,
                        ip_subnet=ip_subnet, exclude_site=exclude_site, exclude_host=exclude_host,
                        exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                        exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                        exclude_user_email=exclude_user_email
                    )
                    user["slices"] = {
                        "total": slices.get("total"),
                        "data": slices.get("slices")
                    }
                else:
                    # Simpler direct count
                    user["slices"] = {
                        "total": session.query(func.count(Slices.id)).filter(Slices.user_id == u.id).scalar()
                    }

                result.append(user)

            self.logger.info(f"Query Users (dict building) = {time.time() - parse_ts:.2f}s")

            return {
                "total": total_users,
                "users": result
            }

        finally:
            session.close()

    def get_slivers(self, start_time: datetime = None, end_time: datetime = None, user_email: list[str] = None,
                    user_id: list[str] = None, project_id: list[str] = None, component_type: list[str] = None,
                    slice_id: list[str] = None, slice_state: list[int] = None, component_model: list[str] = None,
                    sliver_type: list[str] = None, sliver_id: list[str] = None, sliver_state: list[int] = None,
                    site: list[str] = None, ip_subnet: list[str] = None, bdf: list[str] = None,
                    vlan: list[str] = None, host: list[str] = None, exclude_user_id: list[str] = None,
                    exclude_user_email: list[str] = None, exclude_project_id: list[str] = None,
                    exclude_site: list[str] = None, exclude_host: list[str] = None, facility: list[str] = None,
                    exclude_slice_state: list[int] = None, exclude_sliver_state: list[int] = None,
                    page: int = 0, per_page: int = 100) -> dict:
        """
        Retrieve a list of slivers filtered by time range, user, project, slice, component, and network-related fields.

        :param start_time: Filter slivers that start on or after this time.
        :type start_time: datetime, optional
        :param end_time: Filter slivers that end on or before this time.
        :type end_time: datetime, optional
        :param user_email: Filter by one or more user email addresses.
        :type user_email: list[str], optional
        :param user_id: Filter by one or more user IDs.
        :type user_id: list[str], optional
        :param project_id: Filter by one or more project IDs associated with the sliver.
        :type project_id: list[str], optional
        :param component_type: Filter by one or more component types (e.g., FPGA, GPU, SmartNIC).
        :type component_type: list[str], optional
        :param slice_id: Filter by one or more slice IDs containing the sliver.
        :type slice_id: list[str], optional
        :param slice_state: Filter slivers by the state of their parent slices.
        :type slice_state: list[int], optional
        :param component_model: Filter by one or more component models (e.g., Tesla T4, ConnectX-5).
        :type component_model: list[str], optional
        :param sliver_type: Filter by one or more types of slivers (e.g., VM, Switch).
        :type sliver_type: list[str], optional
        :param sliver_id: Filter by one or more specific sliver IDs.
        :type sliver_id: list[str], optional
        :param sliver_state: Filter by one or more sliver states (integer-based status code).
        :type sliver_state: list[int], optional
        :param site: Filter by one or more site names hosting the slivers.
        :type site: list[str], optional
        :param ip_subnet: Filter by one or more IP subnets assigned to slivers.
        :type ip_subnet: list[str], optional
        :param bdf: Filter by one or more PCI BDF (Bus:Device.Function) values.
        :type bdf: list[str], optional
        :param vlan: Filter by one or more VLANs associated with the sliver interfaces.
        :type vlan: list[str], optional
        :param host: Filter by one or more hostnames where slivers are instantiated.
        :type host: list[str], optional
        :param facility: Filter by facility
        :type facility: List[str]
        :param exclude_user_id: Exclude slivers associated with these user IDs.
        :type exclude_user_id: list[str], optional
        :param exclude_user_email: Exclude slivers associated with these user email addresses.
        :type exclude_user_email: list[str], optional
        :param exclude_project_id: Exclude slivers belonging to these project IDs.
        :type exclude_project_id: list[str], optional
        :param exclude_site: Exclude slivers hosted at these site names.
        :type exclude_site: list[str], optional
        :param exclude_host: Exclude slivers hosted on these hostnames.
        :type exclude_host: list[str], optional
        :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type exclude_slice_state: List[int]
        :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type exclude_sliver_state: List[int]

        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of slivers to return per page.
        :type per_page: int, optional

        :return: A dictionary containing the list of slivers and pagination metadata.
        :rtype: dict
        """
        session = self.get_session()
        try:
            start_ts = time.time()
            now = datetime.utcnow()

            # Always force time filter if missing (because Slivers is big!)
            if start_time and not end_time:
                end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(f"Only start_time given. Setting end_time to 30 days from start_time: {end_time.isoformat()}")
            elif end_time and not start_time:
                start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(f"Only end_time given. Setting start_time to {start_time.isoformat()}")

            query = session.query(Slivers).distinct()

            # Join only what's necessary
            query = query.join(Slices, Slivers.slice_id == Slices.id)
            query = query.join(Users, Slivers.user_id == Users.id)
            query = query.join(Projects, Slivers.project_id == Projects.id)

            if host or site or exclude_host or exclude_site:
                query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                             .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            if start_time or end_time:
                time_filter = self.__build_time_filter(Slivers, start_time, end_time)
                if time_filter is not None:
                    filters.append(time_filter)

            # User filters
            if user_email:
                filters.append(Users.user_email.in_(user_email))
            if user_id:
                filters.append(Users.user_uuid.in_(user_id))

            # Project filters
            if project_id:
                filters.append(Projects.project_uuid.in_(project_id))

            # Slice filters
            if slice_id:
                filters.append(Slices.slice_guid.in_(slice_id))
            if slice_state:
                filters.append(Slices.state.in_(slice_state))

            # Sliver filters
            if sliver_id:
                filters.append(Slivers.sliver_guid.in_(sliver_id))
            if sliver_type:
                filters.append(Slivers.sliver_type.in_([t.lower() for t in sliver_type]))
            if sliver_state:
                filters.append(Slivers.state.in_(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet.in_(ip_subnet))

            if component_type:
                filters.append(Components.type.in_([t.lower() for t in component_type]))
            if component_model:
                filters.append(Components.model.in_([t.lower() for t in component_model]))

            if bdf:
                filters.append(Interfaces.bdf.in_(bdf))
            if vlan:
                filters.append(Interfaces.vlan.in_(vlan))
            if facility:
                filters.append(or_(*[Interfaces.name.like(f"%{f}%") for f in facility]))

            if site:
                filters.append(Sites.name.in_(site))
            if host:
                filters.append(Hosts.name.in_(host))

            # Exclude filters
            if exclude_project_id:
                filters.append(Projects.project_uuid.notin_(exclude_project_id))
            if exclude_user_id:
                filters.append(Users.user_uuid.notin_(exclude_user_id))
            if exclude_user_email:
                filters.append(Users.user_email.notin_(exclude_user_email))
            if exclude_site:
                filters.append(Sites.name.notin_(exclude_site))
            if exclude_host:
                filters.append(Hosts.name.notin_(exclude_host))
            if exclude_slice_state:
                filters.append(Slices.state.notin_(exclude_slice_state))
            if exclude_sliver_state:
                filters.append(Slivers.state.notin_(exclude_sliver_state))

            if filters:
                query = query.filter(and_(*filters))

            self.logger.info(f"Query Slivers (build query) = {time.time() - start_ts:.2f}s")
            count_ts = time.time()

            # Count distinct slivers
            count_query = session.query(func.count(distinct(Slivers.id)))
            if filters:
                count_query = count_query.filter(and_(*filters))

            count_query = count_query.join(Slices, Slivers.slice_id == Slices.id)\
                                     .join(Users, Slivers.user_id == Users.id)\
                                     .join(Projects, Slivers.project_id == Projects.id)

            if host or site or exclude_host or exclude_site:
                count_query = count_query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                         .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                count_query = count_query.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                count_query = count_query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            total_slivers = count_query.scalar()

            self.logger.info(f"Query Slivers (count) = {time.time() - count_ts:.2f}s")
            fetch_ts = time.time()

            slivers = query.offset(page * per_page).limit(per_page).all()

            self.logger.info(f"Query Slivers (fetch rows) = {time.time() - fetch_ts:.2f}s")
            parse_ts = time.time()

            # Preload Users, Projects, Hosts, Sites, Slices to avoid N queries
            user_ids = {s.user_id for s in slivers}
            project_ids = {s.project_id for s in slivers}
            site_ids = {s.site_id for s in slivers if s.site_id}
            host_ids = {s.host_id for s in slivers if s.host_id}
            slice_ids = {s.slice_id for s in slivers}

            users_map = {u.id: u for u in session.query(Users).filter(Users.id.in_(user_ids)).all()}
            projects_map = {p.id: p for p in session.query(Projects).filter(Projects.id.in_(project_ids)).all()}
            sites_map = {site.id: site for site in
                         session.query(Sites).filter(Sites.id.in_(site_ids)).all()} if site_ids else {}
            hosts_map = {host.id: host for host in
                         session.query(Hosts).filter(Hosts.id.in_(host_ids)).all()} if host_ids else {}
            slices_map = {slice.id: slice for slice in session.query(Slices).filter(Slices.id.in_(slice_ids)).all()}

            result = []
            for s in slivers:
                user = users_map.get(s.user_id)
                project = projects_map.get(s.project_id)
                site_name = sites_map.get(s.site_id).name if s.site_id and sites_map.get(s.site_id) else None
                host_name = hosts_map.get(s.host_id).name if s.host_id and hosts_map.get(s.host_id) else None
                slice_guid = slices_map.get(s.slice_id).slice_guid if slices_map.get(s.slice_id) else None

                sliver = DatabaseManager.sliver_to_dict(sliver=s, user=user, project=project,
                                                        site=site_name, host=host_name, slice_id=slice_guid)
                components = session.query(Components).filter(Components.sliver_id == s.id).all()
                interfaces = session.query(Interfaces).filter(Interfaces.sliver_id == s.id).all()
                sliver["components"] = {
                    "total": len(components),
                    "data": [DatabaseManager.component_to_dict(c) for c in components]
                }
                sliver["interfaces"] = {
                    "total": len(interfaces),
                    "data": [DatabaseManager.interface_to_dict(i) for i in interfaces]
                }
                '''
                if sliver_id or slice_id:
                    components = session.query(Components).filter(Components.sliver_id == s.id).all()
                    interfaces = session.query(Interfaces).filter(Interfaces.sliver_id == s.id).all()
                    sliver["components"] = {
                        "total": len(components),
                        "data": [DatabaseManager.component_to_dict(c) for c in components]
                    }
                    sliver["interfaces"] = {
                        "total": len(interfaces),
                        "data": [DatabaseManager.interface_to_dict(i) for i in interfaces]
                    }
                else:
                    component_count = session.query(func.count()).select_from(Components).filter(
                        Components.sliver_id == s.id).scalar()
                    interface_count = session.query(func.count()).select_from(Interfaces).filter(
                        Interfaces.sliver_id == s.id).scalar()
                    sliver["components"] = {
                        "total": component_count
                    }
                    sliver["interfaces"] = {
                        "total": interface_count
                    }
                '''
                result.append(sliver)

            self.logger.info(f"Query Slivers (dict building) = {time.time() - parse_ts:.2f}s")

            return {
                "total": total_slivers,
                "slivers": result
            }

        finally:
            session.close()

    def get_slices(self, start_time: datetime = None, end_time: datetime = None, user_email: list[str] = None,
                   user_id: list[str] = None, project_id: list[str] = None, component_type: list[str] = None,
                   slice_id: list[str] = None, slice_state: list[int] = None, component_model: list[str] = None,
                   sliver_type: list[str] = None, sliver_id: list[str] = None, sliver_state: list[int] = None,
                   site: list[str] = None, ip_subnet: list[str] = None, bdf: list[str] = None,
                   vlan: list[str] = None, host: list[str] = None, exclude_user_id: list[str] = None,
                   exclude_user_email: list[str] = None, exclude_project_id: list[str] = None,
                   exclude_site: list[str] = None, exclude_host: list[str] = None, facility: list[str] = None,
                   exclude_slice_state: list[int] = None, exclude_sliver_state: list[int] = None,
                   page: int = 0, per_page: int = 100) -> dict:
        """
        Retrieve a list of slices filtered by time, user, project, sliver, component, and network attributes.

        :param start_time: Filter slices with slivers starting after this time.
        :type start_time: datetime, optional
        :param end_time: Filter slices with slivers ending before this time.
        :type end_time: datetime, optional
        :param user_email: Filter by one or more user email addresses.
        :type user_email: list[str], optional
        :param user_id: Filter by one or more user IDs.
        :type user_id: list[str], optional
        :param project_id: Filter by one or more project IDs.
        :type project_id: list[str], optional
        :param component_type: Filter slices that include components of any of these types (e.g., GPU, SmartNIC).
        :type component_type: list[str], optional
        :param slice_id: Filter by one or more specific slice IDs.
        :type slice_id: list[str], optional
        :param slice_state: Filter by one or more slice states.
        :type slice_state: list[int], optional
        :param component_model: Filter by one or more component models (e.g., ConnectX-6, A30).
        :type component_model: list[str], optional
        :param sliver_type: Filter by one or more sliver types (e.g., VM, Switch, Facility).
        :type sliver_type: list[str], optional
        :param sliver_id: Filter by one or more sliver IDs.
        :type sliver_id: list[str], optional
        :param sliver_state: Filter by one or more sliver states (integer-based status code).
        :type sliver_state: list[int], optional
        :param site: Filter by one or more site names where the slivers are located.
        :type site: list[str], optional
        :param ip_subnet: Filter slivers by one or more IP subnets.
        :type ip_subnet: list[str], optional
        :param bdf: Filter by one or more PCI BDF (Bus:Device.Function) values.
        :type bdf: list[str], optional
        :param vlan: Filter by one or more VLAN IDs associated with interfaces.
        :type vlan: list[str], optional
        :param host: Filter by one or more hostnames where slivers are running.
        :type host: list[str], optional
        :param facility: Filter by facility
        :type facility: List[str]
        :param exclude_user_id: Exclude slices associated with these user IDs.
        :type exclude_user_id: list[str], optional
        :param exclude_user_email: Exclude slices associated with these user email addresses.
        :type exclude_user_email: list[str], optional
        :param exclude_project_id: Exclude slices belonging to these project IDs.
        :type exclude_project_id: list[str], optional
        :param exclude_site: Exclude slices deployed at these site names.
        :type exclude_site: list[str], optional
        :param exclude_host: Exclude slices running on these hostnames.
        :type exclude_host: list[str], optional
        :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type exclude_slice_state: List[int]
        :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type exclude_sliver_state: List[int]

        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of slices to return per page.
        :type per_page: int, optional

        :return: A dictionary containing the list of slices and metadata like pagination.
        :rtype: dict
        """
        session = self.get_session()
        try:
            start_ts = time.time()

            # Force default time range if no time provided
            if start_time and not end_time:
                end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(f"Only start_time given. Setting end_time to 30 days from start_time: {end_time.isoformat()}")
            elif end_time and not start_time:
                start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
                self.logger.info(f"Only end_time given. Setting start_time to {start_time.isoformat()}")

            query = session.query(Slices).distinct()

            # Always join user and project
            query = query.join(Users, Slices.user_id == Users.id)
            query = query.join(Projects, Slices.project_id == Projects.id)

            # Join slivers only if needed
            join_slivers = any([
                sliver_id, sliver_type, sliver_state, ip_subnet,
                site, host, component_type, component_model, bdf, vlan, facility,
                exclude_site, exclude_host, exclude_sliver_state
            ])

            if join_slivers:
                query = query.join(Slivers, Slices.id == Slivers.slice_id)
                if host or site or exclude_host or exclude_site:
                    query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id).outerjoin(Sites, Slivers.site_id == Sites.id)
                if component_type or component_model:
                    query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
                if bdf or vlan or facility:
                    query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time filter (on Slices)
            if start_time or end_time:
                time_filter = self.__build_time_filter(Slices, start_time, end_time)
                if time_filter is not None:
                    filters.append(time_filter)

            # Filters
            if user_email:
                filters.append(Users.user_email.in_(user_email))
            if user_id:
                filters.append(Users.user_uuid.in_(user_id))

            if project_id:
                filters.append(Projects.project_uuid.in_(project_id))

            if slice_id:
                filters.append(Slices.slice_guid.in_(slice_id))
            if slice_state:
                filters.append(Slices.state.in_(slice_state))

            if sliver_id:
                filters.append(Slivers.sliver_guid.in_(sliver_id))
            if sliver_type:
                filters.append(Slivers.sliver_type.in_([t.lower() for t in sliver_type]))
            if sliver_state:
                filters.append(Slivers.state.in_(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet.in_(ip_subnet))

            if component_type:
                filters.append(Components.type.in_([t.lower() for t in component_type]))
            if component_model:
                filters.append(Components.model.in_([t.lower() for t in component_model]))

            if bdf:
                filters.append(Interfaces.bdf.in_(bdf))
            if vlan:
                filters.append(Interfaces.vlan.in_(vlan))
            if facility:
                filters.append(or_(*[Interfaces.name.like(f"%{f}%") for f in facility]))

            if site:
                filters.append(Sites.name.in_(site))
            if host:
                filters.append(Hosts.name.in_(host))

            # Exclusions
            if exclude_project_id:
                filters.append(Projects.project_uuid.notin_(exclude_project_id))
            if exclude_user_id:
                filters.append(Users.user_uuid.notin_(exclude_user_id))
            if exclude_user_email:
                filters.append(Users.user_email.notin_(exclude_user_email))
            if exclude_site:
                filters.append(Sites.name.notin_(exclude_site))
            if exclude_host:
                filters.append(Hosts.name.notin_(exclude_host))
            if exclude_slice_state:
                filters.append(Slices.state.notin_(exclude_slice_state))
            if exclude_sliver_state:
                filters.append(Slivers.state.notin_(exclude_sliver_state))

            if filters:
                query = query.filter(and_(*filters))

            self.logger.info(f"Query Slices (build query) = {time.time() - start_ts:.2f}s")
            count_ts = time.time()

            # Count distinct slices
            count_query = session.query(func.count(distinct(Slices.id)))
            count_query = count_query.join(Users, Slices.user_id == Users.id).join(Projects, Slices.project_id == Projects.id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            if join_slivers:
                count_query = count_query.join(Slivers, Slices.id == Slivers.slice_id)

                if host or site or exclude_host or exclude_site:
                    count_query = count_query.outerjoin(Hosts, Slivers.host_id == Hosts.id).outerjoin(Sites, Slivers.site_id == Sites.id)
                if component_type or component_model:
                    count_query = count_query.outerjoin(Components, Slivers.id == Components.sliver_id)
                if bdf or vlan or facility:
                    count_query = count_query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            if filters:
                count_query = count_query.filter(and_(*filters))

            total_slices = count_query.scalar()

            self.logger.info(f"Query Slices (count) = {time.time() - count_ts:.2f}s")
            fetch_ts = time.time()

            slices = query.offset(page * per_page).limit(per_page).all()

            self.logger.info(f"Query Slices (fetch rows) = {time.time() - fetch_ts:.2f}s")
            parse_ts = time.time()

            # Preload Users and Projects to avoid per-slice query
            user_ids = {s.user_id for s in slices}
            project_ids = {s.project_id for s in slices}

            users_map = {u.id: u for u in session.query(Users).filter(Users.id.in_(user_ids)).all()}
            projects_map = {p.id: p for p in session.query(Projects).filter(Projects.id.in_(project_ids)).all()}

            result = []
            for s in slices:
                user = users_map.get(s.user_id)
                project = projects_map.get(s.project_id)

                slice_obj = DatabaseManager.slice_to_dict(slice=s, user=user, project=project)

                if slice_id:
                    slivers = self.get_slivers(
                        start_time=start_time, end_time=end_time, user_email=user_email,
                        user_id=user_id, vlan=vlan, sliver_id=sliver_id, sliver_type=sliver_type, slice_id=[s.slice_guid],
                        bdf=bdf, sliver_state=sliver_state, site=site, host=host, project_id=project_id,
                        component_model=component_model, component_type=component_type, ip_subnet=ip_subnet,
                        exclude_site=exclude_site, exclude_host=exclude_host,
                        exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                        exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                        exclude_user_email=exclude_user_email
                    )
                    slice_obj["slivers"] = {
                        "total": slivers.get("total"),
                        "data": slivers.get("slivers")
                    }
                else:
                    slice_obj["slivers"] = {
                        "total": session.query(func.count(Slivers.id)).filter(Slivers.slice_id == s.id).scalar()
                    }

                result.append(slice_obj)

            self.logger.info(f"Query Slices (dict building) = {time.time() - parse_ts:.2f}s")

            return {
                "total": total_slices,
                "slices": result
            }

        finally:
            session.close()

    @staticmethod
    def interface_to_dict(interface: Interfaces):
        return {
            "interface_guid": interface.interface_guid,
            "bdf": interface.bdf,
            "vlan": interface.vlan,
            "local_name": interface.local_name,
            "device_name": interface.device_name,
            "name": interface.name,
        }

    @staticmethod
    def component_to_dict(component: Components):
        return {
            "component_guid": component.component_guid,
            "node_id": component.node_id,
            "component_node_id": component.component_node_id,
            "type": component.type,
            "model": component.model,
            "bdfs": component.bdfs,
        }

    @staticmethod
    def sliver_to_dict(sliver: Slivers, user: Users, project: Projects, site: str, host: str, slice_id: str):
        return {
            "slice_id": slice_id,
            "sliver_id": sliver.sliver_guid,
            "node_id": sliver.node_id,
            "state": SliverStates(sliver.state).name,
            "sliver_type": sliver.sliver_type,
            "ip_subnet": sliver.ip_subnet,
            "image": sliver.image,
            "core": sliver.core,
            "ram": sliver.ram,
            "site": site,
            "host": host,
            "disk": sliver.disk,
            "bandwidth": sliver.bandwidth,
            "lease_start": sliver.lease_start.isoformat() if sliver.lease_start else None,
            "lease_end": sliver.lease_end.isoformat() if sliver.lease_end else None,
            "user_id": user.user_uuid,
            "user_email": user.user_email,
            "project_id": project.project_uuid,
            "project_name": project.project_name,
        }

    @staticmethod
    def slice_to_dict(slice: Slices, user: Users, project: Projects):
        return {
            "slice_id": slice.slice_guid,
            "slice_name": slice.slice_name,
            "state": SliceState(slice.state).name,
            "lease_start": slice.lease_start.isoformat() if slice.lease_start else None,
            "lease_end": slice.lease_end.isoformat() if slice.lease_end else None,
            "user_id": user.user_uuid,
            "user_email": user.user_email,
            "project_id": project.project_uuid,
            "project_name": project.project_name,
        }

    @staticmethod
    def user_to_dict(user: Users):
        return {
            "user_id": user.user_uuid,
            "user_email": user.user_email,
            "active": user.active,
            "user_name": user.name,
            "affiliation": user.affiliation,
            "registered_on": user.registered_on.isoformat() if user.registered_on else None,
            "last_updated": user.last_updated.isoformat() if user.last_updated else None,
            "google_scholar": user.google_scholar,
            "scopus": user.scopus,
        }

    @staticmethod
    def project_to_dict(project: Projects):
        return {
            "project_id": project.project_uuid,
            "project_name": project.project_name,
            "project_type": project.project_type,
            "active": project.active,
            "created_date": project.created_date.isoformat() if project.created_date else None,
            "expires_on": project.expires_on.isoformat() if project.expires_on else None,
            "retired_date": project.retired_date.isoformat() if project.retired_date else None,
            "last_updated": project.last_updated.isoformat() if project.last_updated else None
        }

    def __get_projects_for_user(self, user_uuid: str):
        session = self.get_session()
        try:
            projects = (
                session.query(Projects)
                    .distinct()
                    .join(Membership, Membership.project_id == Projects.id)
                    .join(Users, Membership.user_id == Users.id)
                    .filter(
                    Users.user_uuid == user_uuid,
                    Membership.active.is_(True)
                )
                    .all()
            )
            return projects
        finally:
            session.rollback()

    def __get_user_count_for_project(self, project_id: int):
        session = self.get_session()
        try:
            user_count = session.query(func.count(distinct(Membership.user_id))) \
                .filter(
                Membership.project_id == project_id,
                Membership.active.is_(True)
            ).scalar()
            self.logger.info(f"KOMAL --- User count for {project_id} {user_count}")
            return user_count
        finally:
            session.rollback()

    def get_slice_by_slice_id(self, slice_id: str) -> bool:
        """
        Retrieve a slice by its ID.

        :param slice_id: The ID of the slice to retrieve.
        :type slice_id: str

        :return: A dictionary containing the slice details.
        :rtype: dict
        """
        session = self.get_session()
        try:
            slice_obj = session.query(Slices).filter(Slices.slice_guid == slice_id).first()
            if not slice_obj:
                return False

            user = session.query(Users).filter(Users.id == slice_obj.user_id).first()
            project = session.query(Projects).filter(Projects.id == slice_obj.project_id).first()

            return True
        finally:
            session.close()
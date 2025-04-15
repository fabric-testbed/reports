#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2025 FABRIC Testbed
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
import threading
from collections import defaultdict
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

from analytics_api.database import Slices, Slivers, Hosts, Sites, Users, Projects, Components, Interfaces, Base


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
    def __init__(self, user: str, password: str, database: str, db_host: str):
        """
        Initializes the connection to the PostgreSQL database.
        """
        self.db_engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{db_host}/{database}", echo=True)
        self.session_factory = sessionmaker(bind=self.db_engine)
        self.sessions = {}

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
    def add_or_update_project(self, project_uuid: str, project_name: Optional[str] = None) -> int:
        """
        Adds a project if it doesn't exist, otherwise updates the name.
        """
        session = self.get_session()
        try:
            project = session.query(Projects).filter(Projects.project_uuid == project_uuid).first()
            if project:
                if project_name:
                    project.project_name = project_name
            else:
                project = Projects(project_uuid=project_uuid, project_name=project_name)
                session.add(project)

            session.commit()
            return project.id
        finally:
            session.rollback()

    def add_or_update_user(self, user_uuid: str, user_email: Optional[str] = None) -> int:
        """
        Adds a user if it doesn't exist, otherwise updates the email.
        """
        session = self.get_session()
        try:
            user = session.query(Users).filter(Users.user_uuid == user_uuid).first()
            if user:
                if user_email:
                    user.user_email = user_email
            else:
                user = Users(user_uuid=user_uuid, user_email=user_email)
                session.add(user)

            session.commit()
            return user.id
        finally:
            session.rollback()

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
                slice_obj.project_id = project_id
                slice_obj.user_id = user_id
                slice_obj.slice_name = slice_name
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
                sliver.sliver_type = sliver_type
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
                    sliver_type=sliver_type,
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
                    component.type = component_type
                if model:
                    component.model = model
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
                    type=component_type,
                    model=model,
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
                                bdf: str, local_name: str, device_name: str, name: str) -> str:
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
                    interface.facility = device_name
                if name:
                    interface.name = name
            else:
                interface = Interfaces(
                    sliver_id=sliver_id,
                    interface_guid=interface_guid,
                    local_name=local_name,
                    device_name=device_name,
                    vlan=vlan,
                    bdf=bdf,
                    name=name
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
    def __build_time_filter(table, start: datetime = None, end: datetime = None):
        lease_end_filter = False

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

    def get_hosts(self, site: str = None):
        session = self.get_session()
        try:
            rows = session.query(Hosts.name, Sites.name.label('site_name')).join(Sites, Hosts.site_id == Sites.id)
            if site:
                rows = rows.filter(Sites.name == site)
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

    def get_projects(self, start_time: datetime = None, end_time: datetime = None, user_email: str = None,
                     sliver_id: str = None,
                     user_id: str = None, project_id: str = None, component_type: str = None, slice_id: str = None,
                     component_model: str = None, sliver_type: str = None, sliver_state: str = None, site: str = None,
                     ip_subnet: str = None, bdf: str = None, vlan: str = None, host: str = None, page: int = 0,
                     per_page: int = 100):
        """
        Retrieve a list of projects filtered by related slices, slivers, users, components, interface attributes, and time range.

        :param start_time: Filter projects with slivers that start on or after this time.
        :type start_time: datetime, optional
        :param end_time: Filter projects with slivers that end on or before this time.
        :type end_time: datetime, optional
        :param user_email: Filter projects by email of the user associated with related slices or slivers.
        :type user_email: str, optional
        :param sliver_id: Filter by specific sliver ID associated with the project.
        :type sliver_id: str, optional
        :param user_id: Filter projects associated with a given user ID.
        :type user_id: str, optional
        :param project_id: Filter by project ID.
        :type project_id: str, optional
        :param component_type: Filter projects where slivers include components of this type.
        :type component_type: str, optional
        :param slice_id: Filter projects containing a specific slice.
        :type slice_id: str, optional
        :param component_model: Filter projects where slivers include components of this model.
        :type component_model: str, optional
        :param sliver_type: Filter projects by the type of slivers they include (e.g., VM, BareMetal).
        :type sliver_type: str, optional
        :param sliver_state: Filter projects by the state of their associated slivers (integer status code).
        :type sliver_state: str, optional
        :param site: Filter projects by site name where their slivers are deployed.
        :type site: str, optional
        :param ip_subnet: Filter projects with slivers using the specified IP subnet.
        :type ip_subnet: str, optional
        :param bdf: Filter projects by PCI BDF (Bus:Device.Function) of associated interfaces or components.
        :type bdf: str, optional
        :param vlan: Filter projects by VLAN associated with sliver interfaces.
        :type vlan: str, optional
        :param host: Filter projects by the host name where slivers are running.
        :type host: str, optional
        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of projects to return per page.
        :type per_page: int, optional

        :return: A list of projects matching the given filters.
        :rtype: List[Project]
        """
        session = self.get_session()
        try:
            rows = session.query(Projects).distinct() \
                .join(Slices, Slices.project_id == Projects.id) \
                .join(Users, Slices.user_id == Users.id) \
                .join(Slivers, Slivers.project_id == Projects.id) \
                .join(Hosts, Slivers.host_id == Hosts.id) \
                .join(Sites, Slivers.site_id == Sites.id) \
                .outerjoin(Components, Slivers.id == Components.sliver_id) \
                .outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time filter
            if start_time or end_time:
                time_filter = self.__build_time_filter(Slivers, start_time, end_time)
                if time_filter:
                    filters.append(time_filter)

            # Project ID
            if project_id:
                filters.append(Projects.project_uuid == project_id)

            # Slice ID
            if slice_id:
                filters.append(Slices.slice_guid == slice_id)

            if sliver_id:
                filters.append(Slivers.sliver_guid == sliver_id)

            # User
            if user_id:
                filters.append(Users.user_uuid == user_id)
            if user_email:
                filters.append(Users.user_email == user_email)

            # Sliver attributes
            if sliver_type:
                filters.append(Slivers.sliver_type == sliver_type)
            if sliver_state:
                filters.append(Slivers.state == int(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet == ip_subnet)

            # Component filters
            if component_type:
                filters.append(Components.type == component_type)
            if component_model:
                filters.append(Components.model == component_model)

            # Interface filters
            if bdf:
                filters.append(Interfaces.bdf == bdf)
            if vlan:
                filters.append(Interfaces.vlan == vlan)

            # Host and Site
            if host:
                filters.append(Hosts.name == host)
            if site:
                filters.append(Sites.name == site)

            # Apply filters
            if filters:
                rows = rows.filter(and_(*filters))

            # Pagination
            rows = rows.offset(page * per_page).limit(per_page)

            return rows.all()

        finally:
            session.rollback()

    def get_users(self, start_time: datetime = None, end_time: datetime = None, user_email: str = None,
                  sliver_id: str = None,
                  user_id: str = None, project_id: str = None, component_type: str = None, slice_id: str = None,
                  component_model: str = None, sliver_type: str = None, sliver_state: str = None, site: str = None,
                  ip_subnet: str = None, bdf: str = None, vlan: str = None, host: str = None, page: int = 0,
                  per_page: int = 100):
        """
        Retrieve a list of users filtered by associated slices, slivers, components, network interfaces, and time range.

        :param start_time: Filter users with slivers that start on or after this time.
        :type start_time: datetime, optional
        :param end_time: Filter users with slivers that end on or before this time.
        :type end_time: datetime, optional
        :param user_email: Filter by user email address.
        :type user_email: str, optional
        :param sliver_id: Filter by specific sliver ID associated with the user.
        :type sliver_id: str, optional
        :param user_id: Filter by user ID.
        :type user_id: str, optional
        :param project_id: Filter users associated with a given project ID.
        :type project_id: str, optional
        :param component_type: Filter users whose slivers include components of this type.
        :type component_type: str, optional
        :param slice_id: Filter users who own a specific slice.
        :type slice_id: str, optional
        :param component_model: Filter users whose slivers include components of this model.
        :type component_model: str, optional
        :param sliver_type: Filter users by the type of their associated slivers (e.g., VM, BareMetal).
        :type sliver_type: str, optional
        :param sliver_state: Filter users by the state of their associated slivers (integer code).
        :type sliver_state: str, optional
        :param site: Filter users based on the site name where their slivers are deployed.
        :type site: str, optional
        :param ip_subnet: Filter users whose slivers use the specified IP subnet.
        :type ip_subnet: str, optional
        :param bdf: Filter users based on the BDF (Bus:Device.Function) of interfaces/components.
        :type bdf: str, optional
        :param vlan: Filter users by VLAN associated with their sliver interfaces.
        :type vlan: str, optional
        :param host: Filter users by host name where their slivers are running.
        :type host: str, optional
        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of users to return per page.
        :type per_page: int, optional

        :return: A list of users matching the given filters.
        :rtype: List[User]
        """

        session = self.get_session()
        try:
            rows = session.query(Users).distinct() \
                .join(Slices, Users.id == Slices.user_id) \
                .join(Slivers, Users.id == Slivers.user_id) \
                .join(Projects, Slivers.project_id == Projects.id) \
                .join(Hosts, Slivers.host_id == Hosts.id) \
                .join(Sites, Slivers.site_id == Sites.id) \
                .outerjoin(Components, Slivers.id == Components.sliver_id) \
                .outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time range filter
            if start_time or end_time:
                time_filter = self.__build_time_filter(Slivers, start_time, end_time)
                if time_filter:
                    filters.append(time_filter)

            # User filters
            if user_email:
                filters.append(Users.user_email == user_email)
            if user_id:
                filters.append(Users.user_uuid == user_id)

            # Project filter
            if project_id:
                filters.append(Projects.project_uuid == project_id)

            # Slice filter
            if slice_id:
                filters.append(Slices.slice_guid == slice_id)

            if sliver_id:
                filters.append(Slivers.sliver_guid == sliver_id)

            # Sliver attributes
            if sliver_type:
                filters.append(Slivers.sliver_type == sliver_type)
            if sliver_state:
                filters.append(Slivers.state == int(sliver_state))
            if ip_subnet:
                filters.append(Slivers.ip_subnet == ip_subnet)

            # Component filters
            if component_type:
                filters.append(Components.type == component_type)
            if component_model:
                filters.append(Components.model == component_model)

            # Interface filters
            if bdf:
                filters.append(Interfaces.bdf == bdf)
            if vlan:
                filters.append(Interfaces.vlan == vlan)

            # Site and host filters
            if site:
                filters.append(Sites.name == site)
            if host:
                filters.append(Hosts.name == host)

            # Apply filters
            if filters:
                rows = rows.filter(and_(*filters))

            # Pagination
            rows = rows.offset(page * per_page).limit(per_page)

            return rows.all()

        finally:
            session.rollback()

    def get_slivers(self, start_time: datetime = None, end_time: datetime = None, user_email: str = None,
                    sliver_id: str = None,
                    user_id: str = None, project_id: str = None, component_type: str = None, slice_id: str = None,
                    component_model: str = None, sliver_type: str = None, sliver_state: str = None, site: str = None,
                    ip_subnet: str = None, bdf: str = None, vlan: str = None, host: str = None, page: int = 0,
                    per_page: int = 100):
        """
        Retrieve a list of slivers filtered by time range, user, project, slice, component, and network-related fields.

        :param start_time: Filter slivers that start on or after this time.
        :type start_time: datetime, optional
        :param end_time: Filter slivers that end on or before this time.
        :type end_time: datetime, optional
        :param user_email: Filter by user email address.
        :type user_email: str, optional
        :param sliver_id: Filter by a specific sliver ID.
        :type sliver_id: str, optional
        :param user_id: Filter by user ID.
        :type user_id: str, optional
        :param project_id: Filter by project ID associated with the sliver.
        :type project_id: str, optional
        :param component_type: Filter by component type (e.g., FPGA, GPU, NIC).
        :type component_type: str, optional
        :param slice_id: Filter by slice ID containing the sliver.
        :type slice_id: str, optional
        :param component_model: Filter by model of the attached component (e.g., Tesla T4, ConnectX-5).
        :type component_model: str, optional
        :param sliver_type: Filter by type of sliver (e.g., VM, BareMetal).
        :type sliver_type: str, optional
        :param sliver_state: Filter by sliver state (status code, usually integer).
        :type sliver_state: str, optional
        :param site: Filter by site name hosting the sliver.
        :type site: str, optional
        :param ip_subnet: Filter by IP subnet assigned to the sliver.
        :type ip_subnet: str, optional
        :param bdf: Filter by PCI BDF (Bus:Device.Function) of a device/interface.
        :type bdf: str, optional
        :param vlan: Filter by VLAN associated with the sliver's interface.
        :type vlan: str, optional
        :param host: Filter by hostname where the sliver is instantiated.
        :type host: str, optional
        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of results per page.
        :type per_page: int, optional

        :return: A list of slivers matching the given filters.
        :rtype: List[Sliver]
        """

        session = self.get_session()
        try:
            rows = session.query(Slivers).distinct() \
                .join(Users, Slivers.user_id == Users.id) \
                .join(Projects, Slivers.project_id == Projects.id) \
                .join(Hosts, Slivers.host_id == Hosts.id) \
                .join(Sites, Slivers.site_id == Sites.id) \
                .outerjoin(Components, Slivers.id == Components.sliver_id) \
                .outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time range filter
            if start_time or end_time:
                time_filter = self.__build_time_filter(Slivers, start_time, end_time)
                if time_filter:
                    filters.append(time_filter)

            # User filters
            if user_email:
                filters.append(Users.user_email == user_email)
            if user_id:
                filters.append(Users.user_uuid == user_id)

            # Project filter
            if project_id:
                filters.append(Projects.project_uuid == project_id)

            # Slice filter
            if slice_id:
                filters.append(Slices.slice_guid == slice_id)

            if sliver_id:
                filters.append(Slivers.sliver_guid == sliver_id)

            # Sliver attributes
            if sliver_type:
                filters.append(Slivers.sliver_type == sliver_type)
            if sliver_state:
                filters.append(Slivers.state == int(sliver_state))  # assuming state is stored as int
            if ip_subnet:
                filters.append(Slivers.ip_subnet == ip_subnet)

            # Component filters
            if component_type:
                filters.append(Components.type == component_type)
            if component_model:
                filters.append(Components.model == component_model)

            # Interface filters
            if bdf:
                filters.append(Interfaces.bdf == bdf)
            if vlan:
                filters.append(Interfaces.vlan == vlan)

            # Host/Site filters
            if site:
                filters.append(Sites.name == site)
            if host:
                filters.append(Hosts.name == host)

            # Apply filters
            if filters:
                rows = rows.filter(and_(*filters))

            # Pagination
            rows = rows.offset(page * per_page).limit(per_page)

            return rows.all()

        finally:
            session.rollback()

    def get_slices(self, start_time: datetime = None, end_time: datetime = None, user_email: str = None, slice_id: str = None,
                   user_id: str = None, project_id: str = None, component_type: str = None, component_model: str = None,
                   sliver_type: str = None, sliver_state: str = None, site: str = None, ip_subnet: str = None, sliver_id: str = None,
                   bdf: str = None, vlan: str = None, host: str = None, page: int = 0, per_page: int = 100):

        """
        Retrieve a list of slices filtered by time, user, project, sliver, component, and network attributes.

        :param start_time: Filter slices with slivers starting after this time.
        :type start_time: datetime, optional
        :param end_time: Filter slices with slivers ending before this time.
        :type end_time: datetime, optional
        :param user_email: Filter by user's email address.
        :type user_email: str, optional
        :param slice_id: Filter by specific slice ID.
        :type slice_id: str, optional
        :param user_id: Filter by user ID.
        :type user_id: str, optional
        :param project_id: Filter by project ID.
        :type project_id: str, optional
        :param component_type: Filter by component type (e.g., GPU, SmartNIC).
        :type component_type: str, optional
        :param component_model: Filter by component model (e.g., ConnectX-6, A30).
        :type component_model: str, optional
        :param sliver_type: Filter by sliver type (e.g., VM, BareMetal).
        :type sliver_type: str, optional
        :param sliver_state: Filter by sliver state (integer-based status code).
        :type sliver_state: str, optional
        :param site: Filter by site name where the sliver is located.
        :type site: str, optional
        :param ip_subnet: Filter slivers by their IP subnet.
        :type ip_subnet: str, optional
        :param sliver_id: Filter by specific sliver ID.
        :type sliver_id: str, optional
        :param bdf: Filter by PCI BDF (Bus:Device.Function) value.
        :type bdf: str, optional
        :param vlan: Filter by VLAN ID associated with an interface.
        :type vlan: str, optional
        :param host: Filter by host name where the sliver is running.
        :type host: str, optional
        :param page: Page number for paginated results (0-based index).
        :type page: int, optional
        :param per_page: Number of results per page.
        :type per_page: int, optional

        :return: A list of slices matching the given filters.
        :rtype: List[Slice]
        """

        session = self.get_session()
        try:
            rows = session.query(Slices).distinct() \
                .join(Users, Slices.user_id == Users.id) \
                .join(Projects, Slices.project_id == Projects.id) \
                .join(Slivers, Slices.id == Slivers.slice_id) \
                .join(Hosts, Slivers.host_id == Hosts.id) \
                .join(Sites, Slivers.site_id == Sites.id) \
                .outerjoin(Components, Slivers.id == Components.sliver_id) \
                .outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

            filters = []

            # Time range filter
            if start_time or end_time:
                time_filter = self.__build_time_filter(Slices, start_time, end_time)
                if time_filter:
                    filters.append(time_filter)

            # User filter
            if user_email:
                filters.append(Users.user_email == user_email)
            if user_id:
                filters.append(Users.user_uuid == user_id)

            # Project filter
            if project_id:
                filters.append(Projects.project_uuid == project_id)

            # Slice filter
            if slice_id:
                filters.append(Slices.slice_guid == slice_id)

            if sliver_id:
                filters.append(Slivers.sliver_guid == sliver_id)

            # Sliver attributes
            if sliver_type:
                filters.append(Slivers.sliver_type == sliver_type)
            if sliver_state:
                filters.append(Slivers.state == int(sliver_state))  # assuming state is stored as int
            if ip_subnet:
                filters.append(Slivers.ip_subnet == ip_subnet)

            # Component filters
            if component_type:
                filters.append(Components.type == component_type)
            if component_model:
                filters.append(Components.model == component_model)

            # Interface filters
            if bdf:
                filters.append(Interfaces.bdf == bdf)
            if vlan:
                filters.append(Interfaces.vlan == vlan)

            # Host/Site filters
            if site:
                filters.append(Sites.name == site)
            if host:
                filters.append(Hosts.name == host)

            # Apply all filters
            if filters:
                rows = rows.filter(and_(*filters))

            # Pagination
            rows = rows.offset(page * per_page).limit(per_page)

            return rows.all()

        finally:
            session.rollback()

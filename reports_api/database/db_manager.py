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
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Union

from sqlalchemy import and_, or_, func, distinct, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from reports_api.database import (
    Slices, Slivers, Hosts, Sites, Users, Projects, Components, Interfaces,
    Membership, HostCapacities, LinkCapacities, FacilityPortCapacities,
)
from reports_api.response_code.slice_sliver_states import SliceState, SliverStates


def _ensure_datetime(value) -> Optional[datetime]:
    """Convert ISO format strings to datetime objects if needed."""
    if value is None:
        return None
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def _parse_vlan_range(range_str: str) -> set:
    """Parse '100-200,300-350' -> {100, 101, ..., 200, 300, ..., 350}"""
    vlans = set()
    if not range_str:
        return vlans
    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            vlans.update(range(int(start), int(end) + 1))
        elif part.isdigit():
            vlans.add(int(part))
    return vlans


def _format_vlan_set_as_range(vlan_set: set) -> str:
    """Format {100,101,102,105,110} -> '100-102,105,110'"""
    if not vlan_set:
        return ""
    sorted_vlans = sorted(vlan_set)
    ranges = []
    start = prev = sorted_vlans[0]
    for v in sorted_vlans[1:]:
        if v == prev + 1:
            prev = v
        else:
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = v
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


_db_manager_instance: "DatabaseManager | None" = None


def get_db_manager() -> "DatabaseManager":
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(logger=logging.getLogger("reports"))
    return _db_manager_instance


def init_db_manager(logger: logging.Logger) -> "DatabaseManager":
    global _db_manager_instance
    _db_manager_instance = DatabaseManager(logger=logger)
    return _db_manager_instance


class DatabaseManager:
    DEFAULT_TIME_WINDOW_DAYS = 30

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    # -------------------- DELETE DATA --------------------
    async def delete_slice(self, session: AsyncSession, slice_id):
        result = await session.execute(select(Slices).where(Slices.id == slice_id))
        slice_object = result.scalars().first()
        if slice_object:
            await session.delete(slice_object)
            return True
        return False

    async def delete_project(self, session: AsyncSession, project_id):
        result = await session.execute(select(Projects).where(Projects.id == project_id))
        project = result.scalars().first()
        if project:
            await session.delete(project)
            return True
        return False

    async def delete_user(self, session: AsyncSession, user_id):
        result = await session.execute(select(Users).where(Users.id == user_id))
        user = result.scalars().first()
        if user:
            await session.delete(user)
            return True
        return False

    # -------------------- ADD OR UPDATE DATA --------------------
    async def add_or_update_project(
            self,
            session: AsyncSession,
            project_uuid: str,
            project_name: Optional[str] = None,
            project_type: Optional[str] = None,
            active: Optional[bool] = None,
            created_date: Optional[datetime] = None,
            expires_on: Optional[datetime] = None,
            retired_date: Optional[datetime] = None,
            last_updated: Optional[datetime] = None,
    ) -> int:
        result = await session.execute(select(Projects).where(Projects.project_uuid == project_uuid))
        project = result.scalars().first()
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

        await session.flush()
        return project.id

    async def add_or_update_user(
            self,
            session: AsyncSession,
            user_uuid: str,
            user_email: Optional[str] = None,
            active: Optional[bool] = None,
            name: Optional[str] = None,
            affiliation: Optional[str] = None,
            registered_on: Optional[datetime] = None,
            last_updated: Optional[datetime] = None,
            google_scholar: Optional[str] = None,
            scopus: Optional[str] = None,
            bastion_login: Optional[str] = None
    ) -> int:
        result = await session.execute(select(Users).where(Users.user_uuid == user_uuid))
        user = result.scalars().first()
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
            if bastion_login is not None:
                user.bastion_login = bastion_login
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
                bastion_login=bastion_login
            )
            session.add(user)

        await session.flush()
        return user.id

    async def add_or_update_membership(self, session: AsyncSession, user_id, project_id,
                                       start_time, end_time, membership_type, active):
        result = await session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.project_id == project_id,
                Membership.start_time == start_time,
                Membership.membership_type == membership_type,
            )
        )
        existing = result.scalars().first()

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

    async def add_or_update_slice(
            self, session: AsyncSession, project_id: int, user_id: int, slice_guid: str,
            slice_name: str, state: int,
            lease_start: Optional[datetime], lease_end: Optional[datetime]
    ) -> int:
        lease_start = _ensure_datetime(lease_start)
        lease_end = _ensure_datetime(lease_end)
        result = await session.execute(select(Slices).where(Slices.slice_guid == slice_guid))
        slice_obj = result.scalars().first()
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

        await session.flush()
        return slice_obj.id

    async def add_or_update_sliver(
        self,
        session: AsyncSession,
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
        ip_v4: Optional[str] = None,
        ip_v6: Optional[str] = None,
        image: Optional[str] = None,
        core: Optional[int] = None,
        ram: Optional[int] = None,
        disk: Optional[int] = None,
        bandwidth: Optional[int] = None,
        lease_start: Optional[datetime] = None,
        lease_end: Optional[datetime] = None,
        closed_at: Optional[datetime] = None,
        error: Optional[str] = None
    ) -> int:
        lease_start = _ensure_datetime(lease_start)
        lease_end = _ensure_datetime(lease_end)
        closed_at = _ensure_datetime(closed_at)
        result = await session.execute(select(Slivers).where(Slivers.sliver_guid == sliver_guid))
        sliver = result.scalars().first()

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
            if ip_v4:
                sliver.ip_v4 = ip_v4
            if ip_v6:
                sliver.ip_v6 = ip_v6
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
            if closed_at:
                sliver.closed_at = closed_at
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
                ip_v4=ip_v4,
                ip_v6=ip_v6,
                image=image,
                core=core,
                ram=ram,
                disk=disk,
                bandwidth=bandwidth,
                lease_start=lease_start,
                lease_end=lease_end,
                closed_at=closed_at,
                error=error
            )
            session.add(sliver)

        await session.flush()
        return sliver.id

    async def add_or_update_component(
        self, session: AsyncSession, sliver_id: int, component_guid: str,
        component_type: str, model: str, bdfs: List[str], node_id: str,
        component_node_id: str
    ) -> str:
        result = await session.execute(
            select(Components).where(
                Components.component_guid == component_guid,
                Components.sliver_id == sliver_id,
            )
        )
        component = result.scalars().first()

        if component:
            if component_type:
                component.type = component_type.lower()
            if model:
                component.model = model.lower()
            if bdfs:
                component.bdfs = bdfs
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

        await session.flush()
        return component.component_guid

    async def add_or_update_interface(
        self, session: AsyncSession, sliver_id: int, interface_guid: str, vlan: str,
        bdf: str, local_name: str, device_name: str, name: str, site_id: int
    ) -> str:
        result = await session.execute(
            select(Interfaces).where(
                Interfaces.interface_guid == interface_guid,
                Interfaces.sliver_id == sliver_id,
            )
        )
        interface = result.scalars().first()

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

        await session.flush()
        return interface.interface_guid

    async def add_or_update_host(self, session: AsyncSession, host_name: str, site_id: int) -> int:
        result = await session.execute(select(Hosts).where(Hosts.name == host_name))
        host = result.scalars().first()
        if not host:
            host = Hosts(name=host_name, site_id=site_id)
            session.add(host)
            await session.flush()
        return host.id

    async def add_or_update_site(self, session: AsyncSession, site_name: str) -> int:
        result = await session.execute(select(Sites).where(Sites.name == site_name))
        site = result.scalars().first()
        if not site:
            site = Sites(name=site_name)
            session.add(site)
            await session.flush()
        return site.id

    async def add_or_update_host_capacity(
        self, session: AsyncSession, host_name: str, site_name: str,
        cores: int = 0, ram: int = 0, disk: int = 0,
        components: Optional[dict] = None
    ) -> int:
        site_id = await self.add_or_update_site(session, site_name)
        host_id = await self.add_or_update_host(session, host_name, site_id)

        result = await session.execute(
            select(HostCapacities).where(HostCapacities.host_id == host_id)
        )
        capacity = result.scalars().first()
        if capacity:
            capacity.site_id = site_id
            capacity.cores_capacity = cores
            capacity.ram_capacity = ram
            capacity.disk_capacity = disk
            capacity.components = components
        else:
            capacity = HostCapacities(
                host_id=host_id,
                site_id=site_id,
                cores_capacity=cores,
                ram_capacity=ram,
                disk_capacity=disk,
                components=components
            )
            session.add(capacity)

        await session.flush()
        return capacity.id

    async def add_or_update_link_capacity(
        self, session: AsyncSession, link_name: str, site_a_name: str,
        site_b_name: str, layer: str, bandwidth: int = 0
    ) -> int:
        if site_a_name > site_b_name:
            site_a_name, site_b_name = site_b_name, site_a_name

        site_a_id = await self.add_or_update_site(session, site_a_name)
        site_b_id = await self.add_or_update_site(session, site_b_name)

        result = await session.execute(
            select(LinkCapacities).where(LinkCapacities.name == link_name)
        )
        capacity = result.scalars().first()
        if capacity:
            capacity.site_a_id = site_a_id
            capacity.site_b_id = site_b_id
            capacity.layer = layer
            capacity.bandwidth_capacity = bandwidth
        else:
            capacity = LinkCapacities(
                name=link_name,
                site_a_id=site_a_id,
                site_b_id=site_b_id,
                layer=layer,
                bandwidth_capacity=bandwidth
            )
            session.add(capacity)

        await session.flush()
        return capacity.id

    async def add_or_update_facility_port_capacity(
        self, session: AsyncSession, port_name: str, site_name: str,
        device_name: str = "", local_name: str = "",
        vlan_range: Optional[str] = None, total_vlans: int = 0
    ) -> int:
        site_id = await self.add_or_update_site(session, site_name)

        result = await session.execute(
            select(FacilityPortCapacities).where(
                FacilityPortCapacities.name == port_name,
                FacilityPortCapacities.site_id == site_id,
                FacilityPortCapacities.device_name == device_name,
                FacilityPortCapacities.local_name == local_name,
            )
        )
        capacity = result.scalars().first()
        if capacity:
            capacity.device_name = device_name
            capacity.local_name = local_name
            capacity.vlan_range = vlan_range
            capacity.total_vlans = total_vlans
        else:
            capacity = FacilityPortCapacities(
                name=port_name,
                site_id=site_id,
                device_name=device_name,
                local_name=local_name,
                vlan_range=vlan_range,
                total_vlans=total_vlans
            )
            session.add(capacity)

        await session.flush()
        return capacity.id

    # -------------------- SHARED CALENDAR QUERY HELPERS --------------------
    @staticmethod
    async def _query_host_capacities(session: AsyncSession, site=None, host=None,
                                     exclude_site=None, exclude_host=None):
        stmt = (
            select(HostCapacities, Hosts.name.label("host_name"), Sites.name.label("site_name"))
            .join(Hosts, HostCapacities.host_id == Hosts.id)
            .join(Sites, HostCapacities.site_id == Sites.id)
        )

        if site:
            stmt = stmt.where(Sites.name.in_(site))
        if host:
            stmt = stmt.where(Hosts.name.in_(host))
        if exclude_site:
            stmt = stmt.where(not_(Sites.name.in_(exclude_site)))
        if exclude_host:
            stmt = stmt.where(not_(Hosts.name.in_(exclude_host)))

        result = await session.execute(stmt)
        capacities = result.all()

        host_cap_map = {}
        for cap, h_name, s_name in capacities:
            host_cap_map[cap.host_id] = {
                "name": h_name, "site": s_name,
                "cores_capacity": cap.cores_capacity or 0,
                "ram_capacity": cap.ram_capacity or 0,
                "disk_capacity": cap.disk_capacity or 0,
                "components": cap.components or {}
            }
        return capacities, host_cap_map

    @staticmethod
    async def _query_link_capacities(session: AsyncSession, site=None, exclude_site=None):
        site_a_alias = Sites.__table__.alias("site_a")
        site_b_alias = Sites.__table__.alias("site_b")
        stmt = (
            select(LinkCapacities,
                   site_a_alias.c.name.label("site_a_name"),
                   site_b_alias.c.name.label("site_b_name"))
            .join(site_a_alias, LinkCapacities.site_a_id == site_a_alias.c.id)
            .join(site_b_alias, LinkCapacities.site_b_id == site_b_alias.c.id)
        )

        if site:
            stmt = stmt.where(or_(
                site_a_alias.c.name.in_(site),
                site_b_alias.c.name.in_(site)
            ))
        if exclude_site:
            stmt = stmt.where(
                not_(site_a_alias.c.name.in_(exclude_site)),
                not_(site_b_alias.c.name.in_(exclude_site))
            )

        result = await session.execute(stmt)
        link_capacities = result.all()

        link_cap_map = {}
        for lc, sa_name, sb_name in link_capacities:
            pair = tuple(sorted([sa_name, sb_name]))
            link_cap_map[pair] = {
                "name": lc.name,
                "site_a": pair[0],
                "site_b": pair[1],
                "layer": lc.layer,
                "bandwidth_capacity": lc.bandwidth_capacity or 0
            }
        return link_capacities, link_cap_map

    @staticmethod
    async def _query_fp_capacities(session: AsyncSession, site=None, exclude_site=None):
        stmt = (
            select(FacilityPortCapacities, Sites.name.label("site_name"))
            .join(Sites, FacilityPortCapacities.site_id == Sites.id)
        )

        if site:
            stmt = stmt.where(Sites.name.in_(site))
        if exclude_site:
            stmt = stmt.where(not_(Sites.name.in_(exclude_site)))

        result = await session.execute(stmt)
        fp_capacities = result.all()

        fp_cap_map = {}
        for fp, s_name in fp_capacities:
            key = (fp.name, s_name, fp.device_name, fp.local_name)
            fp_cap_map[key] = {
                "name": fp.name,
                "site": s_name,
                "device_name": fp.device_name,
                "local_name": fp.local_name,
                "vlan_range": fp.vlan_range or "",
                "total_vlans": fp.total_vlans or 0
            }
        return fp_capacities, fp_cap_map

    @staticmethod
    async def _query_compute_slivers(session: AsyncSession, host_ids, start_time, end_time):
        active_states = [1, 2, 4, 5]
        slivers_in_range = []
        if host_ids:
            stmt = (
                select(Slivers.id, Slivers.host_id, Slivers.core, Slivers.ram, Slivers.disk,
                       Slivers.lease_start, Slivers.lease_end)
                .where(
                    Slivers.host_id.in_(host_ids),
                    Slivers.state.in_(active_states),
                    Slivers.lease_start < end_time,
                    Slivers.lease_end > start_time
                )
            )
            result = await session.execute(stmt)
            slivers_in_range = result.all()

        sliver_ids = [s.id for s in slivers_in_range]
        comp_rows = []
        if sliver_ids:
            stmt = (
                select(Components.sliver_id, Components.type, Components.model, Components.component_guid)
                .where(Components.sliver_id.in_(sliver_ids))
            )
            result = await session.execute(stmt)
            comp_rows = result.all()

        comp_by_sliver = defaultdict(list)
        for cr in comp_rows:
            key = f"{cr.type}-{cr.model}" if cr.model else cr.type
            comp_by_sliver[cr.sliver_id].append((key, cr.component_guid))

        return slivers_in_range, comp_by_sliver

    @staticmethod
    async def _query_network_slivers(session: AsyncSession, link_cap_map, start_time, end_time):
        active_states = [1, 2, 4, 5]
        net_slivers_in_range = []
        net_sliver_interfaces = defaultdict(list)
        if link_cap_map:
            cross_site_types = ['l2ptp', 'l2sts']
            stmt = (
                select(Slivers.id, Slivers.bandwidth, Slivers.lease_start, Slivers.lease_end)
                .where(
                    Slivers.sliver_type.in_(cross_site_types),
                    Slivers.state.in_(active_states),
                    Slivers.lease_start < end_time,
                    Slivers.lease_end > start_time
                )
            )
            result = await session.execute(stmt)
            net_slivers_in_range = result.all()

            net_sliver_ids = [s.id for s in net_slivers_in_range]
            if net_sliver_ids:
                stmt = (
                    select(Interfaces.sliver_id, Sites.name.label("site_name"))
                    .join(Sites, Interfaces.site_id == Sites.id)
                    .where(
                        Interfaces.sliver_id.in_(net_sliver_ids),
                        Interfaces.site_id.isnot(None)
                    )
                )
                result = await session.execute(stmt)
                iface_rows = result.all()

                for row in iface_rows:
                    net_sliver_interfaces[row.sliver_id].append(row.site_name)

        return net_slivers_in_range, net_sliver_interfaces

    @staticmethod
    async def _query_fp_slivers(session: AsyncSession, fp_cap_map, start_time, end_time):
        active_states = [1, 2, 4, 5]
        fp_iface_slivers = []
        if fp_cap_map:
            fp_names = list(set(k[0] for k in fp_cap_map.keys()))
            stmt = (
                select(Interfaces.name.label("fp_name"),
                       Sites.name.label("site_name"),
                       Interfaces.vlan,
                       Slivers.lease_start,
                       Slivers.lease_end)
                .join(Slivers, Interfaces.sliver_id == Slivers.id)
                .join(Sites, Interfaces.site_id == Sites.id)
                .where(
                    Interfaces.name.in_(fp_names),
                    Interfaces.site_id.isnot(None),
                    Slivers.state.in_(active_states),
                    Slivers.lease_start < end_time,
                    Slivers.lease_end > start_time
                )
            )
            result = await session.execute(stmt)
            fp_iface_slivers = result.all()
        return fp_iface_slivers

    # -------------------- CALENDAR QUERY --------------------
    async def get_calendar(self, session: AsyncSession, start_time: datetime, end_time: datetime,
                           interval: str = "day",
                           site: Optional[List[str]] = None, host: Optional[List[str]] = None,
                           exclude_site: Optional[List[str]] = None,
                           exclude_host: Optional[List[str]] = None) -> dict:
        capacities, host_cap_map = await self._query_host_capacities(
            session, site=site, host=host, exclude_site=exclude_site, exclude_host=exclude_host)
        host_ids = list(host_cap_map.keys())

        link_capacities, link_cap_map = await self._query_link_capacities(
            session, site=site, exclude_site=exclude_site)

        fp_capacities, fp_cap_map = await self._query_fp_capacities(
            session, site=site, exclude_site=exclude_site)

        if not capacities and not link_capacities and not fp_capacities:
            return {"data": [], "interval": interval,
                    "query_start": start_time.isoformat(), "query_end": end_time.isoformat(), "total": 0}

        if interval == "week":
            delta = timedelta(weeks=1)
        elif interval == "hour":
            delta = timedelta(hours=1)
        else:
            delta = timedelta(days=1)

        slots = []
        slot_start = start_time
        while slot_start < end_time:
            slot_end = min(slot_start + delta, end_time)
            slots.append((slot_start, slot_end))
            slot_start = slot_end

        slivers_in_range, comp_by_sliver = await self._query_compute_slivers(
            session, host_ids, start_time, end_time)

        net_slivers_in_range, net_sliver_interfaces = await self._query_network_slivers(
            session, link_cap_map, start_time, end_time)

        fp_iface_slivers = await self._query_fp_slivers(session, fp_cap_map, start_time, end_time)

        result_data = []
        for slot_start, slot_end in slots:
            alloc_map = defaultdict(lambda: {"cores": 0, "ram": 0, "disk": 0})
            comp_alloc_map = defaultdict(lambda: defaultdict(int))

            for sliver in slivers_in_range:
                if sliver.lease_start < slot_end and sliver.lease_end > slot_start:
                    h = sliver.host_id
                    alloc_map[h]["cores"] += sliver.core or 0
                    alloc_map[h]["ram"] += sliver.ram or 0
                    alloc_map[h]["disk"] += sliver.disk or 0
                    for comp_key, _ in comp_by_sliver.get(sliver.id, []):
                        comp_alloc_map[h][comp_key] += 1

            hosts_result = []
            site_agg = {}
            for host_id, cap in host_cap_map.items():
                alloc = alloc_map.get(host_id, {"cores": 0, "ram": 0, "disk": 0})
                comp_alloc = comp_alloc_map.get(host_id, {})

                comp_result = {}
                comp_alloc_lower = {k.lower(): v for k, v in comp_alloc.items()}
                for comp_key, comp_cap in cap["components"].items():
                    comp_allocated = comp_alloc_lower.get(comp_key.lower(), 0)
                    comp_result[comp_key] = {
                        "capacity": comp_cap,
                        "allocated": comp_allocated,
                        "available": comp_cap - comp_allocated
                    }

                host_entry = {
                    "name": cap["name"], "site": cap["site"],
                    "cores_capacity": cap["cores_capacity"],
                    "cores_allocated": alloc["cores"],
                    "cores_available": cap["cores_capacity"] - alloc["cores"],
                    "ram_capacity": cap["ram_capacity"],
                    "ram_allocated": alloc["ram"],
                    "ram_available": cap["ram_capacity"] - alloc["ram"],
                    "disk_capacity": cap["disk_capacity"],
                    "disk_allocated": alloc["disk"],
                    "disk_available": cap["disk_capacity"] - alloc["disk"],
                    "components": comp_result
                }
                hosts_result.append(host_entry)

                s = cap["site"]
                if s not in site_agg:
                    site_agg[s] = {"name": s,
                                   "cores_capacity": 0, "cores_allocated": 0, "cores_available": 0,
                                   "ram_capacity": 0, "ram_allocated": 0, "ram_available": 0,
                                   "disk_capacity": 0, "disk_allocated": 0, "disk_available": 0,
                                   "components": {}}
                for field in ["cores", "ram", "disk"]:
                    site_agg[s][f"{field}_capacity"] += host_entry[f"{field}_capacity"]
                    site_agg[s][f"{field}_allocated"] += host_entry[f"{field}_allocated"]
                    site_agg[s][f"{field}_available"] += host_entry[f"{field}_available"]
                for comp_key, comp_data in comp_result.items():
                    if comp_key not in site_agg[s]["components"]:
                        site_agg[s]["components"][comp_key] = {"capacity": 0, "allocated": 0, "available": 0}
                    for k in ["capacity", "allocated", "available"]:
                        site_agg[s]["components"][comp_key][k] += comp_data[k]

            links_result = []
            if link_cap_map:
                link_bw_alloc = defaultdict(int)
                for ns in net_slivers_in_range:
                    if ns.lease_start < slot_end and ns.lease_end > slot_start:
                        sites_list = net_sliver_interfaces.get(ns.id, [])
                        unique_sites = sorted(set(sites_list))
                        if len(unique_sites) == 2:
                            pair = tuple(unique_sites)
                            link_bw_alloc[pair] += ns.bandwidth or 0

                for pair, cap in link_cap_map.items():
                    allocated = link_bw_alloc.get(pair, 0)
                    links_result.append({
                        "name": cap["name"],
                        "site_a": cap["site_a"],
                        "site_b": cap["site_b"],
                        "layer": cap["layer"],
                        "bandwidth_capacity": cap["bandwidth_capacity"],
                        "bandwidth_allocated": allocated,
                        "bandwidth_available": cap["bandwidth_capacity"] - allocated
                    })

            fp_result = []
            if fp_cap_map:
                fp_vlan_alloc = defaultdict(set)
                for fp_iface in fp_iface_slivers:
                    if fp_iface.lease_start < slot_end and fp_iface.lease_end > slot_start:
                        key = (fp_iface.fp_name, fp_iface.site_name)
                        if fp_iface.vlan:
                            fp_vlan_alloc[key].add(fp_iface.vlan)

                for (fp_name, s_name, dev_name, loc_name), cap in fp_cap_map.items():
                    allocated_vlans = {int(v) for v in fp_vlan_alloc.get((fp_name, s_name), set()) if v}
                    capacity_set = _parse_vlan_range(cap["vlan_range"])
                    available_set = capacity_set - allocated_vlans
                    fp_result.append({
                        "name": cap["name"],
                        "site": cap["site"],
                        "device_name": cap["device_name"],
                        "local_name": cap["local_name"],
                        "vlan_range": cap["vlan_range"],
                        "total_vlans": cap["total_vlans"],
                        "vlans_allocated": sorted([str(v) for v in allocated_vlans]),
                        "vlans_available": _format_vlan_set_as_range(available_set)
                    })

            slot_entry = {
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
                "hosts": hosts_result,
                "sites": list(site_agg.values())
            }
            if links_result:
                slot_entry["links"] = links_result
            if fp_result:
                slot_entry["facility_ports"] = fp_result

            result_data.append(slot_entry)

        return {
            "data": result_data,
            "interval": interval,
            "query_start": start_time.isoformat(),
            "query_end": end_time.isoformat(),
            "total": len(result_data)
        }

    # -------------------- FIND SLOT QUERY --------------------
    async def find_slot(self, session: AsyncSession, start_time: datetime, end_time: datetime,
                        duration: int, resources: List[dict],
                        max_results: int = 1) -> dict:
        compute_sites = set()
        for r in resources:
            if r.get("type") == "compute" and r.get("site"):
                compute_sites.add(r["site"])

        link_sites = set()
        for r in resources:
            if r.get("type") == "link":
                link_sites.add(r["site_a"])
                link_sites.add(r["site_b"])

        fp_sites = set()
        for r in resources:
            if r.get("type") == "facility_port" and r.get("site"):
                fp_sites.add(r["site"])

        compute_requests = [r for r in resources if r.get("type") == "compute"]
        has_siteless_compute = any(not r.get("site") for r in compute_requests)
        host_site_filter = list(compute_sites) if compute_sites and not has_siteless_compute else None

        capacities, host_cap_map = await self._query_host_capacities(session, site=host_site_filter)
        host_ids = list(host_cap_map.keys())

        link_requests = [r for r in resources if r.get("type") == "link"]
        link_capacities, link_cap_map = (
            await self._query_link_capacities(session) if link_requests else ([], {}))

        fp_requests = [r for r in resources if r.get("type") == "facility_port"]
        fp_capacities, fp_cap_map = (
            await self._query_fp_capacities(session) if fp_requests else ([], {}))

        if compute_requests and not host_cap_map:
            return self._empty_find_slot_result(start_time, end_time, duration)
        if link_requests and not link_cap_map:
            return self._empty_find_slot_result(start_time, end_time, duration)
        if fp_requests and not fp_cap_map:
            return self._empty_find_slot_result(start_time, end_time, duration)

        slivers_in_range, comp_by_sliver = await self._query_compute_slivers(
            session, host_ids, start_time, end_time)

        net_slivers_in_range, net_sliver_interfaces = await self._query_network_slivers(
            session, link_cap_map, start_time, end_time)

        fp_iface_slivers = await self._query_fp_slivers(session, fp_cap_map, start_time, end_time)

        hosts_by_site = defaultdict(list)
        for host_id, cap in host_cap_map.items():
            hosts_by_site[cap["site"]].append(host_id)

        total_hours = int((end_time - start_time).total_seconds() // 3600)
        if total_hours < duration:
            return self._empty_find_slot_result(start_time, end_time, duration)

        windows = []
        for h in range(total_hours - duration + 1):
            window_start = start_time + timedelta(hours=h)
            window_end = window_start + timedelta(hours=duration)

            if self._check_window(
                window_start, window_end, duration,
                compute_requests, link_requests, fp_requests,
                host_cap_map, hosts_by_site, slivers_in_range, comp_by_sliver,
                link_cap_map, net_slivers_in_range, net_sliver_interfaces,
                fp_cap_map, fp_iface_slivers
            ):
                windows.append({
                    "start": window_start.isoformat(),
                    "end": window_end.isoformat()
                })
                if len(windows) >= max_results:
                    break

        return {
            "windows": windows,
            "total": len(windows),
            "search_start": start_time.isoformat(),
            "search_end": end_time.isoformat(),
            "duration_hours": duration
        }

    @staticmethod
    def _empty_find_slot_result(start_time, end_time, duration):
        return {
            "windows": [],
            "total": 0,
            "search_start": start_time.isoformat(),
            "search_end": end_time.isoformat(),
            "duration_hours": duration
        }

    @staticmethod
    def _check_window(window_start, window_end, duration,
                      compute_requests, link_requests, fp_requests,
                      host_cap_map, hosts_by_site, slivers_in_range, comp_by_sliver,
                      link_cap_map, net_slivers_in_range, net_sliver_interfaces,
                      fp_cap_map, fp_iface_slivers):
        if compute_requests:
            for dh in range(duration):
                hour_start = window_start + timedelta(hours=dh)
                hour_end = hour_start + timedelta(hours=1)

                remaining = {}
                for host_id, cap in host_cap_map.items():
                    remaining[host_id] = {
                        "cores": cap["cores_capacity"],
                        "ram": cap["ram_capacity"],
                        "disk": cap["disk_capacity"],
                        "components": {k.lower(): v for k, v in cap["components"].items()}
                    }

                for sliver in slivers_in_range:
                    if sliver.lease_start < hour_end and sliver.lease_end > hour_start:
                        h = sliver.host_id
                        if h in remaining:
                            remaining[h]["cores"] -= sliver.core or 0
                            remaining[h]["ram"] -= sliver.ram or 0
                            remaining[h]["disk"] -= sliver.disk or 0
                            for comp_key, _ in comp_by_sliver.get(sliver.id, []):
                                comp_key_lower = comp_key.lower()
                                if comp_key_lower in remaining[h]["components"]:
                                    remaining[h]["components"][comp_key_lower] -= 1

                for req in compute_requests:
                    req_cores = req.get("cores", 0)
                    req_ram = req.get("ram", 0)
                    req_disk = req.get("disk", 0)
                    req_components = req.get("components", {})
                    req_site = req.get("site")

                    if req_site:
                        candidate_hosts = [hid for hid in hosts_by_site.get(req_site, [])
                                           if hid in remaining]
                    else:
                        candidate_hosts = list(remaining.keys())

                    placed = False
                    for host_id in candidate_hosts:
                        rem = remaining[host_id]
                        if rem["cores"] < req_cores:
                            continue
                        if rem["ram"] < req_ram:
                            continue
                        if rem["disk"] < req_disk:
                            continue

                        comp_ok = True
                        for comp_key, comp_count in req_components.items():
                            if rem["components"].get(comp_key.lower(), 0) < comp_count:
                                comp_ok = False
                                break
                        if not comp_ok:
                            continue

                        rem["cores"] -= req_cores
                        rem["ram"] -= req_ram
                        rem["disk"] -= req_disk
                        for comp_key, comp_count in req_components.items():
                            rem["components"][comp_key.lower()] -= comp_count
                        placed = True
                        break

                    if not placed:
                        return False

        for req in link_requests:
            pair = tuple(sorted([req["site_a"], req["site_b"]]))
            cap_entry = link_cap_map.get(pair)
            if not cap_entry:
                return False
            bw_cap = cap_entry["bandwidth_capacity"]
            req_bw = req["bandwidth"]

            for dh in range(duration):
                hour_start = window_start + timedelta(hours=dh)
                hour_end = hour_start + timedelta(hours=1)

                bw_used = 0
                for ns in net_slivers_in_range:
                    if ns.lease_start < hour_end and ns.lease_end > hour_start:
                        sites_list = net_sliver_interfaces.get(ns.id, [])
                        unique_sites = sorted(set(sites_list))
                        if len(unique_sites) == 2 and tuple(unique_sites) == pair:
                            bw_used += ns.bandwidth or 0

                if bw_cap - bw_used < req_bw:
                    return False

        for req in fp_requests:
            req_name = req["name"]
            req_site = req["site"]
            req_vlans = req["vlans"]

            matching_fp = None
            for (fp_name, s_name, dev_name, loc_name), cap in fp_cap_map.items():
                if fp_name == req_name and s_name == req_site:
                    matching_fp = cap
                    break
            if not matching_fp:
                return False

            total_vlans = matching_fp["total_vlans"]

            for dh in range(duration):
                hour_start = window_start + timedelta(hours=dh)
                hour_end = hour_start + timedelta(hours=1)

                vlans_in_use = set()
                for fp_iface in fp_iface_slivers:
                    if (fp_iface.fp_name == req_name and fp_iface.site_name == req_site and
                            fp_iface.lease_start < hour_end and fp_iface.lease_end > hour_start):
                        if fp_iface.vlan:
                            vlans_in_use.add(fp_iface.vlan)

                if total_vlans - len(vlans_in_use) < req_vlans:
                    return False

        return True

    # -------------------- QUERY DATA --------------------
    @staticmethod
    def __build_time_filter(table: Union[Slices, Slivers], start: datetime = None, end: datetime = None):
        if start is not None or end is not None:
            if start is not None and end is not None:
                lease_end_filter = or_(
                    and_(start <= table.lease_end, table.lease_end <= end),
                    and_(start <= table.lease_start, table.lease_start <= end),
                    and_(table.lease_start <= start, table.lease_end >= end)
                )
            elif start is not None:
                lease_end_filter = start <= table.lease_end
            else:
                lease_end_filter = table.lease_end <= end
            return lease_end_filter
        return None

    async def get_sites(self, session: AsyncSession):
        result = await session.execute(select(Sites))
        sites = result.scalars().all()
        return [{'name': site.name} for site in sites]

    async def get_hosts(self, session: AsyncSession, site: list[str] = None,
                        exclude_site: list[str] = None):
        stmt = (
            select(Hosts.name, Sites.name.label('site_name'))
            .join(Sites, Hosts.site_id == Sites.id)
        )
        if site:
            stmt = stmt.where(Sites.name.in_(site))
        if exclude_site:
            stmt = stmt.where(Sites.name.notin_(exclude_site))

        result = await session.execute(stmt)
        rows = result.all()

        site_map = defaultdict(list)
        for host_name, site_name in rows:
            site_map[site_name].append({'name': host_name})

        return [
            {'name': site_name, 'hosts': host_list}
            for site_name, host_list in site_map.items()
        ]

    async def get_projects(self, session: AsyncSession, start_time: datetime = None,
                           end_time: datetime = None, user_email: list[str] = None,
                           user_id: list[str] = None, project_id: list[str] = None,
                           component_type: list[str] = None,
                           slice_id: list[str] = None, slice_state: list[int] = None,
                           component_model: list[str] = None,
                           sliver_type: list[str] = None, sliver_id: list[str] = None,
                           sliver_state: list[int] = None,
                           site: list[str] = None, ip_subnet: list[str] = None,
                           bdf: list[str] = None,
                           ip_v4: list[str] = None, ip_v6: list[str] = None,
                           vlan: list[str] = None, host: list[str] = None,
                           exclude_user_id: list[str] = None,
                           exclude_user_email: list[str] = None,
                           exclude_project_id: list[str] = None,
                           exclude_site: list[str] = None, exclude_host: list[str] = None,
                           facility: list[str] = None,
                           exclude_slice_state: list[int] = None,
                           exclude_sliver_state: list[int] = None,
                           project_type: list[str] = None,
                           exclude_project_type: list[str] = None,
                           project_active: bool = None,
                           page: int = 0, per_page: int = 100) -> dict:
        requires_slice = any([
            slice_id, slice_state, user_email, user_id,
            exclude_user_id, exclude_user_email, exclude_slice_state
        ])
        requires_sliver = any([
            sliver_id, sliver_type, sliver_state, ip_subnet, ip_v4, ip_v6,
            host, site, component_type, component_model, bdf, vlan, facility,
            exclude_site, exclude_host, exclude_sliver_state
        ])

        if requires_sliver:
            now = datetime.utcnow()
            if not start_time and not end_time:
                end_time = now
                start_time = now - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
            elif start_time and not end_time:
                end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
            elif end_time and not start_time:
                start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)

        start_ts = time.time()

        query = select(Projects).distinct()

        if requires_slice or requires_sliver:
            query = query.join(Slices, Slices.project_id == Projects.id)\
                .join(Users, Slices.user_id == Users.id)

        filters = []

        if requires_sliver:
            query = query.join(Slivers, Slivers.project_id == Projects.id)
            if host or site or exclude_host or exclude_site:
                query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                             .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

        if start_time or end_time:
            if requires_slice or requires_sliver:
                time_filter = self.__build_time_filter(Slices, start_time, end_time)
                if time_filter is not None:
                    filters.append(time_filter)
            else:
                if start_time and end_time:
                    filters.append(or_(
                        and_(Projects.created_date.isnot(None), Projects.created_date.between(start_time, end_time)),
                        and_(Projects.expires_on.isnot(None), Projects.expires_on.between(start_time, end_time))
                    ))
                elif start_time:
                    filters.append(or_(
                        and_(Projects.created_date.isnot(None), Projects.created_date >= start_time),
                        and_(Projects.expires_on.isnot(None), Projects.expires_on >= start_time)
                    ))
                elif end_time:
                    filters.append(or_(
                        and_(Projects.created_date.isnot(None), Projects.created_date <= end_time),
                        and_(Projects.expires_on.isnot(None), Projects.expires_on <= end_time)
                    ))

        if project_id:
            filters.append(Projects.project_uuid.in_(project_id))
        if project_active is not None:
            filters.append(Projects.active == project_active)
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
        if ip_v4:
            filters.append(Slivers.ip_v4.in_(ip_v4))
        if ip_v6:
            filters.append(Slivers.ip_v6.in_(ip_v6))
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
            query = query.where(and_(*filters))

        self.logger.info(f"Query Projects (building query) = {time.time() - start_ts:.2f}s")
        query_ts = time.time()

        # Count query
        count_stmt = select(func.count(distinct(Projects.id)))
        if requires_slice or requires_sliver:
            count_stmt = count_stmt.join(Slices, Slices.project_id == Projects.id)\
                .join(Users, Slices.user_id == Users.id)
        if requires_sliver:
            count_stmt = count_stmt.join(Slivers, Slivers.project_id == Projects.id)
            if host or site or exclude_host or exclude_site:
                count_stmt = count_stmt.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                       .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                count_stmt = count_stmt.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                count_stmt = count_stmt.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))

        count_result = await session.execute(count_stmt)
        total_projects = count_result.scalar()

        self.logger.info(f"Query Projects (count) = {time.time() - query_ts:.2f}s")
        fetch_ts = time.time()

        paginated = query.offset(page * per_page).limit(per_page)
        result = await session.execute(paginated)
        projects = result.scalars().all()

        self.logger.info(f"Query Projects (fetch rows) = {time.time() - fetch_ts:.2f}s")
        parse_ts = time.time()

        result_list = []
        for p in projects:
            project_dict = self.project_to_dict(p)

            if project_id:
                users = await self.get_users(
                    session=session, start_time=start_time, end_time=end_time,
                    user_email=user_email, user_id=user_id, vlan=vlan, facility=facility,
                    sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                    sliver_state=sliver_state, site=site, host=host,
                    project_id=project_id, component_model=component_model,
                    component_type=component_type, ip_subnet=ip_subnet, ip_v4=ip_v4,
                    ip_v6=ip_v6, page=page, per_page=per_page,
                    exclude_site=exclude_site, exclude_host=exclude_host,
                    exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                    exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                    exclude_user_email=exclude_user_email)
                project_dict["users"] = {
                    "total": users.get("total"),
                    "data": users.get("users")
                }
            else:
                user_count = await self.__get_user_count_for_project(session, p.id)
                project_dict["users"] = {"total": user_count}

            result_list.append(project_dict)

        self.logger.info(f"Query Projects (dict building) = {time.time() - parse_ts:.2f}s")

        return {
            "total": total_projects,
            "projects": result_list
        }

    async def get_users(self, session: AsyncSession, start_time: datetime = None,
                        end_time: datetime = None, user_email: list[str] = None,
                        user_id: list[str] = None, project_id: list[str] = None,
                        component_type: list[str] = None,
                        slice_id: list[str] = None, slice_state: list[int] = None,
                        component_model: list[str] = None,
                        sliver_type: list[str] = None, sliver_id: list[str] = None,
                        sliver_state: list[int] = None,
                        site: list[str] = None, ip_subnet: list[str] = None,
                        bdf: list[str] = None,
                        ip_v4: list[str] = None, ip_v6: list[str] = None,
                        vlan: list[str] = None, host: list[str] = None,
                        exclude_user_id: list[str] = None,
                        exclude_user_email: list[str] = None,
                        exclude_project_id: list[str] = None,
                        exclude_site: list[str] = None, exclude_host: list[str] = None,
                        facility: list[str] = None,
                        exclude_slice_state: list[int] = None,
                        exclude_sliver_state: list[int] = None,
                        project_type: list[str] = None,
                        exclude_project_type: list[str] = None,
                        user_active: bool = None,
                        page: int = 0, per_page: int = 100) -> dict:
        start_ts = time.time()

        requires_slice = any([
            slice_id, slice_state, user_email, user_id,
            exclude_user_id, exclude_user_email, exclude_slice_state
        ])
        requires_sliver = any([
            sliver_id, sliver_type, sliver_state, ip_subnet, ip_v4, ip_v6,
            host, site, component_type, component_model, bdf, vlan, facility,
            exclude_site, exclude_sliver_state, exclude_host
        ])

        now = datetime.utcnow()
        if requires_sliver:
            if not start_time and not end_time:
                end_time = now
                start_time = now - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
            elif start_time and not end_time:
                end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
            elif end_time and not start_time:
                start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)

        query = select(Users).distinct()

        if requires_slice or requires_sliver:
            query = query.join(Slices, Users.id == Slices.user_id)

        if project_id:
            if requires_slice or requires_sliver:
                query = query.join(Projects, Slices.project_id == Projects.id)
            else:
                query = query.join(Membership, Membership.user_id == Users.id)\
                    .join(Projects, Projects.id == Membership.project_id)

        if requires_sliver:
            query = query.join(Slivers, Users.id == Slivers.user_id)
            if host or site or exclude_host or exclude_site:
                query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                             .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

        filters = []

        if start_time or end_time:
            if requires_slice or requires_sliver:
                time_filter = self.__build_time_filter(Slices, start_time, end_time)
                if time_filter is not None:
                    filters.append(time_filter)
            else:
                st = start_time or (end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS))
                et = end_time or (start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS))
                filters.append(
                    or_(
                        and_(Membership.start_time <= et, Membership.end_time >= st),
                        and_(Membership.start_time <= et, Membership.end_time.is_(None))
                    )
                )

        if user_email:
            filters.append(Users.user_email.in_(user_email))
        if user_id:
            filters.append(Users.user_uuid.in_(user_id))
        if user_active is not None:
            filters.append(Users.active == user_active)
        if project_id:
            filters.append(Projects.project_uuid.in_(project_id))
        if project_type:
            filters.append(Projects.project_type.in_(project_type))
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
        if ip_v4:
            filters.append(Slivers.ip_v4.in_(ip_v4))
        if ip_v6:
            filters.append(Slivers.ip_v6.in_(ip_v6))
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
            query = query.where(and_(*filters))

        self.logger.info(f"Query Users (building query) = {time.time() - start_ts:.2f}s")
        count_ts = time.time()

        count_stmt = select(func.count(distinct(Users.id)))
        if requires_slice or requires_sliver:
            count_stmt = count_stmt.join(Slices, Users.id == Slices.user_id)
        if project_id:
            if requires_slice or requires_sliver:
                count_stmt = count_stmt.join(Projects, Slices.project_id == Projects.id)
        if requires_sliver:
            count_stmt = count_stmt.join(Slivers, Users.id == Slivers.user_id)
            if host or site or exclude_host or exclude_site:
                count_stmt = count_stmt.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                       .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                count_stmt = count_stmt.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                count_stmt = count_stmt.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))

        count_result = await session.execute(count_stmt)
        total_users = count_result.scalar()

        self.logger.info(f"Query Users (count) = {time.time() - count_ts:.2f}s")
        fetch_ts = time.time()

        paginated = query.offset(page * per_page).limit(per_page)
        result = await session.execute(paginated)
        users = result.scalars().all()

        self.logger.info(f"Query Users (fetch rows) = {time.time() - fetch_ts:.2f}s")
        parse_ts = time.time()

        result_list = []
        for u in users:
            user_dict = self.user_to_dict(u)

            if project_id or user_id or user_email:
                slices = await self.get_slices(
                    session=session, start_time=start_time, end_time=end_time,
                    user_email=[u.user_email], user_id=[u.user_uuid], vlan=vlan,
                    sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                    sliver_state=sliver_state, site=site, host=host, project_id=project_id,
                    component_model=component_model, component_type=component_type,
                    ip_subnet=ip_subnet, ip_v4=ip_v4, ip_v6=ip_v6,
                    exclude_site=exclude_site, exclude_host=exclude_host,
                    exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                    exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                    exclude_user_email=exclude_user_email)
                user_dict["slices"] = {
                    "total": slices.get("total"),
                    "data": slices.get("slices")
                }
            else:
                count_r = await session.execute(
                    select(func.count(Slices.id)).where(Slices.user_id == u.id)
                )
                user_dict["slices"] = {"total": count_r.scalar()}

            result_list.append(user_dict)

        self.logger.info(f"Query Users (dict building) = {time.time() - parse_ts:.2f}s")

        return {
            "total": total_users,
            "users": result_list
        }

    async def get_slivers(self, session: AsyncSession, start_time: datetime = None,
                          end_time: datetime = None, user_email: list[str] = None,
                          user_id: list[str] = None, project_id: list[str] = None,
                          component_type: list[str] = None,
                          slice_id: list[str] = None, slice_state: list[int] = None,
                          component_model: list[str] = None,
                          sliver_type: list[str] = None, sliver_id: list[str] = None,
                          sliver_state: list[int] = None,
                          site: list[str] = None, ip_subnet: list[str] = None,
                          bdf: list[str] = None,
                          ip_v4: list[str] = None, ip_v6: list[str] = None,
                          vlan: list[str] = None, host: list[str] = None,
                          exclude_user_id: list[str] = None,
                          exclude_user_email: list[str] = None,
                          exclude_project_id: list[str] = None,
                          exclude_site: list[str] = None, exclude_host: list[str] = None,
                          facility: list[str] = None,
                          exclude_slice_state: list[int] = None,
                          exclude_sliver_state: list[int] = None,
                          page: int = 0, per_page: int = 100) -> dict:
        start_ts = time.time()

        if start_time and not end_time:
            end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
        elif end_time and not start_time:
            start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)

        query = select(Slivers).distinct()
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
        if ip_v4:
            filters.append(Slivers.ip_v4.in_(ip_v4))
        if ip_v6:
            filters.append(Slivers.ip_v6.in_(ip_v6))
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
            query = query.where(and_(*filters))

        self.logger.info(f"Query Slivers (build query) = {time.time() - start_ts:.2f}s")
        count_ts = time.time()

        count_stmt = select(func.count(distinct(Slivers.id)))
        count_stmt = count_stmt.join(Slices, Slivers.slice_id == Slices.id)\
                               .join(Users, Slivers.user_id == Users.id)\
                               .join(Projects, Slivers.project_id == Projects.id)
        if host or site or exclude_host or exclude_site:
            count_stmt = count_stmt.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                   .outerjoin(Sites, Slivers.site_id == Sites.id)
        if component_type or component_model:
            count_stmt = count_stmt.outerjoin(Components, Slivers.id == Components.sliver_id)
        if bdf or vlan or facility:
            count_stmt = count_stmt.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))

        count_result = await session.execute(count_stmt)
        total_slivers = count_result.scalar()

        self.logger.info(f"Query Slivers (count) = {time.time() - count_ts:.2f}s")
        fetch_ts = time.time()

        paginated = query.offset(page * per_page).limit(per_page)
        result = await session.execute(paginated)
        slivers = result.scalars().all()

        self.logger.info(f"Query Slivers (fetch rows) = {time.time() - fetch_ts:.2f}s")
        parse_ts = time.time()

        # Preload related entities
        s_user_ids = {s.user_id for s in slivers}
        s_project_ids = {s.project_id for s in slivers}
        s_site_ids = {s.site_id for s in slivers if s.site_id}
        s_host_ids = {s.host_id for s in slivers if s.host_id}
        s_slice_ids = {s.slice_id for s in slivers}

        users_map = {}
        if s_user_ids:
            r = await session.execute(select(Users).where(Users.id.in_(s_user_ids)))
            users_map = {u.id: u for u in r.scalars().all()}

        projects_map = {}
        if s_project_ids:
            r = await session.execute(select(Projects).where(Projects.id.in_(s_project_ids)))
            projects_map = {p.id: p for p in r.scalars().all()}

        sites_map = {}
        if s_site_ids:
            r = await session.execute(select(Sites).where(Sites.id.in_(s_site_ids)))
            sites_map = {s.id: s for s in r.scalars().all()}

        hosts_map = {}
        if s_host_ids:
            r = await session.execute(select(Hosts).where(Hosts.id.in_(s_host_ids)))
            hosts_map = {h.id: h for h in r.scalars().all()}

        slices_map = {}
        if s_slice_ids:
            r = await session.execute(select(Slices).where(Slices.id.in_(s_slice_ids)))
            slices_map = {s.id: s for s in r.scalars().all()}

        result_list = []
        for s in slivers:
            user = users_map.get(s.user_id)
            project = projects_map.get(s.project_id)
            site_name = sites_map.get(s.site_id).name if s.site_id and sites_map.get(s.site_id) else None
            host_name = hosts_map.get(s.host_id).name if s.host_id and hosts_map.get(s.host_id) else None
            slice_guid = slices_map.get(s.slice_id).slice_guid if slices_map.get(s.slice_id) else None

            sliver_dict = self.sliver_to_dict(sliver=s, user=user, project=project,
                                              site=site_name, host=host_name, slice_id=slice_guid)

            comp_r = await session.execute(
                select(Components).where(Components.sliver_id == s.id)
            )
            components = comp_r.scalars().all()
            iface_r = await session.execute(
                select(Interfaces).where(Interfaces.sliver_id == s.id)
            )
            interfaces = iface_r.scalars().all()

            sliver_dict["components"] = {
                "total": len(components),
                "data": [self.component_to_dict(c) for c in components]
            }
            sliver_dict["interfaces"] = {
                "total": len(interfaces),
                "data": [self.interface_to_dict(i) for i in interfaces]
            }
            result_list.append(sliver_dict)

        self.logger.info(f"Query Slivers (dict building) = {time.time() - parse_ts:.2f}s")

        return {
            "total": total_slivers,
            "slivers": result_list
        }

    async def get_slices(self, session: AsyncSession, start_time: datetime = None,
                         end_time: datetime = None, user_email: list[str] = None,
                         user_id: list[str] = None, project_id: list[str] = None,
                         component_type: list[str] = None,
                         slice_id: list[str] = None, slice_state: list[int] = None,
                         component_model: list[str] = None,
                         sliver_type: list[str] = None, sliver_id: list[str] = None,
                         sliver_state: list[int] = None,
                         site: list[str] = None, ip_subnet: list[str] = None,
                         bdf: list[str] = None,
                         ip_v4: list[str] = None, ip_v6: list[str] = None,
                         vlan: list[str] = None, host: list[str] = None,
                         exclude_user_id: list[str] = None,
                         exclude_user_email: list[str] = None,
                         exclude_project_id: list[str] = None,
                         exclude_site: list[str] = None, exclude_host: list[str] = None,
                         facility: list[str] = None,
                         exclude_slice_state: list[int] = None,
                         exclude_sliver_state: list[int] = None,
                         page: int = 0, per_page: int = 100) -> dict:
        start_ts = time.time()

        if start_time and not end_time:
            end_time = start_time + timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)
        elif end_time and not start_time:
            start_time = end_time - timedelta(days=self.DEFAULT_TIME_WINDOW_DAYS)

        query = select(Slices).distinct()
        query = query.join(Users, Slices.user_id == Users.id)
        query = query.join(Projects, Slices.project_id == Projects.id)

        join_slivers = any([
            sliver_id, sliver_type, sliver_state, ip_subnet, ip_v4, ip_v6,
            site, host, component_type, component_model, bdf, vlan, facility,
            exclude_site, exclude_host, exclude_sliver_state
        ])

        if join_slivers:
            query = query.join(Slivers, Slices.id == Slivers.slice_id)
            if host or site or exclude_host or exclude_site:
                query = query.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                             .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                query = query.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                query = query.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)

        filters = []

        if start_time or end_time:
            time_filter = self.__build_time_filter(Slices, start_time, end_time)
            if time_filter is not None:
                filters.append(time_filter)

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
        if ip_v4:
            filters.append(Slivers.ip_v4.in_(ip_v4))
        if ip_v6:
            filters.append(Slivers.ip_v6.in_(ip_v6))
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
            query = query.where(and_(*filters))

        self.logger.info(f"Query Slices (build query) = {time.time() - start_ts:.2f}s")
        count_ts = time.time()

        count_stmt = select(func.count(distinct(Slices.id)))
        count_stmt = count_stmt.join(Users, Slices.user_id == Users.id)\
                               .join(Projects, Slices.project_id == Projects.id)
        if join_slivers:
            count_stmt = count_stmt.join(Slivers, Slices.id == Slivers.slice_id)
            if host or site or exclude_host or exclude_site:
                count_stmt = count_stmt.outerjoin(Hosts, Slivers.host_id == Hosts.id)\
                                       .outerjoin(Sites, Slivers.site_id == Sites.id)
            if component_type or component_model:
                count_stmt = count_stmt.outerjoin(Components, Slivers.id == Components.sliver_id)
            if bdf or vlan or facility:
                count_stmt = count_stmt.outerjoin(Interfaces, Slivers.id == Interfaces.sliver_id)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))

        count_result = await session.execute(count_stmt)
        total_slices = count_result.scalar()

        self.logger.info(f"Query Slices (count) = {time.time() - count_ts:.2f}s")
        fetch_ts = time.time()

        paginated = query.offset(page * per_page).limit(per_page)
        result = await session.execute(paginated)
        slices = result.scalars().all()

        self.logger.info(f"Query Slices (fetch rows) = {time.time() - fetch_ts:.2f}s")
        parse_ts = time.time()

        s_user_ids = {s.user_id for s in slices}
        s_project_ids = {s.project_id for s in slices}

        users_map = {}
        if s_user_ids:
            r = await session.execute(select(Users).where(Users.id.in_(s_user_ids)))
            users_map = {u.id: u for u in r.scalars().all()}

        projects_map = {}
        if s_project_ids:
            r = await session.execute(select(Projects).where(Projects.id.in_(s_project_ids)))
            projects_map = {p.id: p for p in r.scalars().all()}

        result_list = []
        for s in slices:
            user = users_map.get(s.user_id)
            project = projects_map.get(s.project_id)

            slice_dict = self.slice_to_dict(slice_obj=s, user=user, project=project)

            if slice_id:
                slivers = await self.get_slivers(
                    session=session, start_time=start_time, end_time=end_time,
                    user_email=user_email, user_id=user_id, vlan=vlan,
                    sliver_id=sliver_id, sliver_type=sliver_type, slice_id=[s.slice_guid],
                    bdf=bdf, sliver_state=sliver_state, site=site, host=host,
                    project_id=project_id, component_model=component_model,
                    component_type=component_type, ip_subnet=ip_subnet,
                    ip_v4=ip_v4, ip_v6=ip_v6,
                    exclude_site=exclude_site, exclude_host=exclude_host,
                    exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                    exclude_project_id=exclude_project_id, exclude_user_id=exclude_user_id,
                    exclude_user_email=exclude_user_email)
                slice_dict["slivers"] = {
                    "total": slivers.get("total"),
                    "data": slivers.get("slivers")
                }
            else:
                count_r = await session.execute(
                    select(func.count(Slivers.id)).where(Slivers.slice_id == s.id)
                )
                slice_dict["slivers"] = {"total": count_r.scalar()}

            result_list.append(slice_dict)

        self.logger.info(f"Query Slices (dict building) = {time.time() - parse_ts:.2f}s")

        return {
            "total": total_slices,
            "slices": result_list
        }

    # -------------------- DICT CONVERTERS --------------------
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
            "ip_v4": sliver.ip_v4,
            "ip_v6": sliver.ip_v6,
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
    def slice_to_dict(slice_obj: Slices, user: Users, project: Projects):
        return {
            "slice_id": slice_obj.slice_guid,
            "slice_name": slice_obj.slice_name,
            "state": SliceState(slice_obj.state).name,
            "lease_start": slice_obj.lease_start.isoformat() if slice_obj.lease_start else None,
            "lease_end": slice_obj.lease_end.isoformat() if slice_obj.lease_end else None,
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
            "bastion_login": user.bastion_login,
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

    # -------------------- HELPER QUERIES --------------------
    @staticmethod
    async def __get_user_count_for_project(session: AsyncSession, project_id: int):
        result = await session.execute(
            select(func.count(distinct(Membership.user_id)))
            .where(Membership.project_id == project_id, Membership.active.is_(True))
        )
        return result.scalar()

    async def get_user_memberships(
            self, session: AsyncSession, start_time: datetime, end_time: datetime,
            user_id: list[str], user_email: list[str],
            exclude_user_id: list[str], exclude_user_email: list[str],
            project_type: list[str] = None, exclude_project_type: list[str] = None,
            project_active: bool = None, project_expired: bool = None,
            project_retired: bool = None, user_active: bool = None,
            page: int = 0, per_page: int = 100):
        stmt = (
            select(Membership, Users, Projects)
            .join(Users, Membership.user_id == Users.id)
            .join(Projects, Membership.project_id == Projects.id)
        )

        filters = []

        if start_time and end_time:
            filters.append(or_(Membership.start_time.is_(None), Membership.start_time <= end_time))
            filters.append(or_(Membership.end_time.is_(None), Membership.end_time >= start_time))

        if user_id:
            filters.append(Users.user_uuid.in_(user_id))
        if user_email:
            filters.append(Users.user_email.in_(user_email))
        if exclude_user_id:
            filters.append(not_(Users.user_uuid.in_(exclude_user_id)))
        if exclude_user_email:
            filters.append(not_(Users.user_email.in_(exclude_user_email)))
        if user_active is not None:
            filters.append(Users.active == user_active)
        if project_type:
            filters.append(Projects.project_type.in_(project_type))
        if exclude_project_type:
            filters.append(not_(Projects.project_type.in_(exclude_project_type)))
        if project_active is not None:
            filters.append(Projects.active == project_active)
        if project_expired is True:
            filters.append(Projects.expires_on.isnot(None))
            filters.append(Projects.expires_on < datetime.utcnow())
        if project_retired is True:
            filters.append(Projects.retired_date.isnot(None))
        elif project_retired is False:
            filters.append(Projects.retired_date.is_(None))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Membership.start_time.desc())
        stmt = stmt.offset(page * per_page).limit(per_page)

        result = await session.execute(stmt)
        rows = result.all()

        output = {}
        priority_order = {"owner": 1, "creator": 2, "tokenholder": 3, "member": 4}

        for membership, user, project in rows:
            r_user_id = str(user.user_uuid)

            user_dict = self.user_to_dict(user)
            project_dict = self.project_to_dict(project)
            project_dict["membership_type"] = membership.membership_type
            project_dict["start_time"] = membership.start_time.isoformat() if membership.start_time else None
            project_dict["end_time"] = membership.end_time.isoformat() if membership.end_time else None
            project_dict["active"] = membership.active

            if r_user_id not in output:
                user_dict["projects"] = {}
                output[r_user_id] = user_dict

            project_key = f"{membership.project_id}_{membership.start_time}_{membership.end_time}"
            existing_entry = output[r_user_id]["projects"].get(project_key)

            current_priority = priority_order.get(membership.membership_type, 99)
            existing_priority = priority_order.get(
                existing_entry["membership_type"], 99
            ) if existing_entry else 999

            if not existing_entry or current_priority < existing_priority:
                output[r_user_id]["projects"][project_key] = project_dict

        for user_data in output.values():
            user_data["projects"] = list(user_data["projects"].values())

        return {
            "total": len(output.values()),
            "users": list(output.values())
        }

    async def get_project_membership(
        self, session: AsyncSession, start_time: datetime, end_time: datetime,
        project_id: list[str], exclude_project_id: list[str],
        project_type: list[str] = None, exclude_project_type: list[str] = None,
        project_active: bool = None, project_expired: bool = None,
        project_retired: bool = None, user_active: bool = None,
        page: int = 0, per_page: int = 100):
        stmt = (
            select(Membership, Users, Projects)
            .join(Users, Membership.user_id == Users.id)
            .join(Projects, Membership.project_id == Projects.id)
        )

        filters = []

        if start_time and end_time:
            filters.append(or_(Membership.start_time.is_(None), Membership.start_time <= end_time))
            filters.append(or_(Membership.end_time.is_(None), Membership.end_time >= start_time))

        if project_id:
            filters.append(Projects.project_uuid.in_(project_id))
        if exclude_project_id:
            filters.append(not_(Projects.project_uuid.in_(exclude_project_id)))
        if project_type:
            filters.append(Projects.project_type.in_(project_type))
        if exclude_project_type:
            filters.append(not_(Projects.project_type.in_(exclude_project_type)))
        if project_active is not None:
            filters.append(Projects.active == project_active)
        if project_expired is True:
            filters.append(Projects.expires_on.isnot(None))
            filters.append(Projects.expires_on < datetime.utcnow())
        if project_retired is True:
            filters.append(Projects.retired_date.isnot(None))
        elif project_retired is False:
            filters.append(Projects.retired_date.is_(None))
        if user_active is not None:
            filters.append(Users.active == user_active)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Membership.start_time.desc())
        stmt = stmt.offset(page * per_page).limit(per_page)

        result = await session.execute(stmt)
        rows = result.all()

        output = {}
        priority_order = {"owner": 1, "creator": 2, "tokenholder": 3, "member": 4}

        for membership, user, project in rows:
            r_project_id = str(project.project_uuid)

            project_dict = self.project_to_dict(project)
            user_dict = self.user_to_dict(user)
            user_dict["membership_type"] = membership.membership_type
            user_dict["start_time"] = membership.start_time.isoformat() if membership.start_time else None
            user_dict["end_time"] = membership.end_time.isoformat() if membership.end_time else None
            user_dict["active"] = membership.active

            if r_project_id not in output:
                project_dict["members"] = {}
                output[r_project_id] = project_dict

            user_key = f"{membership.user_id}_{membership.start_time}_{membership.end_time}"
            existing_entry = output[r_project_id]["members"].get(user_key)

            current_priority = priority_order.get(membership.membership_type, 99)
            existing_priority = priority_order.get(
                existing_entry["membership_type"], 99
            ) if existing_entry else 999

            if not existing_entry or current_priority < existing_priority:
                output[r_project_id]["members"][user_key] = user_dict

        for project_data in output.values():
            project_data["members"] = list(project_data["members"].values())

        return {
            "total": len(output.values()),
            "projects": list(output.values())
        }

    async def get_user_id_by_uuid(self, session: AsyncSession, user_uuid: str) -> int | None:
        result = await session.execute(select(Users).where(Users.user_uuid == user_uuid))
        user = result.scalars().first()
        return user.id if user else None

    async def get_project_id_by_uuid(self, session: AsyncSession, project_uuid: str) -> int | None:
        result = await session.execute(select(Projects).where(Projects.project_uuid == project_uuid))
        project = result.scalars().first()
        return project.id if project else None

    async def get_slice_by_slice_id(self, session: AsyncSession, slice_id: str) -> bool:
        result = await session.execute(select(Slices).where(Slices.slice_guid == slice_id))
        slice_obj = result.scalars().first()
        return slice_obj is not None

    async def get_active_membership(self, session: AsyncSession, user_id: int, project_id: int):
        result = await session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.project_id == project_id,
                Membership.active.is_(True)
            )
        )
        return result.scalars().first()

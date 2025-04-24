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
import traceback
from datetime import datetime

from flask import Response

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.slice_sliver_states import SliverStates, SliceState
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.security.fabric_token import FabricToken
from reports_api.swagger_server.models import Status200OkNoContentData, Status200OkNoContent
from reports_api.swagger_server.models.sliver import Sliver
from reports_api.swagger_server.models.slivers import Slivers  # noqa: E501


def slivers_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None,
                slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None,
                component_model=None, bdf=None, vlan=None, ip_subnet=None, site=None, host=None, exclude_user_id=None,
                exclude_user_email=None, exclude_project_id=None, exclude_site=None, exclude_host=None, facility=None,
                page=None, per_page=None):  # noqa: E501
    """Get slivers

    Retrieve a list of slivers with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: List[str]
    :param user_email: Filter by user email
    :type user_email: List[str]
    :param project_id: Filter by project uuid
    :type project_id: List[str]
    :param slice_id: Filter by slice uuid
    :type slice_id: List[str]
    :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type slice_state: List[str]
    :param sliver_id: Filter by sliver uuid
    :type sliver_id: List[str]
    :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
    :type sliver_type: List[str]
    :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type sliver_state: List[str]
    :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
    :type component_type: List[str]
    :param component_model: Filter by component model
    :type component_model: List[str]
    :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
    :type bdf: List[str]
    :param vlan: Filter by VLAN associated with their sliver interfaces.
    :type vlan: List[str]
    :param ip_subnet: Filter by specified IP subnet
    :type ip_subnet: List[str]
    :param site: Filter by site
    :type site: List[str]
    :param host: Filter by host
    :type host: List[str]
    :param facility: Filter by facility
    :type facility: List[str]
    :param exclude_user_id: Exclude Users by IDs
    :type exclude_user_id: List[str]
    :param exclude_user_email: Exclude Users by emails
    :type exclude_user_email: List[str]
    :param exclude_project_id: Exclude projects
    :type exclude_project_id: List[str]
    :param exclude_site: Exclude sites
    :type exclude_site: List[str]
    :param exclude_host: Exclude hosts
    :type exclude_host: List[str]
    :param page: Page number for pagination. Default is 1.
    :type page: int
    :param per_page: Number of records per page. Default is 10.
    :type per_page: int

    :rtype: Slivers
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - slivers_get")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            # This is a 401 Unauthorized response, already constructed
            return ret_val

        elif isinstance(ret_val, dict):
            # This was authorized via static bearer token (returns empty dict)
            logger.debug("Authorized via bearer token")

        elif isinstance(ret_val, FabricToken):
            # This was authorized via
            logger.debug("Authorized via Fabric token")

        global_obj = GlobalsSingleton.get()
        db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                 password=global_obj.config.database_config.get("db-password"),
                                 database=global_obj.config.database_config.get("db-name"),
                                 db_host=global_obj.config.database_config.get("db-host"))

        response = Slivers()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        sliver_states = [SliverStates.translate(s) for s in sliver_state] if sliver_state else None
        slice_states = [SliceState.translate(s) for s in slice_state] if slice_state else None

        slivers = db_mgr.get_slivers(start_time=start, end_time=end, user_email=user_email, user_id=user_id, vlan=vlan,
                                     sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                     sliver_state=sliver_states, site=site,
                                     host=host, project_id=project_id, component_model=component_model,
                                     slice_state=slice_states, facility=facility,
                                     component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
                                     exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                                     exclude_project_id=exclude_project_id, exclude_site=exclude_site,
                                     exclude_host=exclude_host)
        for s in slivers.get("slivers"):
            response.data.append(Sliver.from_dict(s))
        response.size = len(response.data)
        response.type = "slivers"
        response.total = slivers.get("total")
        logger.debug("Processed - slivers_get")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with slivers_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def slivers_slice_id_sliver_id_post(body: Sliver, slice_id: str, sliver_id: str):  # noqa: E501
    """Create/Update Sliver

    Create/Update Sliver. # noqa: E501

    :param body: Create/Modify sliver
    :type body: dict | bytes
    :param slice_id:
    :type slice_id:
    :param sliver_id:
    :type sliver_id:

    :rtype: Status200OkNoContent
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - slivers_slice_id_sliver_id_post")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            # This is a 401 Unauthorized response, already constructed
            return ret_val

        elif isinstance(ret_val, dict):
            # This was authorized via static bearer token (returns empty dict)
            logger.debug("Authorized via bearer token")

        elif isinstance(ret_val, FabricToken):
            # This was authorized via
            logger.debug("Authorized via Fabric token")

        global_obj = GlobalsSingleton.get()
        db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                 password=global_obj.config.database_config.get("db-password"),
                                 database=global_obj.config.database_config.get("db-name"),
                                 db_host=global_obj.config.database_config.get("db-host"))

        p_id = db_mgr.add_or_update_project(project_uuid=body.project_id, project_name=body.project_name)
        u_id = db_mgr.add_or_update_user(user_uuid=body.user_id, user_email=body.user_email)

        s_id = db_mgr.add_or_update_slice(project_id=p_id, user_id=u_id, slice_guid=body.slice_id,
                                          slice_name=body.slice_name, state=None,
                                          lease_start=body.lease_start, lease_end=body.lease_end)
        if body.site:
            site_id = db_mgr.add_or_update_site(site_name=body.site)
        else:
            site_id = None

        if body.host:
            host_id = db_mgr.add_or_update_host(host_name=body.host, site_id=site_id)
        else:
            host_id = None

        sl_id = db_mgr.add_or_update_sliver(project_id=p_id, user_id=u_id, slice_id=s_id, site_id=site_id,
                                            host_id=host_id, sliver_guid=sliver_id, lease_start=body.lease_start,
                                            lease_end=body.lease_end, state=SliverStates.translate(body.state),
                                            ip_subnet=body.ip_subnet, core=body.core, ram=body.ram, disk=body.disk,
                                            image=body.image, bandwidth=body.bandwidth, sliver_type=body.sliver_type,
                                            error=body.error)
        if body.components and body.components.data:
            for c in body.components.data:
                db_mgr.add_or_update_component(sliver_id=sl_id, component_guid=c.component_id,
                                               component_type=c.type, model=c.model, bdfs=c.bdfs,
                                               component_node_id=c.component_node_id, node_id=c.node_id)

        if body.interfaces and body.interfaces.data:
            for ifc in body.interfaces.data:
                db_mgr.add_or_update_interface(sliver_id=sl_id, interface_guid=ifc.interface_id, name=ifc.name,
                                               local_name=ifc.local_name, device_name=ifc.device_name, bdf=ifc.bdf,
                                               vlan=ifc.vlan, site_id=site_id)

        response_details = Status200OkNoContentData()
        response_details.details = f"Sliver '{sliver_id}' has been successfully created/updated"
        response = Status200OkNoContent()
        response.data = [response_details]
        response.size = len(response.data)
        response.status = 200
        response.type = 'no_content'
        logger.debug("Processed - slivers_slice_id_sliver_id_post")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with slivers_slice_id_sliver_id_post(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)

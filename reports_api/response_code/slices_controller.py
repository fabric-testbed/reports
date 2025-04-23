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
from datetime import datetime, timezone

from flask import Response

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.slice_sliver_states import SliverStates, SliceState
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.security.fabric_token import FabricToken
from reports_api.swagger_server.models import Status200OkNoContentData, Status200OkNoContent
from reports_api.swagger_server.models.slice import Slice
from reports_api.swagger_server.models.slices import Slices  # noqa: E501


def slices_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None,
               slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None,
               component_model=None, bdf=None, vlan=None, ip_subnet=None, site=None, host=None, facility=None,
               exclude_user_id=None, exclude_user_email=None, exclude_project_id=None, exclude_site=None,
               exclude_host=None, page=None, per_page=None):  # noqa: E501
    """Get slices

    Retrieve a list of slices with optional filters. # noqa: E501

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

    :rtype: Slices
    """
    logger = GlobalsSingleton.get().log
    try:
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

        response = Slices()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        sliver_states = [SliverStates.translate(s) for s in sliver_state] if sliver_state else None
        slice_states = [SliceState.translate(s) for s in slice_state] if slice_state else None

        result = db_mgr.get_slices(start_time=start, end_time=end, user_email=user_email, user_id=user_id, vlan=vlan,
                                   sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                   sliver_state=sliver_states, site=site,
                                   host=host, project_id=project_id, component_model=component_model,
                                   slice_state=slice_states, facility=facility,
                                   component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
                                   exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                                   exclude_project_id=exclude_project_id, exclude_site=exclude_site,
                                   exclude_host=exclude_host)
        for s in result.get("slices"):
            response.data.append(Slice.from_dict(s))
        response.size = len(response.data)
        response.type = "slices"
        response.total =result.get("total")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with slices_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def slices_slice_id_post(slice_id, body: Slice):  # noqa: E501
    """Create/Update a slice

    Create a Slice # noqa: E501

    :param slice_id:
    :type slice_id:
    :param body: Create new Slice
    :type body: dict | bytes

    :rtype: Status200OkNoContent
    """
    logger = GlobalsSingleton.get().log
    try:
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

        db_mgr.add_or_update_slice(project_id=p_id, user_id=u_id, slice_guid=body.slice_id,
                                   slice_name=body.slice_name, state=SliceState.translate(body.state),
                                   lease_start=body.lease_start, lease_end=body.lease_end)

        response_details = Status200OkNoContentData()
        response_details.details = f"Slice '{slice_id}' has been successfully created/updated"
        response = Status200OkNoContent()
        response.data = [response_details]
        response.size = len(response.data)
        response.status = 200
        response.type = 'no_content'

        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with slices_slice_id_post(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)

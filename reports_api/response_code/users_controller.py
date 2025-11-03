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
from typing import Optional

from flask import Response

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.slice_sliver_states import SliverStates, SliceState
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.security.fabric_token import FabricToken
from reports_api.openapi_server.models import UserMemberships, UserMembership
from reports_api.openapi_server.models.user import User
from reports_api.openapi_server.models.users import Users  # noqa: E501


def users_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None,
              slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None,
              component_model=None, bdf=None, vlan=None, ip_subnet=None, ip_v4=None, ip_v6=None, site=None, host=None, exclude_user_id=None,
              exclude_user_email=None, exclude_project_id=None, exclude_site=None, exclude_host=None, facility=None,
              exclude_slice_state=None, exclude_sliver_state=None, project_type=None, exclude_project_type=None,
              user_active=None, page=None, per_page=None):  # noqa: E501
    """Get users

    Retrieve a list of users with optional filters. # noqa: E501

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
    :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type exclude_slice_state: List[str]
    :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type exclude_sliver_state: List[str]
    :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
    :type project_type: List[str]
    :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
    :type exclude_project_type: List[str]
    :param user_active:
    :type user_active: bool
    :param page: Page number for pagination. Default is 1.
    :type page: int
    :param per_page: Number of records per page. Default is 10.
    :type per_page: int

    :rtype: Users
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - users_get")
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
                                 db_host=global_obj.config.database_config.get("db-host"),
                                 logger=logger)

        response = Users()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        sliver_states = [SliverStates.translate(s) for s in sliver_state] if sliver_state else None
        slice_states = [SliceState.translate(s) for s in slice_state] if slice_state else None
        exclude_sliver_states = [SliverStates.translate(s) for s in exclude_sliver_state] if exclude_sliver_state else None
        exclude_slice_states = [SliceState.translate(s) for s in exclude_slice_state] if exclude_slice_state else None

        users = db_mgr.get_users(start_time=start, end_time=end, user_email=user_email, user_id=user_id, vlan=vlan,
                                 sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                 sliver_state=sliver_states, site=site,
                                 host=host, project_id=project_id, component_model=component_model,
                                 slice_state=slice_states, facility=facility, ip_v4=ip_v4, ip_v6=ip_v6,
                                 component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
                                 exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                                 exclude_project_id=exclude_project_id, exclude_site=exclude_site,
                                 exclude_host=exclude_host, exclude_sliver_state=exclude_sliver_states,
                                 exclude_slice_state=exclude_slice_states,
                                 project_type=project_type, exclude_project_type=exclude_project_type,
                                 user_active=user_active)
        for u in users.get("users"):
            response.data.append(User.from_dict(u))
        response.size = len(response.data)
        response.type = "users"
        response.total = users.get("total")
        logger.debug("Processed - users_get")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with users_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def users_post(user_uuid: str,
               user_email: Optional[str] = None,
               active: Optional[bool] = None,
               name: Optional[str] = None,
               affiliation: Optional[str] = None,
               registered_on: Optional[str] = None,
               last_updated: Optional[str] = None,
               google_scholar: Optional[str] = None,
               scopus: Optional[str] = None):  # noqa: E501
    """
    Create or update a user in the system. # noqa: E501

    :param user_uuid: Unique identifier for the user.
    :type user_uuid: str
    :param user_email: Email address of the user.
    :type user_email: Optional[str]
    :param active: Whether the user is currently active.
    :type active: Optional[bool]
    :param name: Full name of the user.
    :type name: Optional[str]
    :param affiliation: Affiliation or organization of the user.
    :type affiliation: Optional[str]
    :param registered_on: ISO-formatted registration date and time.
    :type registered_on: Optional[str]
    :param last_updated: ISO-formatted last update timestamp.
    :type last_updated: Optional[str]
    :param google_scholar: Google Scholar profile link or ID.
    :type google_scholar: Optional[str]
    :param scopus: Scopus profile link or ID.
    :type scopus: Optional[str]

    :rtype: int
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - users_post")
        '''
        ret_val = authorize()

        if isinstance(ret_val, Response):
            return ret_val
        elif isinstance(ret_val, dict):
            logger.debug("Authorized via bearer token")
        elif isinstance(ret_val, FabricToken):
            logger.debug("Authorized via Fabric token")
        '''

        # Parse datetime strings
        reg_time = datetime.fromisoformat(registered_on) if registered_on else None
        update_time = datetime.fromisoformat(last_updated) if last_updated else None

        global_obj = GlobalsSingleton.get()
        db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                 password=global_obj.config.database_config.get("db-password"),
                                 database=global_obj.config.database_config.get("db-name"),
                                 db_host=global_obj.config.database_config.get("db-host"),
                                 logger=logger)

        user_id = db_mgr.add_or_update_user(
            user_uuid=user_uuid,
            user_email=user_email,
            active=active,
            name=name,
            affiliation=affiliation,
            registered_on=reg_time,
            last_updated=update_time,
            google_scholar=google_scholar,
            scopus=scopus
        )

        logger.debug(f"User record added/updated: {user_id}")
        #return cors_success_response({"id": user_id})
        return user_id
    except Exception as exc:
        details = f'Oops! something went wrong with users_post(): {exc}'
        logger.error(details)
        logger.error(traceback.format_exc())
        #return cors_500(details=details)


def users_memberships_get(start_time=None, end_time=None, user_id=None, user_email=None, exclude_user_id=None,
                          exclude_user_email=None, project_type=None, exclude_project_type=None, project_active=None,
                          project_expired=None, project_retired=None, user_active=None, page=None, per_page=None):  # noqa: E501
    """Get users

    Retrieve a list of users with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: List[str]
    :param user_email: Filter by user email
    :type user_email: List[str]
    :param exclude_user_id: Exclude Users by IDs
    :type exclude_user_id: List[str]
    :param exclude_user_email: Exclude Users by emails
    :type exclude_user_email: List[str]
    :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
    :type project_type: List[str]
    :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
    :type exclude_project_type: List[str]
    :param active:
    :type active: bool
    :param page: Page number for pagination. Default is 0.
    :type page: int
    :param per_page: Number of records per page. Default is 200.
    :type per_page: int

    :rtype: Users
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - users_memberships_get")
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
                                 db_host=global_obj.config.database_config.get("db-host"),
                                 logger=logger)

        response = UserMemberships()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None

        users = db_mgr.get_user_memberships(start_time=start, end_time=end, user_email=user_email, user_id=user_id,
                                            exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                                            project_type=project_type, exclude_project_type=exclude_project_type,
                                            project_active=project_active, project_expired=project_expired,
                                            project_retired=project_retired, user_active=user_active,
                                            page=page, per_page=per_page)
        for u in users.get("users"):
            response.data.append(UserMembership.from_dict(u))
        response.size = len(response.data)
        response.type = "userMemberships"
        response.total = users.get("total")
        logger.debug("Processed - users_memberships_get")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with users_memberships_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def users_uuid_get(uuid):  # noqa: E501
    """Get specific user

    Returns a user identified by uuid. # noqa: E501

    :param uuid: User identified by universally unique identifier
    :type uuid: str

    :rtype: Users
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - users_uuid_get")
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
                                 db_host=global_obj.config.database_config.get("db-host"),
                                 logger=logger)

        response = Users()
        response.data = []

        users = db_mgr.get_users(user_id=[uuid])
        for u in users.get("users"):
            response.data.append(User.from_dict(u))
        response.size = len(response.data)
        response.type = "users"
        response.total = users.get("total")
        logger.debug("Processed - users_get")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with users_uuid_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)
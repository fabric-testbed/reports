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
from datetime import datetime, timezone

from analytics_api.common.globals import GlobalsSingleton
from analytics_api.database.db_manager import DatabaseManager
from analytics_api.response_code.cors_response import cors_500
from analytics_api.response_code.sliver_states import SliverStates
from analytics_api.response_code.utils import authorize, cors_success_response
from analytics_api.swagger_server.models import Component, Interface, Sliver
from analytics_api.swagger_server.models.components import Components  # noqa: E501
from analytics_api.swagger_server.models.interfaces import Interfaces  # noqa: E501
from analytics_api.swagger_server.models.slivers import Slivers  # noqa: E501


def slivers_get(start_time: str = None, end_time: str = None, user_email: str = None, slice_id: str = None,
                user_id: str = None, project_id: str = None, component_type: str = None, component_model: str = None,
                sliver_type: str = None, sliver_state: str = None, site: str = None, ip_subnet: str = None,
                sliver_id: str = None, bdf: str = None, vlan: str = None, host: str = None, page: int = 0,
                per_page: int = 100):
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

    :rtype: Slivers
    """
    logger = GlobalsSingleton.get().log
    try:
        fabric_token = authorize()
        global_obj = GlobalsSingleton.get()
        db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                 password=global_obj.config.database_config.get("db-password"),
                                 database=global_obj.config.database_config.get("db-name"),
                                 db_host=global_obj.config.database_config.get("db-host"))

        response = Slivers()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        slivers = db_mgr.get_slivers(start_time=start, end_time=end, user_email=user_email, user_id=user_id, vlan=vlan,
                                     sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                     sliver_state=SliverStates.translate(sliver_state), site=site, host=host,
                                     project_id=project_id, component_model=component_model,
                                     component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page)
        print(slivers)
        for s in slivers:
            response.data.append(Sliver.from_dict(s))
        response.size = len(response.data)
        response.type = "slivers"
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with slivers_get(): {0}'.format(exc)
        logger.error(details)
        return cors_500(details=details)
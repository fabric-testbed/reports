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
from datetime import datetime

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.slice_sliver_states import SliverStates
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.swagger_server.models.project import Project
from reports_api.swagger_server.models.projects import Projects  # noqa: E501


def projects_get(start_time: str = None, end_time: str = None, user_email: str = None,  user_id: str = None,
                 project_id: str = None, component_type: str = None, slice_id: str = None, slice_state: str = None,
                 component_model: str = None, sliver_type: str = None, sliver_id: str = None, sliver_state: str = None,
                 site: str = None, ip_subnet: str = None, bdf: str = None, vlan: str = None, host: str = None,
                 page: int = 0, per_page: int = 100):
    """
    Returns a paginated list of projects with their UUIDs. # noqa: E501

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
    :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type slice_state: str
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

    :rtype: Projects
    """
    logger = GlobalsSingleton.get().log
    try:
        fabric_token = authorize()
        global_obj = GlobalsSingleton.get()
        db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                 password=global_obj.config.database_config.get("db-password"),
                                 database=global_obj.config.database_config.get("db-name"),
                                 db_host=global_obj.config.database_config.get("db-host"))

        response = Projects()
        response.data = []
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        projects = db_mgr.get_projects(start_time=start, end_time=end, user_email=user_email, user_id=user_id, vlan=vlan,
                                       sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                                       sliver_state=SliverStates.translate(sliver_state),site=site, host=host,
                                       project_id=project_id, component_model=component_model,
                                       slice_state=SliverStates.translate(slice_state),
                                       component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page)
        for s in projects.get("projects"):
            response.data.append(Project.from_dict(s))
        response.size = len(response.data)
        response.type = "projects"
        response.total = projects.get("total")
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with projects_get(): {0}'.format(exc)
        logger.error(details)
        return cors_500(details=details)

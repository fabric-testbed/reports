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

from flask import Response

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.security.fabric_token import FabricToken
from reports_api.swagger_server.models.site import Site
from reports_api.swagger_server.models.sites import Sites


def hosts_get(site=None, exclude_site=None):  # noqa: E501
    """Get hosts

    Retrieve a list of hosts. # noqa: E501

    :param site: Filter by site
    :type site: List[str]

    :param exclude_site: Exclude sites
    :type exclude_site: List[str]

    :rtype: Sites
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

        response = Sites()
        response.data = []
        for h in db_mgr.get_hosts(site=site, exclude_site=exclude_site):
            response.data.append(Site.from_dict(h))
        response.size = len(response.data)
        response.type = "hosts"
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with hosts_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)
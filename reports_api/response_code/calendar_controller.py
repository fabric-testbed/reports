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
import traceback
from datetime import datetime

from flask import Response

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500, cors_401, cors_400, cors_response
from reports_api.response_code.utils import authorize, cors_success_response
from reports_api.security.fabric_token import FabricToken
from reports_api.openapi_server.models import Status200OkNoContentData, Status200OkNoContent


def _get_db_manager():
    global_obj = GlobalsSingleton.get()
    return DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                           password=global_obj.config.database_config.get("db-password"),
                           database=global_obj.config.database_config.get("db-name"),
                           db_host=global_obj.config.database_config.get("db-host"),
                           logger=global_obj.log)


def calendar_get(start_time=None, end_time=None, interval=None, site=None, host=None,
                 exclude_site=None, exclude_host=None):
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - calendar_get")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            return ret_val
        elif isinstance(ret_val, dict):
            logger.debug("Authorized via bearer token")
        elif isinstance(ret_val, FabricToken):
            logger.debug("Authorized via Fabric token")

        if not start_time or not end_time:
            return cors_400(details="start_time and end_time are required")

        # URL decoding turns '+' into ' ' in timezone offsets like +00:00
        start_time = start_time.replace(' ', '+')
        end_time = end_time.replace(' ', '+')

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        if start >= end:
            return cors_400(details="start_time must be before end_time")

        if interval and interval not in ("day", "week"):
            return cors_400(details="interval must be 'day' or 'week'")

        db_mgr = _get_db_manager()
        result = db_mgr.get_calendar(start_time=start, end_time=end,
                                     interval=interval or "day",
                                     site=site, host=host,
                                     exclude_site=exclude_site, exclude_host=exclude_host)

        from flask import request
        response = cors_response(req=request, status_code=200,
                                 body=json.dumps(result, indent=2, sort_keys=True))
        return response
    except Exception as exc:
        details = 'Oops! something went wrong with calendar_get(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def hosts_host_name_capacity_post(host_name=None, body=None):
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - hosts_host_name_capacity_post")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            return ret_val
        elif isinstance(ret_val, dict):
            logger.debug("Authorized via bearer token")
        elif isinstance(ret_val, FabricToken):
            return cors_401(details=f"{ret_val.uuid}/{ret_val.email} is not authorized!")

        db_mgr = _get_db_manager()
        db_mgr.add_or_update_host_capacity(
            host_name=host_name,
            site_name=body.get("site"),
            cores=body.get("cores_capacity", 0),
            ram=body.get("ram_capacity", 0),
            disk=body.get("disk_capacity", 0),
            components=body.get("components")
        )

        response = Status200OkNoContent()
        response.data = [Status200OkNoContentData()]
        response.data[0].message = "Host capacity updated successfully"
        response.type = "no_content"
        response.size = 1
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with hosts_host_name_capacity_post(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def links_link_name_capacity_post(link_name=None, body=None):
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - links_link_name_capacity_post")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            return ret_val
        elif isinstance(ret_val, dict):
            logger.debug("Authorized via bearer token")
        elif isinstance(ret_val, FabricToken):
            return cors_401(details=f"{ret_val.uuid}/{ret_val.email} is not authorized!")

        db_mgr = _get_db_manager()
        db_mgr.add_or_update_link_capacity(
            link_name=link_name,
            site_a_name=body.get("site_a"),
            site_b_name=body.get("site_b"),
            layer=body.get("layer"),
            bandwidth=body.get("bandwidth_capacity", 0)
        )

        response = Status200OkNoContent()
        response.data = [Status200OkNoContentData()]
        response.data[0].message = "Link capacity updated successfully"
        response.type = "no_content"
        response.size = 1
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with links_link_name_capacity_post(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)


def facility_ports_port_name_capacity_post(port_name=None, body=None):
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - facility_ports_port_name_capacity_post")
        ret_val = authorize()

        if isinstance(ret_val, Response):
            return ret_val
        elif isinstance(ret_val, dict):
            logger.debug("Authorized via bearer token")
        elif isinstance(ret_val, FabricToken):
            return cors_401(details=f"{ret_val.uuid}/{ret_val.email} is not authorized!")

        db_mgr = _get_db_manager()
        db_mgr.add_or_update_facility_port_capacity(
            port_name=port_name,
            site_name=body.get("site"),
            device_name=body.get("device_name"),
            local_name=body.get("local_name"),
            vlan_range=body.get("vlan_range"),
            total_vlans=body.get("total_vlans", 0)
        )

        response = Status200OkNoContent()
        response.data = [Status200OkNoContentData()]
        response.data[0].message = "Facility port capacity updated successfully"
        response.type = "no_content"
        response.size = 1
        return cors_success_response(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with facility_ports_port_name_capacity_post(): {0}'.format(exc)
        logger.error(details)
        logger.error(traceback.format_exc())
        return cors_500(details=details)

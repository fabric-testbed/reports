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
import datetime
import json
import os
from typing import Union

from flask import request, Response

# Constants
from analytics_api.database import Hosts, Users
from analytics_api.swagger_server.models import Slices, Slivers, Version, \
    Status400BadRequestErrors, Status400BadRequest, Status401UnauthorizedErrors, \
    Status401Unauthorized, Status403ForbiddenErrors, Status403Forbidden, Status404NotFoundErrors, Status404NotFound, \
    Status500InternalServerErrorErrors, Status500InternalServerError

_INDENT = int(os.getenv('OC_API_JSON_RESPONSE_INDENT', '4'))


def delete_none(_dict):
    """
    Delete None values recursively from all of the dictionaries, tuples, lists, sets
    """
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none(value)
            elif value is None or key is None:
                del _dict[key]

    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)

    return _dict


def cors_response(req: request, status_code: int = 200, body: object = None, x_error: str = None) -> Response:
    """
    Return CORS Response object
    """
    response = Response()
    response.status_code = status_code
    response.data = body
    response.headers['Access-Control-Allow-Origin'] = req.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = \
        'DNT, User-Agent, X-Requested-With, If-Modified-Since, Cache-Control, Content-Type, Range, Authorization'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range, X-Error'

    if x_error:
        response.headers['X-Error'] = x_error

    return response


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    else:
        return obj


def cors_200(response_body: Union[Slices, Slivers, Version, Hosts, Users] = None) -> cors_response:
    """
    Return 200 - OK
    """
    sanitized_response_body = sanitize_for_json(response_body.to_dict())
    body = json.dumps(delete_none(sanitized_response_body), indent=_INDENT, sort_keys=True) \
        if _INDENT != 0 else json.dumps(delete_none(sanitized_response_body), sort_keys=True)
    return cors_response(
        req=request,
        status_code=200,
        body=body
    )


def cors_400(details: str = None) -> cors_response:
    """
    Return 400 - Bad Request
    """
    errors = Status400BadRequestErrors()
    errors.details = details
    error_object = Status400BadRequest([errors])
    return cors_response(
        req=request,
        status_code=400,
        body=json.dumps(delete_none(error_object.to_dict()), indent=_INDENT, sort_keys=True)
        if _INDENT != 0 else json.dumps(delete_none(error_object.to_dict()), sort_keys=True),
        x_error=details
    )


def cors_401(details: str = None) -> cors_response:
    """
    Return 401 - Unauthorized
    """
    errors = Status401UnauthorizedErrors()
    errors.details = details
    error_object = Status401Unauthorized([errors])
    return cors_response(
        req=request,
        status_code=401,
        body=json.dumps(delete_none(error_object.to_dict()), indent=_INDENT, sort_keys=True)
        if _INDENT != 0 else json.dumps(delete_none(error_object.to_dict()), sort_keys=True),
        x_error=details
    )


def cors_403(details: str = None) -> cors_response:
    """
    Return 403 - Forbidden
    """
    errors = Status403ForbiddenErrors()
    errors.details = details
    error_object = Status403Forbidden([errors])
    return cors_response(
        req=request,
        status_code=403,
        body=json.dumps(delete_none(error_object.to_dict()), indent=_INDENT, sort_keys=True)
        if _INDENT != 0 else json.dumps(delete_none(error_object.to_dict()), sort_keys=True),
        x_error=details
    )


def cors_404(details: str = None) -> cors_response:
    """
    Return 404 - Not Found
    """
    errors = Status404NotFoundErrors()
    errors.details = details
    error_object = Status404NotFound([errors])
    return cors_response(
        req=request,
        status_code=404,
        body=json.dumps(delete_none(error_object.to_dict()), indent=_INDENT, sort_keys=True)
        if _INDENT != 0 else json.dumps(delete_none(error_object.to_dict()), sort_keys=True),
        x_error=details
    )


def cors_500(details: str = None) -> cors_response:
    """
    Return 500 - Internal Server Error
    """
    errors = Status500InternalServerErrorErrors()
    errors.details = details
    error_object = Status500InternalServerError([errors])
    return cors_response(
        req=request,
        status_code=500,
        body=json.dumps(delete_none(error_object.to_dict()), indent=_INDENT, sort_keys=True)
        if _INDENT != 0 else json.dumps(delete_none(error_object.to_dict()), sort_keys=True),
        x_error=details
    )

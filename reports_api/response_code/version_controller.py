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
from reports_api.common.globals import GlobalsSingleton
from reports_api.response_code.cors_response import cors_200, cors_500
from reports_api.swagger_server.models import VersionData
from reports_api.swagger_server.models.version import Version  # noqa: E501

from reports_api import __version__, __API_REFERENCE__


def version_get() -> Version:  # noqa: E501
    """version

    Version # noqa: E501


    :rtype: Version
    """
    logger = GlobalsSingleton.get().log
    try:
        logger.debug("Processing - version_get")
        version = VersionData()
        version.reference = __API_REFERENCE__
        version.version = __version__
        response = Version()
        response.data = [version]
        response.size = len(response.data)
        response.status = 200
        response.type = 'version'
        logger.debug("Processed- version_get")
        return cors_200(response_body=response)
    except Exception as exc:
        details = 'Oops! something went wrong with version_get(): {0}'.format(exc)
        logger.error(details)
        return cors_500(details=details)

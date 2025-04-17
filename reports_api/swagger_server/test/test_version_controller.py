# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from reports_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from reports_api.swagger_server.models.version import Version  # noqa: E501
from reports_api.swagger_server.test import BaseTestCase


class TestVersionController(BaseTestCase):
    """VersionController integration test stubs"""

    def test_version_get(self):
        """Test case for version_get

        Version
        """
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/version',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

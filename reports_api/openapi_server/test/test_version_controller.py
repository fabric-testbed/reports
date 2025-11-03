import unittest

from flask import json

from reports_api.openapi_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from reports_api.openapi_server.models.version import Version  # noqa: E501
from reports_api.openapi_server.test import BaseTestCase


class TestVersionController(BaseTestCase):
    """VersionController integration test stubs"""

    def test_version_get(self):
        """Test case for version_get

        Version
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/version',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()

# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from reports_api.swagger_server.models.sites import Sites  # noqa: E501
from reports_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from reports_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from reports_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from reports_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from reports_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from reports_api.swagger_server.test import BaseTestCase


class TestSitesController(BaseTestCase):
    """SitesController integration test stubs"""

    def test_sites_get(self):
        """Test case for sites_get

        Get sites
        """
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/sites',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

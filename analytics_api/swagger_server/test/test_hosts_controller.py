# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from analytics_api.swagger_server.models.sites import Sites  # noqa: E501
from analytics_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from analytics_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from analytics_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from analytics_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from analytics_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from analytics_api.swagger_server.test import BaseTestCase


class TestHostsController(BaseTestCase):
    """HostsController integration test stubs"""

    def test_hosts_get(self):
        """Test case for hosts_get

        Get hosts
        """
        query_string = [('site', 'site_example')]
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/hosts',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

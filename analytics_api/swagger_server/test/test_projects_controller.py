# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from analytics_api.swagger_server.models.projects import Projects  # noqa: E501
from analytics_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from analytics_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from analytics_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from analytics_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from analytics_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from analytics_api.swagger_server.test import BaseTestCase


class TestProjectsController(BaseTestCase):
    """ProjectsController integration test stubs"""

    def test_projects_get(self):
        """Test case for projects_get

        Retrieve a list of projects
        """
        query_string = [('start_time', '2013-10-20T19:20:30+01:00'),
                        ('end_time', '2013-10-20T19:20:30+01:00'),
                        ('user_id', 'user_id_example'),
                        ('user_email', 'user_email_example'),
                        ('project_id', 'project_id_example'),
                        ('slice_id', 'slice_id_example'),
                        ('slice_state', 'slice_state_example'),
                        ('sliver_id', 'sliver_id_example'),
                        ('sliver_type', 'sliver_type_example'),
                        ('sliver_state', 'sliver_state_example'),
                        ('component_type', 'component_type_example'),
                        ('component_model', 'component_model_example'),
                        ('bdf', 'bdf_example'),
                        ('vlan', 'vlan_example'),
                        ('ip_subnet', 'ip_subnet_example'),
                        ('site', 'site_example'),
                        ('host', 'host_example'),
                        ('page', 1),
                        ('per_page', 100)]
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/projects',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from reports_api.swagger_server.models.slivers import Slivers  # noqa: E501
from reports_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from reports_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from reports_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from reports_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from reports_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from reports_api.swagger_server.test import BaseTestCase


class TestSliversController(BaseTestCase):
    """SliversController integration test stubs"""

    def test_slivers_get(self):
        """Test case for slivers_get

        Get slivers
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
                        ('facility', 'facility_example'),
                        ('site', 'site_example'),
                        ('host', 'host_example'),
                        ('exclude_user_id', 'exclude_user_id_example'),
                        ('exclude_user_email', 'exclude_user_email_example'),
                        ('exclude_project_id', 'exclude_project_id_example'),
                        ('exclude_site', 'exclude_site_example'),
                        ('exclude_host', 'exclude_host_example'),
                        ('page', 1),
                        ('per_page', 100)]
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/slivers',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_slivers_slice_id_sliver_id_post(self):
        """Test case for slivers_slice_id_sliver_id_post

        Create/Update Sliver
        """
        body = Sliver()
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/slivers/{slice_id}/{sliver_id}'.format(slice_id='38400000-8cf0-11bd-b23e-10b96e4ef00d', sliver_id='38400000-8cf0-11bd-b23e-10b96e4ef00d'),
            method='POST',
            data=json.dumps(body),
            content_type='text/plain')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

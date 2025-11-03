import unittest

from flask import json

from reports_api.openapi_server.models.slice import Slice  # noqa: E501
from reports_api.openapi_server.models.slices import Slices  # noqa: E501
from reports_api.openapi_server.models.status200_ok_no_content import Status200OkNoContent  # noqa: E501
from reports_api.openapi_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from reports_api.openapi_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from reports_api.openapi_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from reports_api.openapi_server.models.status404_not_found import Status404NotFound  # noqa: E501
from reports_api.openapi_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from reports_api.openapi_server.test import BaseTestCase


class TestSlicesController(BaseTestCase):
    """SlicesController integration test stubs"""

    def test_slices_get(self):
        """Test case for slices_get

        Get slices
        """
        query_string = [('start_time', '2013-10-20T19:20:30+01:00'),
                        ('end_time', '2013-10-20T19:20:30+01:00'),
                        ('user_id', ['user_id_example']),
                        ('user_email', ['user_email_example']),
                        ('project_id', ['project_id_example']),
                        ('slice_id', ['slice_id_example']),
                        ('slice_state', ['slice_state_example']),
                        ('sliver_id', ['sliver_id_example']),
                        ('sliver_type', ['sliver_type_example']),
                        ('sliver_state', ['sliver_state_example']),
                        ('component_type', ['component_type_example']),
                        ('component_model', ['component_model_example']),
                        ('bdf', ['bdf_example']),
                        ('vlan', ['vlan_example']),
                        ('ip_subnet', ['ip_subnet_example']),
                        ('ip_v4', ['ip_v4_example']),
                        ('ip_v6', ['ip_v6_example']),
                        ('facility', ['facility_example']),
                        ('site', ['site_example']),
                        ('host', ['host_example']),
                        ('exclude_user_id', ['exclude_user_id_example']),
                        ('exclude_user_email', ['exclude_user_email_example']),
                        ('exclude_project_id', ['exclude_project_id_example']),
                        ('exclude_site', ['exclude_site_example']),
                        ('exclude_host', ['exclude_host_example']),
                        ('exclude_slice_state', ['exclude_slice_state_example']),
                        ('exclude_sliver_state', ['exclude_sliver_state_example']),
                        ('page', 0),
                        ('per_page', 200)]
        headers = { 
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/slices',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_slices_slice_id_post(self):
        """Test case for slices_slice_id_post

        Create/Update a slice
        """
        slice = openapi_server.Slice()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/slices/{slice_id}'.format(slice_id='a3f41e9a-7e2b-4df7-baf7-12f48a3c8e6f'),
            method='POST',
            headers=headers,
            data=json.dumps(slice),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()

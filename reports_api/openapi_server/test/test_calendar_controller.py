import unittest

from flask import json

from reports_api.openapi_server.test import BaseTestCase


class TestCalendarController(BaseTestCase):
    """CalendarController integration test stubs"""

    def test_calendar_get(self):
        """Test case for calendar_get

        Get resource availability calendar
        """
        query_string = [('start_time', '2025-07-01T00:00:00+00:00'),
                        ('end_time', '2025-07-04T00:00:00+00:00'),
                        ('interval', 'day')]
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_calendar_find_slot(self):
        """Test case for calendar_find_slot

        Find available time slots for resources
        """
        body = {
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [
                {"type": "compute", "site": "RENC", "cores": 2, "ram": 4, "disk": 10}
            ]
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_calendar_find_slot_multi_resource(self):
        """Test case for find_slot with compute + link"""
        body = {
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 48,
            "max_results": 5,
            "resources": [
                {"type": "compute", "site": "RENC", "cores": 32, "ram": 64, "disk": 100,
                 "components": {"GPU-A100": 1}},
                {"type": "compute", "site": "RENC", "cores": 32, "ram": 64, "disk": 100},
                {"type": "link", "site_a": "RENC", "site_b": "CLEM", "bandwidth": 25}
            ]
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_calendar_find_slot_facility_port(self):
        """Test case for find_slot with facility port"""
        body = {
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [
                {"type": "facility_port", "name": "RENC-Chameleon", "site": "RENC", "vlans": 2}
            ]
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_calendar_find_slot_validation_error(self):
        """Test case for find_slot with invalid body"""
        body = {
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "invalid_type"}]
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='application/json')
        self.assert400(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_calendar_find_slot_empty_body(self):
        """Test case for find_slot with empty body"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        response = self.client.open(
            '/RENCI3/analytics/1.0.0/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps({}),
            content_type='application/json')
        self.assert400(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()

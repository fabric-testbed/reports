#!/usr/bin/env python3
"""
Unit tests for input validation in calendar_find_slot controller.

Uses a Flask test app context to provide request context for cors_* response helpers.
Mocks GlobalsSingleton and authorize so controller validation logic runs without server config.
"""
import json
import logging
import unittest
from unittest.mock import patch, MagicMock

import connexion
from flask_testing import TestCase


# Set up mock before importing anything that uses GlobalsSingleton
_mock_globals = MagicMock()
_mock_globals.log = logging.getLogger("test_find_slot_validation")
_mock_globals.config.database_config = {
    "db-user": "test", "db-password": "test",
    "db-name": "test", "db-host": "localhost",
}


class BaseValidationTestCase(TestCase):
    """Provides a Flask app context for testing controller functions directly."""

    def create_app(self):
        app = connexion.App(__name__, specification_dir='../reports_api/openapi_server/openapi/')
        app.app.json_encoder = None
        app.add_api('openapi.yaml', pythonic_params=True)
        return app.app


@patch('reports_api.response_code.calendar_controller.authorize', return_value={"sub": "test"})
@patch('reports_api.response_code.calendar_controller.GlobalsSingleton')
class TestFindSlotValidation(BaseValidationTestCase):
    """Test input validation in calendar_find_slot via HTTP calls."""

    def _post(self, body):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer special-key',
        }
        return self.client.open(
            '/reports/calendar/find-slot',
            method='POST',
            headers=headers,
            data=json.dumps(body) if body is not None else '{}',
            content_type='application/json')

    def test_empty_body(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({})
        self.assert400(response)

    def test_missing_start(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_missing_end(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_missing_duration(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_zero_duration(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 0,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_negative_duration(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": -5,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_missing_resources(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
        })
        self.assert400(response)

    def test_empty_resources(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": []
        })
        self.assert400(response)

    def test_start_after_end(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-15T00:00:00+00:00",
            "end": "2025-07-01T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_range_exceeds_30_days(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-09-01T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_duration_exceeds_range(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-02T00:00:00+00:00",
            "duration": 48,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_max_results_too_high(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "max_results": 100,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_max_results_zero(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "max_results": 0,
            "resources": [{"type": "compute", "cores": 2}]
        })
        self.assert400(response)

    def test_invalid_resource_type(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "storage"}]
        })
        self.assert400(response)

    def test_link_missing_site_b(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "link", "site_a": "RENC"}]
        })
        self.assert400(response)

    def test_link_missing_bandwidth(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "link", "site_a": "RENC", "site_b": "CLEM"}]
        })
        self.assert400(response)

    def test_facility_port_missing_name(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "facility_port", "site": "RENC", "vlans": 2}]
        })
        self.assert400(response)

    def test_facility_port_missing_vlans(self, mock_gs, mock_auth):
        mock_gs.get.return_value = _mock_globals
        response = self._post({
            "start": "2025-07-01T00:00:00+00:00",
            "end": "2025-07-15T00:00:00+00:00",
            "duration": 24,
            "resources": [{"type": "facility_port", "name": "FP1", "site": "RENC"}]
        })
        self.assert400(response)


if __name__ == '__main__':
    unittest.main()

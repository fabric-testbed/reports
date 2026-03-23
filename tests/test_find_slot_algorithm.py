#!/usr/bin/env python3
"""
Unit tests for the find-slot algorithm (_check_window and find_slot helpers).

These tests use mock data objects — no database required.
"""
import unittest
from collections import namedtuple
from datetime import datetime, timedelta, timezone

from reports_api.database.db_manager import DatabaseManager


# Mock sliver row (matches SQLAlchemy result shape)
SliverRow = namedtuple("SliverRow", ["id", "host_id", "core", "ram", "disk", "lease_start", "lease_end"])
NetSliverRow = namedtuple("NetSliverRow", ["id", "bandwidth", "lease_start", "lease_end"])
FpIfaceRow = namedtuple("FpIfaceRow", ["fp_name", "site_name", "vlan", "lease_start", "lease_end"])


def dt(year, month, day, hour=0):
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


class TestCheckWindow(unittest.TestCase):
    """Tests for DatabaseManager._check_window static method."""

    def _make_host_cap_map(self, hosts):
        """Build host_cap_map from list of (id, site, cores, ram, disk, components) tuples."""
        cap_map = {}
        for hid, site, cores, ram, disk, comps in hosts:
            cap_map[hid] = {
                "name": f"host-{hid}", "site": site,
                "cores_capacity": cores, "ram_capacity": ram,
                "disk_capacity": disk,
                "components": comps or {}
            }
        return cap_map

    def _make_hosts_by_site(self, host_cap_map):
        from collections import defaultdict
        hbs = defaultdict(list)
        for hid, cap in host_cap_map.items():
            hbs[cap["site"]].append(hid)
        return hbs

    # ── Compute tests ──

    def test_single_compute_fits(self):
        """Single compute request fits on a host with no existing slivers."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "site": "RENC", "cores": 32, "ram": 64, "disk": 100}]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_single_compute_does_not_fit(self):
        """Single compute request exceeds host capacity."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 16, 32, 100, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "site": "RENC", "cores": 32, "ram": 64, "disk": 100}]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    def test_two_computes_bin_pack_same_host(self):
        """Two small compute requests fit on one large host."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100},
            {"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100},
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_two_computes_bin_pack_fails_cumulative(self):
        """Two compute requests each need 32 cores but only 48 available — bin-packing catches this."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 48, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 32, "ram": 32, "disk": 100},
            {"type": "compute", "site": "RENC", "cores": 32, "ram": 32, "disk": 100},
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    def test_two_computes_spread_across_hosts(self):
        """Two 32-core requests spread across two 48-core hosts."""
        host_cap_map = self._make_host_cap_map([
            (1, "RENC", 48, 128, 1000, {}),
            (2, "RENC", 48, 128, 1000, {}),
        ])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 32, "ram": 32, "disk": 100},
            {"type": "compute", "site": "RENC", "cores": 32, "ram": 32, "disk": 100},
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_compute_blocked_by_existing_sliver(self):
        """Existing sliver consumes capacity, blocking the new request."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "site": "RENC", "cores": 48, "ram": 64, "disk": 100}]

        existing_sliver = SliverRow(
            id=100, host_id=1, core=32, ram=64, disk=500,
            lease_start=dt(2025, 6, 30), lease_end=dt(2025, 7, 5)
        )

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[existing_sliver], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    def test_compute_fits_after_sliver_ends(self):
        """Existing sliver ends before the window starts — request fits."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "site": "RENC", "cores": 48, "ram": 64, "disk": 100}]

        existing_sliver = SliverRow(
            id=100, host_id=1, core=48, ram=128, disk=1000,
            lease_start=dt(2025, 6, 28), lease_end=dt(2025, 6, 30)
        )

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[existing_sliver], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_compute_with_components(self):
        """Compute request with GPU component requirement."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {"GPU-A100": 4})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100,
             "components": {"GPU-A100": 2}}
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_compute_component_insufficient(self):
        """Request needs 4 GPUs but host only has 2."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {"GPU-A100": 2})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100,
             "components": {"GPU-A100": 4}}
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    def test_compute_component_case_insensitive(self):
        """Component matching is case-insensitive."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {"GPU-A100": 4})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [
            {"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100,
             "components": {"gpu-a100": 2}}
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_siteless_compute_any_host(self):
        """Compute without site searches all hosts."""
        host_cap_map = self._make_host_cap_map([
            (1, "RENC", 16, 32, 100, {}),
            (2, "CLEM", 64, 128, 1000, {}),
        ])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "cores": 32, "ram": 64, "disk": 100}]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    # ── Link tests ──

    def test_link_fits(self):
        """Link request fits within available bandwidth."""
        link_cap_map = {
            ("CLEM", "RENC"): {"name": "link-1", "site_a": "CLEM", "site_b": "RENC",
                               "layer": "L2", "bandwidth_capacity": 100}
        }

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[{"type": "link", "site_a": "RENC", "site_b": "CLEM", "bandwidth": 25}],
            fp_requests=[],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map=link_cap_map, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_link_exceeded(self):
        """Link request exceeds remaining bandwidth due to existing sliver."""
        link_cap_map = {
            ("CLEM", "RENC"): {"name": "link-1", "site_a": "CLEM", "site_b": "RENC",
                               "layer": "L2", "bandwidth_capacity": 100}
        }
        net_sliver = NetSliverRow(
            id=200, bandwidth=80,
            lease_start=dt(2025, 6, 30), lease_end=dt(2025, 7, 5)
        )
        net_ifaces = {200: ["CLEM", "RENC"]}

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[{"type": "link", "site_a": "RENC", "site_b": "CLEM", "bandwidth": 25}],
            fp_requests=[],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map=link_cap_map, net_slivers_in_range=[net_sliver], net_sliver_interfaces=net_ifaces,
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    def test_link_no_capacity_entry(self):
        """Link request for a site pair with no capacity data → fail."""
        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[{"type": "link", "site_a": "RENC", "site_b": "STAR", "bandwidth": 10}],
            fp_requests=[],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    # ── Facility port tests ──

    def test_facility_port_fits(self):
        """Facility port VLAN request fits."""
        fp_cap_map = {
            ("RENC-Chameleon", "RENC", "sw1", "port1"): {
                "name": "RENC-Chameleon", "site": "RENC",
                "device_name": "sw1", "local_name": "port1",
                "vlan_range": "100-200", "total_vlans": 101
            }
        }

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[],
            fp_requests=[{"type": "facility_port", "name": "RENC-Chameleon", "site": "RENC", "vlans": 5}],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map=fp_cap_map, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_facility_port_vlans_exhausted(self):
        """Facility port VLAN request fails — too many VLANs in use."""
        fp_cap_map = {
            ("RENC-Chameleon", "RENC", "sw1", "port1"): {
                "name": "RENC-Chameleon", "site": "RENC",
                "device_name": "sw1", "local_name": "port1",
                "vlan_range": "100-102", "total_vlans": 3
            }
        }
        fp_ifaces = [
            FpIfaceRow("RENC-Chameleon", "RENC", "100", dt(2025, 6, 30), dt(2025, 7, 5)),
            FpIfaceRow("RENC-Chameleon", "RENC", "101", dt(2025, 6, 30), dt(2025, 7, 5)),
            FpIfaceRow("RENC-Chameleon", "RENC", "102", dt(2025, 6, 30), dt(2025, 7, 5)),
        ]

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[],
            fp_requests=[{"type": "facility_port", "name": "RENC-Chameleon", "site": "RENC", "vlans": 1}],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map=fp_cap_map, fp_iface_slivers=fp_ifaces
        )
        self.assertFalse(result)

    def test_facility_port_not_found(self):
        """Facility port name doesn't exist in capacity map."""
        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[],
            fp_requests=[{"type": "facility_port", "name": "NONEXISTENT", "site": "RENC", "vlans": 1}],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    # ── Multi-resource tests ──

    def test_compute_plus_link(self):
        """Combined compute + link request where both fit."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        link_cap_map = {
            ("CLEM", "RENC"): {"name": "link-1", "site_a": "CLEM", "site_b": "RENC",
                               "layer": "L2", "bandwidth_capacity": 100}
        }

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[{"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100}],
            link_requests=[{"type": "link", "site_a": "RENC", "site_b": "CLEM", "bandwidth": 25}],
            fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map=link_cap_map, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)

    def test_compute_fits_but_link_fails(self):
        """Compute fits but link doesn't — combined result should be False."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 64, 128, 1000, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[{"type": "compute", "site": "RENC", "cores": 16, "ram": 32, "disk": 100}],
            link_requests=[{"type": "link", "site_a": "RENC", "site_b": "STAR", "bandwidth": 25}],
            fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    # ── Duration / partial overlap tests ──

    def test_sliver_blocks_one_hour_in_window(self):
        """Existing sliver overlaps just one hour of the duration window — should still block."""
        host_cap_map = self._make_host_cap_map([(1, "RENC", 32, 64, 500, {})])
        hosts_by_site = self._make_hosts_by_site(host_cap_map)
        compute_requests = [{"type": "compute", "site": "RENC", "cores": 32, "ram": 64, "disk": 100}]

        # Sliver occupies full host, overlaps only the last hour of the 24h window
        existing_sliver = SliverRow(
            id=100, host_id=1, core=32, ram=64, disk=500,
            lease_start=dt(2025, 7, 1, 23), lease_end=dt(2025, 7, 3)
        )

        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=compute_requests, link_requests=[], fp_requests=[],
            host_cap_map=host_cap_map, hosts_by_site=hosts_by_site,
            slivers_in_range=[existing_sliver], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertFalse(result)

    # ── Empty requests ──

    def test_no_requests_returns_true(self):
        """No resource requests → window is trivially available."""
        result = DatabaseManager._check_window(
            window_start=dt(2025, 7, 1), window_end=dt(2025, 7, 2), duration=24,
            compute_requests=[], link_requests=[], fp_requests=[],
            host_cap_map={}, hosts_by_site={},
            slivers_in_range=[], comp_by_sliver={},
            link_cap_map={}, net_slivers_in_range=[], net_sliver_interfaces={},
            fp_cap_map={}, fp_iface_slivers=[]
        )
        self.assertTrue(result)


class TestEmptyFindSlotResult(unittest.TestCase):
    """Tests for _empty_find_slot_result helper."""

    def test_structure(self):
        result = DatabaseManager._empty_find_slot_result(dt(2025, 7, 1), dt(2025, 7, 15), 48)
        self.assertEqual(result["windows"], [])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["duration_hours"], 48)
        self.assertIn("search_start", result)
        self.assertIn("search_end", result)


if __name__ == '__main__':
    unittest.main()

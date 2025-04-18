import requests
import json
import os


class ReportsApi:
    def __init__(self, base_url: str, token_file: str):
        self.base_url = base_url.rstrip("/")
        self.token = self._load_token(token_file)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

    def _load_token(self, token_file: str) -> str:
        """
        Load bearer token from a JSON file with structure: { "id_token": "<token>" }
        """
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file '{token_file}' not found")

        with open(token_file, 'r') as f:
            data = json.load(f)

        token = data.get("id_token")
        if not token:
            raise ValueError("Missing 'id_token' field in token JSON file")
        return token
    
    def query_sites(self):
        """
        Query the /slices endpoint with optional filters.
        """
        url = f"{self.base_url}/sites"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch slices: {response.status_code} - {response.text}")    

    def query_slices(self, start_time: str = None, end_time: str = None, user_id: list[str] = None,
                     user_email: list[str] = None, project_id: list[str] = None, slice_id: list[str] = None,
                     slice_state: list[str] = None, sliver_id: list[str] = None, sliver_type: list[str] = None,
                     sliver_state: list[str] = None, component_type: list[str] = None,
                     component_model: list[str] = None, bdf: list[str] = None, vlan: list[str] = None,
                     ip_subnet: list[str] = None, site: list[str] = None, host: list[str] = None,
                     exclude_user_id: list[str] = None, exclude_user_email: list[str] = None,
                     exclude_project_id: list[str] = None, exclude_site: list[str] = None,
                     exclude_host: list[str] = None, page=0, per_page=100, fetch_all=True):
        """
        Fetch slices with optional filters. Supports fetching all pages or just one.

        :param start_time: Filter by start time (inclusive)
        :type start_time: str
        :param end_time: Filter by end time (inclusive)
        :type end_time: str
        :param user_id: Filter by user uuid
        :type user_id: List[str]
        :param user_email: Filter by user email
        :type user_email: List[str]
        :param project_id: Filter by project uuid
        :type project_id: List[str]
        :param slice_id: Filter by slice uuid
        :type slice_id: List[str]
        :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type slice_state: List[str]
        :param sliver_id: Filter by sliver uuid
        :type sliver_id: List[str]
        :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
        :type sliver_type: List[str]
        :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type sliver_state: List[str]
        :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
        :type component_type: List[str]
        :param component_model: Filter by component model
        :type component_model: List[str]
        :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
        :type bdf: List[str]
        :param vlan: Filter by VLAN associated with their sliver interfaces.
        :type vlan: List[str]
        :param ip_subnet: Filter by specified IP subnet
        :type ip_subnet: List[str]
        :param site: Filter by site
        :type site: List[str]
        :param host: Filter by host
        :type host: List[str]
        :param exclude_user_id: Exclude Users by IDs
        :type exclude_user_id: List[str]
        :param exclude_user_email: Exclude Users by emails
        :type exclude_user_email: List[str]
        :param exclude_project_id: Exclude projects
        :type exclude_project_id: List[str]
        :param exclude_site: Exclude sites
        :type exclude_site: List[str]
        :param exclude_host: Exclude hosts
        :type exclude_host: List[str]
        :param page: Page number for pagination. Default is 1.
        :type page: int
        :param per_page: Number of records per page. Default is 10.
        :type per_page: int
        :param fetch_all: If True, paginates until all results are fetched.
        :return: Dict with 'total' and 'data' keys.
        """
        all_slices = []
        total = 0
        url = f"{self.base_url}/slices"

        base_params = {
            "start_time": start_time,
            "end_time": end_time,
            "user_id": user_id,
            "user_email": user_email,
            "project_id": project_id,
            "slice_id": slice_id,
            "slice_state": slice_state,
            "sliver_id": sliver_id,
            "sliver_type": sliver_type,
            "sliver_state": sliver_state,
            "component_type": component_type,
            "component_model": component_model,
            "bdf": bdf,
            "vlan": vlan,
            "ip_subnet": ip_subnet,
            "site": site,
            "host": host,
            "exclude_user_id": exclude_user_id,
            "exclude_user_email": exclude_user_email,
            "exclude_project_id": exclude_project_id,
            "exclude_site": exclude_site,
            "exclude_host": exclude_host,
            "per_page": per_page  # page will be added per iteration
        }

        # Remove keys with None values
        filtered_params = {k: v for k, v in base_params.items() if v is not None}

        while True:
            filtered_params["page"] = page
            response = requests.get(url, headers=self.headers, params=filtered_params)

            if response.status_code == 200:
                response = response.json()
            else:
                raise Exception(f"Failed to fetch slices: {response.status_code} - {response.text}")

            if page == 0:
                total = response.get("total")

            data = response.get("data", [])
            all_slices.extend(data)

            if not fetch_all or not data or len(all_slices) >= total:
                break

            page += 1

        return {
            "total": total,
            "data": all_slices
        }

    def query_slivers(self, start_time: str = None, end_time: str = None, user_id: list[str] = None,
                      user_email: list[str] = None, project_id: list[str] = None, slice_id: list[str] = None,
                      slice_state: list[str] = None, sliver_id: list[str] = None, sliver_type: list[str] = None,
                      sliver_state: list[str] = None, component_type: list[str] = None,
                      component_model: list[str] = None, bdf: list[str] = None, vlan: list[str] = None,
                      ip_subnet: list[str] = None, site: list[str] = None, host: list[str] = None,
                      exclude_user_id: list[str] = None, exclude_user_email: list[str] = None,
                      exclude_project_id: list[str] = None, exclude_site: list[str] = None,
                      exclude_host: list[str] = None, page=0, per_page=100, fetch_all=True):
        """
        Fetch slivers with optional filters. Supports fetching all pages or just one.

        :param start_time: Filter by start time (inclusive)
        :type start_time: str
        :param end_time: Filter by end time (inclusive)
        :type end_time: str
        :param user_id: Filter by user uuid
        :type user_id: List[str]
        :param user_email: Filter by user email
        :type user_email: List[str]
        :param project_id: Filter by project uuid
        :type project_id: List[str]
        :param slice_id: Filter by slice uuid
        :type slice_id: List[str]
        :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type slice_state: List[str]
        :param sliver_id: Filter by sliver uuid
        :type sliver_id: List[str]
        :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
        :type sliver_type: List[str]
        :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type sliver_state: List[str]
        :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
        :type component_type: List[str]
        :param component_model: Filter by component model
        :type component_model: List[str]
        :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
        :type bdf: List[str]
        :param vlan: Filter by VLAN associated with their sliver interfaces.
        :type vlan: List[str]
        :param ip_subnet: Filter by specified IP subnet
        :type ip_subnet: List[str]
        :param site: Filter by site
        :type site: List[str]
        :param host: Filter by host
        :type host: List[str]
        :param exclude_user_id: Exclude Users by IDs
        :type exclude_user_id: List[str]
        :param exclude_user_email: Exclude Users by emails
        :type exclude_user_email: List[str]
        :param exclude_project_id: Exclude projects
        :type exclude_project_id: List[str]
        :param exclude_site: Exclude sites
        :type exclude_site: List[str]
        :param exclude_host: Exclude hosts
        :type exclude_host: List[str]
        :param page: Page number for pagination. Default is 1.
        :type page: int
        :param per_page: Number of records per page. Default is 10.
        :type per_page: int

        :param fetch_all: If True, paginates until all results are fetched.
        :return: Dict with 'total' and 'data' keys.
        """
        all_slivers = []
        total = 0
        url = f"{self.base_url}/slivers"

        base_params = {
            "start_time": start_time,
            "end_time": end_time,
            "user_id": user_id,
            "user_email": user_email,
            "project_id": project_id,
            "slice_id": slice_id,
            "slice_state": slice_state,
            "sliver_id": sliver_id,
            "sliver_type": sliver_type,
            "sliver_state": sliver_state,
            "component_type": component_type,
            "component_model": component_model,
            "bdf": bdf,
            "vlan": vlan,
            "ip_subnet": ip_subnet,
            "site": site,
            "host": host,
            "exclude_user_id": exclude_user_id,
            "exclude_user_email": exclude_user_email,
            "exclude_project_id": exclude_project_id,
            "exclude_site": exclude_site,
            "exclude_host": exclude_host,
            "per_page": per_page  # page will be added per iteration
        }

        # Remove keys with None values
        filtered_params = {k: v for k, v in base_params.items() if v is not None}

        while True:
            filtered_params["page"] = page
            response = requests.get(url, headers=self.headers, params=filtered_params)

            if response.status_code == 200:
                response = response.json()
            else:
                raise Exception(f"Failed to fetch slices: {response.status_code} - {response.text}")

            if page == 0:
                total = response.get("total")

            data = response.get("data", [])
            all_slivers.extend(data)

            if not fetch_all or not data or len(all_slivers) >= total:
                break

            page += 1

        return {
            "total": total,
            "data": all_slivers
        }

    def query_users(self, start_time: str = None, end_time: str = None, user_id: list[str] = None,
                    user_email: list[str] = None, project_id: list[str] = None, slice_id: list[str] = None,
                    slice_state: list[str] = None, sliver_id: list[str] = None, sliver_type: list[str] = None,
                    sliver_state: list[str] = None, component_type: list[str] = None,
                    component_model: list[str] = None, bdf: list[str] = None, vlan: list[str] = None,
                    ip_subnet: list[str] = None, site: list[str] = None, host: list[str] = None,
                    exclude_user_id: list[str] = None, exclude_user_email: list[str] = None,
                    exclude_project_id: list[str] = None, exclude_site: list[str] = None,
                    exclude_host: list[str] = None, page=0, per_page=100, fetch_all=True):
        """
        Fetch users with optional filters. Supports fetching all pages or just one.

        :param start_time: Filter by start time (inclusive)
        :type start_time: str
        :param end_time: Filter by end time (inclusive)
        :type end_time: str
        :param user_id: Filter by user uuid
        :type user_id: List[str]
        :param user_email: Filter by user email
        :type user_email: List[str]
        :param project_id: Filter by project uuid
        :type project_id: List[str]
        :param slice_id: Filter by slice uuid
        :type slice_id: List[str]
        :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type slice_state: List[str]
        :param sliver_id: Filter by sliver uuid
        :type sliver_id: List[str]
        :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
        :type sliver_type: List[str]
        :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type sliver_state: List[str]
        :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
        :type component_type: List[str]
        :param component_model: Filter by component model
        :type component_model: List[str]
        :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
        :type bdf: List[str]
        :param vlan: Filter by VLAN associated with their sliver interfaces.
        :type vlan: List[str]
        :param ip_subnet: Filter by specified IP subnet
        :type ip_subnet: List[str]
        :param site: Filter by site
        :type site: List[str]
        :param host: Filter by host
        :type host: List[str]
        :param exclude_user_id: Exclude Users by IDs
        :type exclude_user_id: List[str]
        :param exclude_user_email: Exclude Users by emails
        :type exclude_user_email: List[str]
        :param exclude_project_id: Exclude projects
        :type exclude_project_id: List[str]
        :param exclude_site: Exclude sites
        :type exclude_site: List[str]
        :param exclude_host: Exclude hosts
        :type exclude_host: List[str]
        :param page: Page number for pagination. Default is 1.
        :type page: int
        :param per_page: Number of records per page. Default is 10.
        :type per_page: int

        :param fetch_all: If True, paginates until all results are fetched.
        :return: Dict with 'total' and 'data' keys.
        """
        all_users = []
        total = 0
        url = f"{self.base_url}/users"

        base_params = {
            "start_time": start_time,
            "end_time": end_time,
            "user_id": user_id,
            "user_email": user_email,
            "project_id": project_id,
            "slice_id": slice_id,
            "slice_state": slice_state,
            "sliver_id": sliver_id,
            "sliver_type": sliver_type,
            "sliver_state": sliver_state,
            "component_type": component_type,
            "component_model": component_model,
            "bdf": bdf,
            "vlan": vlan,
            "ip_subnet": ip_subnet,
            "site": site,
            "host": host,
            "exclude_user_id": exclude_user_id,
            "exclude_user_email": exclude_user_email,
            "exclude_project_id": exclude_project_id,
            "exclude_site": exclude_site,
            "exclude_host": exclude_host,
            "per_page": per_page  # page will be added per iteration
        }

        # Remove keys with None values
        filtered_params = {k: v for k, v in base_params.items() if v is not None}

        while True:
            filtered_params["page"] = page
            response = requests.get(url, headers=self.headers, params=filtered_params)

            if response.status_code == 200:
                response = response.json()
            else:
                raise Exception(f"Failed to fetch slices: {response.status_code} - {response.text}")

            if page == 0:
                total = response.get("total")

            data = response.get("data", [])
            all_users.extend(data)

            if not fetch_all or not data or len(all_users) >= total:
                break

            page += 1

        return {
            "total": total,
            "data": all_users
        }

    def query_projects(self, start_time: str = None, end_time: str = None, user_id: list[str] = None,
                       user_email: list[str] = None, project_id: list[str] = None, slice_id: list[str] = None,
                       slice_state: list[str] = None, sliver_id: list[str] = None, sliver_type: list[str] = None,
                       sliver_state: list[str] = None, component_type: list[str] = None,
                       component_model: list[str] = None, bdf: list[str] = None, vlan: list[str] = None,
                       ip_subnet: list[str] = None, site: list[str] = None, host: list[str] = None,
                       exclude_user_id: list[str] = None, exclude_user_email: list[str] = None,
                       exclude_project_id: list[str] = None, exclude_site: list[str] = None,
                       exclude_host: list[str] = None, page=0, per_page=100, fetch_all=True):
        """
        Fetch projects with optional filters. Supports fetching all pages or just one.

        :param start_time: Filter by start time (inclusive)
        :type start_time: str
        :param end_time: Filter by end time (inclusive)
        :type end_time: str
        :param user_id: Filter by user uuid
        :type user_id: List[str]
        :param user_email: Filter by user email
        :type user_email: List[str]
        :param project_id: Filter by project uuid
        :type project_id: List[str]
        :param slice_id: Filter by slice uuid
        :type slice_id: List[str]
        :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
        :type slice_state: List[str]
        :param sliver_id: Filter by sliver uuid
        :type sliver_id: List[str]
        :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
        :type sliver_type: List[str]
        :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
        :type sliver_state: List[str]
        :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
        :type component_type: List[str]
        :param component_model: Filter by component model
        :type component_model: List[str]
        :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
        :type bdf: List[str]
        :param vlan: Filter by VLAN associated with their sliver interfaces.
        :type vlan: List[str]
        :param ip_subnet: Filter by specified IP subnet
        :type ip_subnet: List[str]
        :param site: Filter by site
        :type site: List[str]
        :param host: Filter by host
        :type host: List[str]
        :param exclude_user_id: Exclude Users by IDs
        :type exclude_user_id: List[str]
        :param exclude_user_email: Exclude Users by emails
        :type exclude_user_email: List[str]
        :param exclude_project_id: Exclude projects
        :type exclude_project_id: List[str]
        :param exclude_site: Exclude sites
        :type exclude_site: List[str]
        :param exclude_host: Exclude hosts
        :type exclude_host: List[str]
        :param page: Page number for pagination. Default is 1.
        :type page: int
        :param per_page: Number of records per page. Default is 10.
        :type per_page: int

        :param fetch_all: If True, paginates until all results are fetched.
        :return: Dict with 'total' and 'data' keys.
        """
        all_projects = []
        total = 0
        url = f"{self.base_url}/projects"

        base_params = {
            "start_time": start_time,
            "end_time": end_time,
            "user_id": user_id,
            "user_email": user_email,
            "project_id": project_id,
            "slice_id": slice_id,
            "slice_state": slice_state,
            "sliver_id": sliver_id,
            "sliver_type": sliver_type,
            "sliver_state": sliver_state,
            "component_type": component_type,
            "component_model": component_model,
            "bdf": bdf,
            "vlan": vlan,
            "ip_subnet": ip_subnet,
            "site": site,
            "host": host,
            "exclude_user_id": exclude_user_id,
            "exclude_user_email": exclude_user_email,
            "exclude_project_id": exclude_project_id,
            "exclude_site": exclude_site,
            "exclude_host": exclude_host,
            "per_page": per_page  # page will be added per iteration
        }

        # Remove keys with None values
        filtered_params = {k: v for k, v in base_params.items() if v is not None}

        while True:
            filtered_params["page"] = page
            response = requests.get(url, headers=self.headers, params=filtered_params)

            if response.status_code == 200:
                response = response.json()
            else:
                raise Exception(f"Failed to fetch slices: {response.status_code} - {response.text}")

            if page == 0:
                total = response.get("total")

            data = response.get("data", [])
            all_projects.extend(data)

            if not fetch_all or not data or len(all_projects) >= total:
                break

            page += 1

        return {
            "total": total,
            "data": all_projects
        }
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

    def query_slices(self, start_time=None, end_time=None, user_id=None, user_email=None,
                    project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None,
                    sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None,
                    ip_subnet=None, site=None, host=None, page=0, per_page=100, fetch_all=True):
        """
        Fetch slices with optional filters. Supports fetching all pages or just one.

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

    def query_slivers(self, start_time=None, end_time=None, user_id=None, user_email=None,
                      project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None,
                      sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None,
                      ip_subnet=None, site=None, host=None, page=0, per_page=100, fetch_all=True):
        """
        Fetch slivers with optional filters. Supports fetching all pages or just one.

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

    def query_users(self, start_time=None, end_time=None, user_id=None, user_email=None,
                      project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None,
                      sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None,
                      ip_subnet=None, site=None, host=None, page=0, per_page=100, fetch_all=True):
        """
        Fetch users with optional filters. Supports fetching all pages or just one.

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

    def query_projects(self, start_time=None, end_time=None, user_id=None, user_email=None,
                    project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None,
                    sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None,
                    ip_subnet=None, site=None, host=None, page=0, per_page=100, fetch_all=True):
            """
            Fetch projects with optional filters. Supports fetching all pages or just one.

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
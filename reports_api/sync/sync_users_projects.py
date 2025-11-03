#!/usr/bin/env python3
# MIT License
#
# Copyright (component) 2025 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)
import argparse
import logging
import traceback
import yaml
from pathlib import Path

from logging.handlers import RotatingFileHandler

import requests
from dateutil.parser import isoparse

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager


class UserSyncScript:
    def __init__(self, endpoint: str, token: str, logger: logging.Logger):
        self.endpoint = endpoint
        self.token = token
        self.logger = logger

    @property
    def headers(self):
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def fetch_user_list(self):
        try:
            url = f"{self.endpoint}/core-api-metrics/people"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            self.logger.error(f"Error fetching user list: {e}")
            traceback.print_exc()
            return []

    def fetch_user_detail(self, uuid):
        try:
            url = f"{self.endpoint}/core-api-metrics/people-details/{uuid}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])[0]
        except Exception as e:
            self.logger.error(f"Error fetching user details for {uuid}: {e}")
            traceback.print_exc()
            return None

    def fetch_memberships_for_user(self, uuid: str):
        try:
            url = f"{self.endpoint}/core-api-metrics/events/people-membership/{uuid}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            self.logger.error(f"Error fetching membership events for user {uuid}: {e}")
            traceback.print_exc()
            return []

    def sync_users(self, db_mgr):
        users = self.fetch_user_list()
        if not users:
            self.logger.warning("No users retrieved from API.")
            return

        updated_count = 0
        for entry in users:
            uuid = entry.get("uuid")
            detail = self.fetch_user_detail(uuid)
            if not detail:
                continue

            try:
                # Add or update user
                print(f'User: {detail.get("bastion_login")}')
                user_id = db_mgr.add_or_update_user(
                    user_uuid=detail.get("uuid"),
                    user_email=detail.get("email"),
                    active=detail.get("active"),
                    name=detail.get("name"),
                    affiliation=detail.get("affiliation"),
                    registered_on=isoparse(detail["registered_on"]) if detail.get("registered_on") else None,
                    last_updated=isoparse(detail["last_updated"]) if detail.get("last_updated") else None,
                    google_scholar=detail.get("google_scholar"),
                    scopus=detail.get("scopus"),
                    bastion_login=detail.get("bastion_login")
                )

                # Fetch and store memberships
                memberships = self.fetch_memberships_for_user(uuid)
                for m in memberships:
                    project_id = db_mgr.add_or_update_project(
                        project_uuid=m["project_uuid"]
                    )

                    db_mgr.add_or_update_membership(
                        user_id=user_id,
                        project_id=project_id,
                        start_time=isoparse(m["added_date"]) if m.get("added_date") else None,
                        end_time=isoparse(m["removed_date"]) if m.get("removed_date") else None,
                        membership_type=m.get("membership_type"),
                        active=m.get("removed_date") is None
                    )

                updated_count += 1
                self.logger.info(f"Updated user + memberships: {detail.get('email')} ({uuid})")
            except Exception as e:
                self.logger.error(f"Failed to update user {uuid}: {e}")
                traceback.print_exc()

        self.logger.info(f"Total users updated (incl. memberships): {updated_count}")


class ProjectSyncScript:
    def __init__(self, endpoint: str, token: str, logger: logging.Logger):
        self.endpoint = endpoint
        self.token = token
        self.logger = logger

    @property
    def headers(self):
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def fetch_project_list(self):
        try:
            url = f"{self.endpoint}/core-api-metrics/projects"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            self.logger.error(f"Error fetching project list: {e}")
            traceback.print_exc()
            return []

    def fetch_project_detail(self, uuid):
        try:
            url = f"{self.endpoint}/core-api-metrics/projects-details/{uuid}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])[0]
        except Exception as e:
            self.logger.error(f"Error fetching details for project {uuid}: {e}")
            traceback.print_exc()
            return None

    def sync_projects(self, db_mgr):
        projects = self.fetch_project_list()
        if not projects:
            self.logger.warning("No projects retrieved from API.")
            return

        updated_count = 0
        for entry in projects:
            uuid = entry.get("uuid")
            detail = self.fetch_project_detail(uuid)
            if not detail:
                continue

            try:
                db_mgr.add_or_update_project(
                    project_uuid=detail.get("uuid"),
                    project_name=detail.get("name"),
                    project_type=detail.get("project_type"),
                    active=detail.get("active"),
                    created_date=isoparse(detail["created_date"]) if detail.get("created_date") else None,
                    expires_on=isoparse(detail["expires_on"]) if detail.get("expires_on") else None,
                    retired_date=isoparse(detail["retired_date"]) if detail.get("retired_date") else None,
                    last_updated=isoparse(detail["last_updated"]) if detail.get("last_updated") else None
                )
                updated_count += 1
                self.logger.info(f"Updated project: {detail.get('name')} ({uuid})")
            except Exception as e:
                self.logger.error(f"Failed to update project {uuid}: {e}")
                traceback.print_exc()

        self.logger.info(f"Total projects updated: {updated_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync users and projects from FABRIC Core API to Reports DB")
    parser.add_argument("--config", required=True, help="Path to YAML config file with core_api.host and token")

    args = parser.parse_args()
    config_path = Path(args.config)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    core_api_cfg = config.get("core_api", {})
    if not core_api_cfg.get("enable", False):
        print("core_api.enable is False. Skipping sync.")
        exit(0)

    endpoint = core_api_cfg.get("host", "").rstrip("/")
    token = core_api_cfg.get("token")
    if not endpoint or not token:
        raise ValueError("core_api.host and core_api.token must be set in config file.")

    logger = logging.getLogger("sync_all")
    file_handler = RotatingFileHandler('./sync_all.log', backupCount=5, maxBytes=1_000_000)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(), file_handler]
    )

    global_obj = GlobalsSingleton.get()
    db_mgr = DatabaseManager(
        user=global_obj.config.database_config.get("db-user"),
        password=global_obj.config.database_config.get("db-password"),
        database=global_obj.config.database_config.get("db-name"),
        db_host=global_obj.config.database_config.get("db-host"),
        logger=logger
    )

    logger.info("Starting sync for users and projects...")
    ProjectSyncScript(endpoint, token, logger).sync_projects(db_mgr)
    UserSyncScript(endpoint, token, logger).sync_users(db_mgr)
    logger.info("Completed sync.")
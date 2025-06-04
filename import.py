#!/usr/bin/env python3
#
# Copyright (c) 2020 FABRIC Testbed
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
import json
import logging
import os
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager
from reports_api.response_code.cors_response import cors_500
from reports_api.response_code.slice_sliver_states import SliceState, SliverStates
from reports_api.swagger_server.models import Slice, Sliver


class ImportScript:
    """
    CLI interface to load slice JSON files from a directory and push to reports db via ReportsApi.
    """

    def __init__(self, slices_dir: str):
        self.logger = logging.getLogger("import")
        file_handler = RotatingFileHandler('./import.log', backupCount=5, maxBytes=50000)
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s",
                            handlers=[logging.StreamHandler(), file_handler])

        self.slices_dir = Path(slices_dir)
        if not self.slices_dir.exists():
            raise FileNotFoundError(f"Slice directory not found: {slices_dir}")

    def _create_temp_token_file(self, token: str) -> str:
        import tempfile
        fd, path = tempfile.mkstemp(prefix="token_", suffix=".json")
        with os.fdopen(fd, 'w') as f:
            f.write(f'{{"id_token": "{token}"}}')
        return path

    def import_slices(self):
        ignored_slices = 0
        imported_slices = 0
        try:
            sorted_files = sorted(self.slices_dir.glob("slice_*.json"), key=lambda f: f.stat().st_mtime)
            start_index = 0
            for i in range(start_index, len(sorted_files)):
                slice_file = sorted_files[i]
                start_index = i
                try:
                    with open(slice_file, 'r') as f:
                        slice_data = json.load(f)
                        slice_guid = slice_data.get("slice_id")
                        slivers = slice_data.get("slivers")

                        lease_start_str = slice_data.get("lease_start", None)
                        lease_end_str = slice_data.get("lease_end", None)

                        has_no_lease_end = lease_end_str is None
                        has_no_lease_start = lease_start_str is None
                        if has_no_lease_start or has_no_lease_end:
                            continue

                        if not slivers:
                            continue

                        state = SliceState(slice_data.get("state")).name

                        slice_payload = {
                            "project_id": slice_data.get("project_id"),
                            "project_name": slice_data.get("project_name"),
                            "user_id": slice_data.get("user_id"),
                            "user_email": slice_data.get("user_email"),
                            "slice_id": slice_guid,
                            "slice_name": slice_data.get("slice_name"),
                            "state": state,
                            "lease_start": lease_start_str,
                            "lease_end": lease_end_str
                        }

                        cleaned_slice_dict = {k: v for k, v in slice_payload.items() if v is not None}
                        body = Slice.from_dict(cleaned_slice_dict)

                        status = self.slices_slice_id_post(slice_id=slice_guid, body=body)
                        if not status:
                            ignored_slices += 1
                            self.logger.info(f"Slice {slice_guid} already exists. Skipping import.")
                            continue

                        self.logger.info(f"Importing Index: {start_index} slice: {slice_guid}")

                        for sliver in slice_data.get("slivers", []):
                            sliver["lease_end"] = lease_end_str
                            sliver["lease_start"] = lease_start_str
                            sliver["sliver_type"] = sliver["type"]
                            sliver.pop("type")
                            if "components" in sliver:
                                for c in sliver["components"]:
                                    c["component_id"] = c["component_guid"]
                                    c.pop("component_guid")
                                    c["sliver_id"] = c["sliver_guid"]
                                    c.pop("sliver_guid")
                                    
                                sliver["components"] = {
                                    "total": len(sliver["components"]),
                                    "data": sliver["components"]
                                }
                            sliver_payload = {k: v for k, v in sliver.items() if v is not None}
                            sl_body = Sliver.from_dict(sliver_payload)
                            self.slivers_slice_id_sliver_id_post(slice_id=slice_guid, sliver_id=sliver.get("sliver_id"),
                                                                 body=sl_body)

                        imported_slices += 1
                except Exception as e:
                    self.logger.error(f"Failed to index: {i} import: {slice_file} error: {e}")
                    traceback.print_exc()

                self.logger.info(f"Total slices ignored: {ignored_slices}")
                self.logger.info(f"Total slices imported: {imported_slices}")

        except Exception as e:
            self.logger.error(f"Exception occurred during import: {e}")
            traceback.print_exc()

    def slices_slice_id_post(self, slice_id, body: Slice) -> bool:  # noqa: E501
        """Create/Update a slice

        Create a Slice # noqa: E501

        :param slice_id:
        :type slice_id:
        :param body: Create new Slice
        :type body: dict | bytes

        :rtype: Status200OkNoContent
        """
        logger = GlobalsSingleton.get().log
        try:
            logger.debug("Processing - slices_slice_id_post")

            global_obj = GlobalsSingleton.get()
            db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                     password=global_obj.config.database_config.get("db-password"),
                                     database=global_obj.config.database_config.get("db-name"),
                                     db_host=global_obj.config.database_config.get("db-host"),
                                     logger=logger)
            
            exists = db_mgr.get_slice_by_slice_id(slice_id=body.slice_id)
            # Check if slice already exists
            if exists:
                logger.debug(f"Slice {body.slice_id} already exists. Skipping import.")
                return False

            p_id = db_mgr.add_or_update_project(project_uuid=body.project_id, project_name=body.project_name)
            u_id = db_mgr.add_or_update_user(user_uuid=body.user_id, user_email=body.user_email)

            db_mgr.add_or_update_slice(project_id=p_id, user_id=u_id, slice_guid=body.slice_id,
                                       slice_name=body.slice_name, state=SliceState.translate(body.state),
                                       lease_start=body.lease_start, lease_end=body.lease_end)

            logger.debug("Processed - slices_slice_id_post")
            return True
        except Exception as exc:
            details = 'Oops! something went wrong with slices_slice_id_post(): {0}'.format(exc)
            logger.error(details)
            logger.error(traceback.format_exc())
            return False

    def slivers_slice_id_sliver_id_post(self, body: Sliver, slice_id: str, sliver_id: str):  # noqa: E501
        """Create/Update Sliver

        Create/Update Sliver. # noqa: E501

        :param body: Create/Modify sliver
        :type body: dict | bytes
        :param slice_id:
        :type slice_id:
        :param sliver_id:
        :type sliver_id:

        :rtype: Status200OkNoContent
        """
        logger = GlobalsSingleton.get().log
        try:
            logger.debug("Processing - slivers_slice_id_sliver_id_post")

            global_obj = GlobalsSingleton.get()
            db_mgr = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                                     password=global_obj.config.database_config.get("db-password"),
                                     database=global_obj.config.database_config.get("db-name"),
                                     db_host=global_obj.config.database_config.get("db-host"),
                                     logger=logger)

            p_id = db_mgr.add_or_update_project(project_uuid=body.project_id, project_name=body.project_name)
            u_id = db_mgr.add_or_update_user(user_uuid=body.user_id, user_email=body.user_email)

            s_id = db_mgr.add_or_update_slice(project_id=p_id, user_id=u_id, slice_guid=body.slice_id,
                                              slice_name=body.slice_name, state=None,
                                              lease_start=body.lease_start, lease_end=body.lease_end)
            if body.site:
                site_id = db_mgr.add_or_update_site(site_name=body.site)
            else:
                site_id = None

            if body.host:
                host_id = db_mgr.add_or_update_host(host_name=body.host, site_id=site_id)
            else:
                host_id = None

            sl_id = db_mgr.add_or_update_sliver(project_id=p_id, user_id=u_id, slice_id=s_id, site_id=site_id,
                                                host_id=host_id, sliver_guid=sliver_id, lease_start=body.lease_start,
                                                lease_end=body.lease_end, state=SliverStates.translate(body.state),
                                                ip_subnet=body.ip_subnet, core=body.core, ram=body.ram, disk=body.disk,
                                                image=body.image, bandwidth=body.bandwidth, sliver_type=body.sliver_type,
                                                error=body.error)
            if body.components and body.components.data:
                for c in body.components.data:
                    db_mgr.add_or_update_component(sliver_id=sl_id, component_guid=c.component_id,
                                                   component_type=c.type, model=c.model, bdfs=c.bdfs,
                                                   component_node_id=c.component_node_id, node_id=c.node_id)

            if body.interfaces and body.interfaces.data:
                for ifc in body.interfaces.data:
                    db_mgr.add_or_update_interface(sliver_id=sl_id, interface_guid=ifc.interface_id, name=ifc.name,
                                                   local_name=ifc.local_name, device_name=ifc.device_name, bdf=ifc.bdf,
                                                   vlan=ifc.vlan, site_id=site_id)

        except Exception as exc:
            details = 'Oops! something went wrong with slivers_slice_id_sliver_id_post(): {0}'.format(exc)
            logger.error(details)
            logger.error(traceback.format_exc())
            return cors_500(details=details)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import JSON slice data to Reports API")
    parser.add_argument("--slices_dir", default="./exported_slices", help="Directory containing exported slice JSON files")

    args = parser.parse_args()
    importer = ImportScript(slices_dir=args.slices_dir)
    importer.import_slices()

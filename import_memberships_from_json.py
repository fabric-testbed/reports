import logging
import os
import json
import argparse
from datetime import datetime
from logging.handlers import RotatingFileHandler

from reports_api.common.globals import GlobalsSingleton
from reports_api.database.db_manager import DatabaseManager


def import_memberships(data_dir):
    logger = logging.getLogger("import")
    file_handler = RotatingFileHandler('./import.log', backupCount=5, maxBytes=50000)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(), file_handler])

    logger = GlobalsSingleton.get().log
    logger.debug("Processing - slices_slice_id_post")

    global_obj = GlobalsSingleton.get()
    db = DatabaseManager(user=global_obj.config.database_config.get("db-user"),
                         password=global_obj.config.database_config.get("db-password"),
                         database=global_obj.config.database_config.get("db-name"),
                         db_host=global_obj.config.database_config.get("db-host"),
                         logger=logger)

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(data_dir, filename)

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            verb = data.get("csel_eventdetail_verb")
            if verb not in {"modify-add", "modify-remove"}:
                continue

            timestamp_str = data.get("csel_timestamp")
            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

            user_uuid = data.get("csel_eventdetail_attr_value", "").replace("usr:", "")
            project_uuid = data.get("csel_identifier_prj_uuid")

            user_id = db.get_user_id_by_uuid(user_uuid)
            project_id = db.get_project_id_by_uuid(project_uuid)

            if not user_id or not project_id:
                print(f"[WARN] Could not resolve IDs for user/project in: {file_path}")
                continue

            if verb == "modify-add":
                db.add_or_update_membership(
                    user_id=user_id,
                    project_id=project_id,
                    start_time=ts,
                    end_time=None,
                    membership_type="member",
                    active=True
                )
                print(f"[ADD] {user_uuid} -> {project_uuid} @ {ts}")

            elif verb == "modify-remove":
                membership = db.get_active_membership(user_id=user_id, project_id=project_id)

                if not membership:
                    print(f"[WARN] No active membership to remove for {user_uuid} in {project_uuid}")
                    continue

                db.add_or_update_membership(
                    user_id=user_id,
                    project_id=project_id,
                    start_time=membership.start_time,
                    end_time=ts,
                    membership_type=membership.membership_type,
                    active=False
                )
                print(f"[REMOVE] {user_uuid} -> {project_uuid} @ {ts}")

        except Exception as e:
            print(f"[ERROR] {file_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import membership events from cs_event_data JSON files.")
    parser.add_argument("data_dir", help="Path to the cs_event_data directory")

    args = parser.parse_args()
    import_memberships(args.data_dir)

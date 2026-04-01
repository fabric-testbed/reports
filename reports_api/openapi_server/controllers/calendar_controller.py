import connexion

from reports_api.response_code import calendar_controller as rc
from reports_api.response_code.cors_response import cors_400


def calendar_get(start_time, end_time, interval=None, site=None, host=None,
                 exclude_site=None, exclude_host=None):  # noqa: E501
    """Get resource availability calendar

    Retrieve resource availability calendar showing capacity and allocation over time slots. # noqa: E501

    :param start_time: Start time for the calendar range (required)
    :type start_time: str
    :param end_time: End time for the calendar range (required)
    :type end_time: str
    :param interval: Time interval for each slot (default: day)
    :type interval: str
    :param site: Filter by site
    :type site: List[str]
    :param host: Filter by host
    :type host: List[str]
    :param exclude_site: Exclude sites
    :type exclude_site: List[str]
    :param exclude_host: Exclude hosts
    :type exclude_host: List[str]

    :rtype: dict
    """
    return rc.calendar_get(start_time=start_time, end_time=end_time, interval=interval,
                           site=site, host=host, exclude_site=exclude_site, exclude_host=exclude_host)


def calendar_find_slot(body):  # noqa: E501
    """Find available time slots for a resource request

    Find the earliest time windows where all requested resources are simultaneously available. # noqa: E501

    :param body: Resource request payload
    :type body: dict

    :rtype: dict
    """
    if connexion.request.is_json:
        body = connexion.request.get_json()
    return rc.calendar_find_slot(body=body)


def hosts_host_name_capacity_post(host_name, body):  # noqa: E501
    """Create/Update host capacity

    Create or update host capacity data. # noqa: E501

    :param host_name: Host name
    :type host_name: str
    :param body: Capacity payload
    :type body: dict

    :rtype: Status200OkNoContent
    """
    if connexion.request.is_json:
        body = connexion.request.get_json()
    if not body or not body.get("site"):
        return cors_400(details="'site' is required in the request body")
    return rc.hosts_host_name_capacity_post(host_name=host_name, body=body)


def links_capacity_post(body):  # noqa: E501
    """Create/Update link capacity

    Create or update link capacity data. # noqa: E501

    :param body: Capacity payload
    :type body: dict

    :rtype: Status200OkNoContent
    """
    if connexion.request.is_json:
        body = connexion.request.get_json()
    if not body or not body.get("name") or not body.get("site_a") or not body.get("site_b") or not body.get("layer"):
        return cors_400(details="'name', 'site_a', 'site_b', and 'layer' are required in the request body")
    return rc.links_capacity_post(body=body)


def facility_ports_capacity_post(body):  # noqa: E501
    """Create/Update facility port capacity

    Create or update facility port capacity data. # noqa: E501

    :param body: Capacity payload
    :type body: dict

    :rtype: Status200OkNoContent
    """
    if connexion.request.is_json:
        body = connexion.request.get_json()
    if not body or not body.get("name") or not body.get("site") or not body.get("device_name") or not body.get("local_name"):
        return cors_400(details="'name', 'site', 'device_name', and 'local_name' are required in the request body")
    return rc.facility_ports_capacity_post(body=body)

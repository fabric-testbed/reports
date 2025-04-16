from analytics_api.response_code import hosts_controller as rc


def hosts_get(site=None):  # noqa: E501
    """Get hosts

    Retrieve a list of hosts. # noqa: E501

    :param site: Filter by site
    :type site: str

    :rtype: Sites
    """
    return rc.hosts_get(site=site)

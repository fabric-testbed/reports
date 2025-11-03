from reports_api.response_code import hosts_controller as rc


def hosts_get(site=None, exclude_site=None):  # noqa: E501
    """Get hosts

    Retrieve a list of hosts. # noqa: E501

    :param site: Filter by site
    :type site: List[str]

    :param exclude_site: Exclude sites
    :type exclude_site: List[str]

    :rtype: Sites
    """
    return rc.hosts_get(site=site, exclude_site=exclude_site)

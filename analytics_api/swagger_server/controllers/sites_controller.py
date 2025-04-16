from analytics_api.response_code import sites_controller as rc


def sites_get():  # noqa: E501
    """Get sites

    Retrieve a list of sites. # noqa: E501


    :rtype: Sites
    """
    return rc.sites_get()

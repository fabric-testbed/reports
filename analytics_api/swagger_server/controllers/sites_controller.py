from analytics_api.swagger_server.models.sites import Sites  # noqa: E501
from analytics_api.response_code import sites_controller as rc


def sites_get():  # noqa: E501
    """Get sites

    Retrieve a list of sites. # noqa: E501


    :rtype: Sites
    """
    return rc.sites_get()

import connexion
import six

from analytics_api.swagger_server.models.sites import Sites  # noqa: E501
from analytics_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from analytics_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from analytics_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from analytics_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from analytics_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from analytics_api.swagger_server import util


def sites_get():  # noqa: E501
    """Get sites

    Retrieve a list of sites. # noqa: E501


    :rtype: Sites
    """
    return 'do some magic!'

import connexion
import six

from analytics_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from analytics_api.swagger_server.models.version import Version  # noqa: E501
from analytics_api.swagger_server import util
from analytics_api.swagger_server.response import version_controller as rc


def version_get():  # noqa: E501
    """Version

    Version # noqa: E501


    :rtype: Version
    """
    return 'do some magic!'

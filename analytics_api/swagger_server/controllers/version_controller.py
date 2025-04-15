from analytics_api.swagger_server.models.version import Version  # noqa: E501
from analytics_api.response_code import version_controller as rc


def version_get():  # noqa: E501
    """Version

    Version # noqa: E501


    :rtype: Version
    """
    return rc.version_get()

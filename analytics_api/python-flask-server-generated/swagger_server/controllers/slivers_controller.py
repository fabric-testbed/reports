import connexion
import six

from analytics_api.swagger_server.models.slivers import Slivers  # noqa: E501
from analytics_api.swagger_server.models.status400_bad_request import Status400BadRequest  # noqa: E501
from analytics_api.swagger_server.models.status401_unauthorized import Status401Unauthorized  # noqa: E501
from analytics_api.swagger_server.models.status403_forbidden import Status403Forbidden  # noqa: E501
from analytics_api.swagger_server.models.status404_not_found import Status404NotFound  # noqa: E501
from analytics_api.swagger_server.models.status500_internal_server_error import Status500InternalServerError  # noqa: E501
from analytics_api.swagger_server import util


def slivers_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None, ip_subnet=None, site=None, host=None, page=None, per_page=None):  # noqa: E501
    """Get slivers

    Retrieve a list of slivers with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: str
    :param user_email: Filter by user email
    :type user_email: str
    :param project_id: Filter by project uuid
    :type project_id: str
    :param slice_id: Filter by slice uuid
    :type slice_id: str
    :param sliver_id: Filter by sliver uuid
    :type sliver_id: str
    :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
    :type sliver_type: str
    :param sliver_state: Filter by sliver state; allowed values ascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type sliver_state: str
    :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
    :type component_type: str
    :param component_model: Filter by component model
    :type component_model: str
    :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
    :type bdf: str
    :param vlan: Filter by VLAN associated with their sliver interfaces.
    :type vlan: str
    :param ip_subnet: Filter by specified IP subnet
    :type ip_subnet: str
    :param site: Filter by site
    :type site: str
    :param host: Filter by host
    :type host: str
    :param page: Page number for pagination. Default is 1.
    :type page: int
    :param per_page: Number of records per page. Default is 10.
    :type per_page: int

    :rtype: Slivers
    """
    start_time = util.deserialize_datetime(start_time)
    end_time = util.deserialize_datetime(end_time)
    return 'do some magic!'

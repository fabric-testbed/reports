import connexion

from reports_api.response_code import slices_controller as rc
from reports_api.response_code.cors_response import cors_400
from reports_api.swagger_server.models import Slice


def slices_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None, ip_subnet=None, facility=None, site=None, host=None, exclude_user_id=None, exclude_user_email=None, exclude_project_id=None, exclude_site=None, exclude_host=None, exclude_slice_state=None, exclude_sliver_state=None, page=None, per_page=None):  # noqa: E501
    """Get slices

    Retrieve a list of slices with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: List[str]
    :param user_email: Filter by user email
    :type user_email: List[str]
    :param project_id: Filter by project uuid
    :type project_id: List[str]
    :param slice_id: Filter by slice uuid
    :type slice_id: List[str]
    :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type slice_state: List[str]
    :param sliver_id: Filter by sliver uuid
    :type sliver_id: List[str]
    :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
    :type sliver_type: List[str]
    :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type sliver_state: List[str]
    :param component_type: Filter by component type, allowed values GPU, SmartNIC, SharedNIC, FPGA, NVME, Storage
    :type component_type: List[str]
    :param component_model: Filter by component model
    :type component_model: List[str]
    :param bdf: Filter by specified BDF (Bus:Device.Function) of interfaces/components
    :type bdf: List[str]
    :param vlan: Filter by VLAN associated with their sliver interfaces.
    :type vlan: List[str]
    :param ip_subnet: Filter by specified IP subnet
    :type ip_subnet: List[str]
    :param facility: Filter by facility
    :type facility: List[str]
    :param site: Filter by site
    :type site: List[str]
    :param host: Filter by host
    :type host: List[str]
    :param exclude_user_id: Exclude Users by IDs
    :type exclude_user_id: List[str]
    :param exclude_user_email: Exclude Users by emails
    :type exclude_user_email: List[str]
    :param exclude_project_id: Exclude projects
    :type exclude_project_id: List[str]
    :param exclude_site: Exclude sites
    :type exclude_site: List[str]
    :param exclude_host: Exclude hosts
    :type exclude_host: List[str]
    :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type exclude_slice_state: List[str]
    :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type exclude_sliver_state: List[str]
    :param page: Page number for pagination. Default is 0.
    :type page: int
    :param per_page: Number of records per page. Default is 200.
    :type per_page: int

    :rtype: Slices
    """
    return rc.slices_get(start_time=start_time, end_time=end_time, user_email=user_email, user_id=user_id, vlan=vlan,
                         sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                         sliver_state=sliver_state,site=site, host=host, slice_state=slice_state,
                         project_id=project_id, component_model=component_model, facility=facility,
                         component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
                         exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                         exclude_project_id=exclude_project_id, exclude_site=exclude_site, exclude_host=exclude_host)


def slices_slice_id_post(slice_id, body=None):  # noqa: E501
    """Create/Update a slice

    Create a Slice # noqa: E501

    :param slice_id: 
    :type slice_id: 
    :param body: Create new Slice
    :type body: dict | bytes

    :rtype: Status200OkNoContent
    """
    if connexion.request.is_json:
        body = Slice.from_dict(connexion.request.get_json())  # noqa: E501
        if slice_id != body.slice_id:
            return cors_400(details="slice_id in uri doesn't match slice_id in body")
    return rc.slices_slice_id_post(body=body, slice_id=slice_id)

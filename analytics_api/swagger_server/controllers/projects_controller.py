from analytics_api.response_code import projects_controller as rc


def projects_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None,
                 slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None,
                 component_model=None, bdf=None, vlan=None, ip_subnet=None, site=None, host=None, page=None,
                 per_page=None):  # noqa: E501
    """Retrieve a list of projects

    Returns a paginated list of projects with their UUIDs. # noqa: E501

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
    :param slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type slice_state: str
    :param sliver_id: Filter by sliver uuid
    :type sliver_id: str
    :param sliver_type: Filter by sliver type; allowed values VM, Switch, Facility, L2STS, L2PTP, L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, FABNetv4Ext, FABNetv6Ext
    :type sliver_type: str
    :param sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
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

    :rtype: Projects
    """
    return rc.projects_get(start_time=start_time, end_time=end_time, user_email=user_email, user_id=user_id, vlan=vlan,
                           sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                           sliver_state=sliver_state,site=site, host=host, slice_state=slice_state,
                           project_id=project_id, component_model=component_model,
                           component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page)

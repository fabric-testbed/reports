from reports_api.response_code import users_controller as rc



def users_get(start_time=None, end_time=None, user_id=None, user_email=None, project_id=None, slice_id=None, slice_state=None, sliver_id=None, sliver_type=None, sliver_state=None, component_type=None, component_model=None, bdf=None, vlan=None, ip_subnet=None, facility=None, site=None, host=None, exclude_user_id=None, exclude_user_email=None, exclude_project_id=None, exclude_site=None, exclude_host=None, exclude_slice_state=None, exclude_sliver_state=None, project_type=None, exclude_project_type=None, user_active=None, page=None, per_page=None):  # noqa: E501
    """Get users

    Retrieve a list of users with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: List[str]
    :param user_email: Filter by user email
    :type user_email: List[str]
    :param project_id: Filter by list of project UUIDs to include
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
    :param exclude_project_id: Filter by list of project UUIDs to exclude
    :type exclude_project_id: List[str]
    :param exclude_site: Exclude sites
    :type exclude_site: List[str]
    :param exclude_host: Exclude hosts
    :type exclude_host: List[str]
    :param exclude_slice_state: Filter by slice state; allowed values Nascent, Configuring, StableError, StableOK, Closing, Dead, Modifying, ModifyOK, ModifyError, AllocatedError, AllocatedOK
    :type exclude_slice_state: List[str]
    :param exclude_sliver_state: Filter by sliver state; allowed values Nascent, Ticketed, Active, ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail
    :type exclude_sliver_state: List[str]
    :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
    :type project_type: List[str]
    :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
    :type exclude_project_type: List[str]
    :param user_active: Filter by user active status
    :type user_active: bool
    :param page: Page number for pagination. Default is 0.
    :type page: int
    :param per_page: Number of records per page. Default is 200.
    :type per_page: int

    :rtype: Users
    """
    return rc.users_get(start_time=start_time, end_time=end_time, user_email=user_email, user_id=user_id, vlan=vlan,
                        sliver_id=sliver_id, sliver_type=sliver_type, slice_id=slice_id, bdf=bdf,
                        sliver_state=sliver_state,site=site, host=host, slice_state=slice_state,
                        project_id=project_id, component_model=component_model, facility=facility,
                        component_type=component_type, ip_subnet=ip_subnet, page=page, per_page=per_page,
                        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
                        exclude_project_id=exclude_project_id, exclude_site=exclude_site, exclude_host=exclude_host,
                        exclude_slice_state=exclude_slice_state, exclude_sliver_state=exclude_sliver_state,
                        project_type=project_type, user_active=user_active, exclude_project_type=exclude_project_type)


def users_memberships_get(start_time=None, end_time=None, user_id=None, user_email=None, exclude_user_id=None, exclude_user_email=None, project_type=None, exclude_project_type=None, project_active=None, project_expired=None, project_retired=None, user_active=None, page=None, per_page=None):  # noqa: E501
    """Get users

    Retrieve a list of users with optional filters. # noqa: E501

    :param start_time: Filter by start time (inclusive)
    :type start_time: str
    :param end_time: Filter by end time (inclusive)
    :type end_time: str
    :param user_id: Filter by user uuid
    :type user_id: List[str]
    :param user_email: Filter by user email
    :type user_email: List[str]
    :param exclude_user_id: Exclude Users by IDs
    :type exclude_user_id: List[str]
    :param exclude_user_email: Exclude Users by emails
    :type exclude_user_email: List[str]
    :param project_type: Filter by project type; allowed values research, education, maintenance, tutorial
    :type project_type: List[str]
    :param exclude_project_type: Exclude by project type; allowed values research, education, maintenance, tutorial
    :type exclude_project_type: List[str]
    :param project_active: Filter by project active status
    :type project_active: bool
    :param project_expired: Filter by project expiration (true &#x3D; expired)
    :type project_expired: bool
    :param project_retired: Filter by project retirement (true &#x3D; retired)
    :type project_retired: bool
    :param user_active: Filter by user active status
    :type user_active: bool
    :param page: Page number for pagination. Default is 0.
    :type page: int
    :param per_page: Number of records per page. Default is 200.
    :type per_page: int

    :rtype: UserMemberships
    """
    return rc.users_memberships_get(start_time=start_time, end_time=end_time, user_id=user_id,
                                    exclude_user_id=exclude_user_id, user_email=user_email,
                                    exclude_user_email=exclude_user_email,
                                    project_type=project_type, exclude_project_type=exclude_project_type,
                                    project_active=project_active, project_expired=project_expired,
                                    project_retired=project_retired, user_active=user_active,
                                    page=page, per_page=per_page)


def users_uuid_get(uuid):  # noqa: E501
    """Get specific user

    Returns a user identified by uuid. # noqa: E501

    :param uuid: User identified by universally unique identifier
    :type uuid: str

    :rtype: Users
    """
    return rc.users_uuid_get(uuid=uuid)

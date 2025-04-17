# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from reports_api.swagger_server.models.base_model_ import Model
from reports_api.swagger_server.models.slice_slivers import SliceSlivers  # noqa: F401,E501
from reports_api.swagger_server import util


class Slice(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, project_id: str=None, user_id: str=None, slice_id: str=None, slice_name: str=None, state: str=None, lease_start: datetime=None, lease_end: datetime=None, slivers: SliceSlivers=None):  # noqa: E501
        """Slice - a model defined in Swagger

        :param project_id: The project_id of this Slice.  # noqa: E501
        :type project_id: str
        :param user_id: The user_id of this Slice.  # noqa: E501
        :type user_id: str
        :param slice_id: The slice_id of this Slice.  # noqa: E501
        :type slice_id: str
        :param slice_name: The slice_name of this Slice.  # noqa: E501
        :type slice_name: str
        :param state: The state of this Slice.  # noqa: E501
        :type state: str
        :param lease_start: The lease_start of this Slice.  # noqa: E501
        :type lease_start: datetime
        :param lease_end: The lease_end of this Slice.  # noqa: E501
        :type lease_end: datetime
        :param slivers: The slivers of this Slice.  # noqa: E501
        :type slivers: SliceSlivers
        """
        self.swagger_types = {
            'project_id': str,
            'user_id': str,
            'slice_id': str,
            'slice_name': str,
            'state': str,
            'lease_start': datetime,
            'lease_end': datetime,
            'slivers': SliceSlivers
        }

        self.attribute_map = {
            'project_id': 'project_id',
            'user_id': 'user_id',
            'slice_id': 'slice_id',
            'slice_name': 'slice_name',
            'state': 'state',
            'lease_start': 'lease_start',
            'lease_end': 'lease_end',
            'slivers': 'slivers'
        }
        self._project_id = project_id
        self._user_id = user_id
        self._slice_id = slice_id
        self._slice_name = slice_name
        self._state = state
        self._lease_start = lease_start
        self._lease_end = lease_end
        self._slivers = slivers

    @classmethod
    def from_dict(cls, dikt) -> 'Slice':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The slice of this Slice.  # noqa: E501
        :rtype: Slice
        """
        return util.deserialize_model(dikt, cls)

    @property
    def project_id(self) -> str:
        """Gets the project_id of this Slice.


        :return: The project_id of this Slice.
        :rtype: str
        """
        return self._project_id

    @project_id.setter
    def project_id(self, project_id: str):
        """Sets the project_id of this Slice.


        :param project_id: The project_id of this Slice.
        :type project_id: str
        """

        self._project_id = project_id

    @property
    def user_id(self) -> str:
        """Gets the user_id of this Slice.


        :return: The user_id of this Slice.
        :rtype: str
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id: str):
        """Sets the user_id of this Slice.


        :param user_id: The user_id of this Slice.
        :type user_id: str
        """

        self._user_id = user_id

    @property
    def slice_id(self) -> str:
        """Gets the slice_id of this Slice.


        :return: The slice_id of this Slice.
        :rtype: str
        """
        return self._slice_id

    @slice_id.setter
    def slice_id(self, slice_id: str):
        """Sets the slice_id of this Slice.


        :param slice_id: The slice_id of this Slice.
        :type slice_id: str
        """

        self._slice_id = slice_id

    @property
    def slice_name(self) -> str:
        """Gets the slice_name of this Slice.


        :return: The slice_name of this Slice.
        :rtype: str
        """
        return self._slice_name

    @slice_name.setter
    def slice_name(self, slice_name: str):
        """Sets the slice_name of this Slice.


        :param slice_name: The slice_name of this Slice.
        :type slice_name: str
        """

        self._slice_name = slice_name

    @property
    def state(self) -> str:
        """Gets the state of this Slice.


        :return: The state of this Slice.
        :rtype: str
        """
        return self._state

    @state.setter
    def state(self, state: str):
        """Sets the state of this Slice.


        :param state: The state of this Slice.
        :type state: str
        """

        self._state = state

    @property
    def lease_start(self) -> datetime:
        """Gets the lease_start of this Slice.


        :return: The lease_start of this Slice.
        :rtype: datetime
        """
        return self._lease_start

    @lease_start.setter
    def lease_start(self, lease_start: datetime):
        """Sets the lease_start of this Slice.


        :param lease_start: The lease_start of this Slice.
        :type lease_start: datetime
        """

        self._lease_start = lease_start

    @property
    def lease_end(self) -> datetime:
        """Gets the lease_end of this Slice.


        :return: The lease_end of this Slice.
        :rtype: datetime
        """
        return self._lease_end

    @lease_end.setter
    def lease_end(self, lease_end: datetime):
        """Sets the lease_end of this Slice.


        :param lease_end: The lease_end of this Slice.
        :type lease_end: datetime
        """

        self._lease_end = lease_end

    @property
    def slivers(self) -> SliceSlivers:
        """Gets the slivers of this Slice.


        :return: The slivers of this Slice.
        :rtype: SliceSlivers
        """
        return self._slivers

    @slivers.setter
    def slivers(self, slivers: SliceSlivers):
        """Sets the slivers of this Slice.


        :param slivers: The slivers of this Slice.
        :type slivers: SliceSlivers
        """

        self._slivers = slivers

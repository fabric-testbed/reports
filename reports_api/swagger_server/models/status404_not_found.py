# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from reports_api.swagger_server.models.base_model_ import Model
from reports_api.swagger_server.models.status404_not_found_errors import Status404NotFoundErrors  # noqa: F401,E501
from reports_api.swagger_server import util


class Status404NotFound(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, errors: List[Status404NotFoundErrors]=None, type: str='error', size: int=1, status: int=404):  # noqa: E501
        """Status404NotFound - a model defined in Swagger

        :param errors: The errors of this Status404NotFound.  # noqa: E501
        :type errors: List[Status404NotFoundErrors]
        :param type: The type of this Status404NotFound.  # noqa: E501
        :type type: str
        :param size: The size of this Status404NotFound.  # noqa: E501
        :type size: int
        :param status: The status of this Status404NotFound.  # noqa: E501
        :type status: int
        """
        self.swagger_types = {
            'errors': List[Status404NotFoundErrors],
            'type': str,
            'size': int,
            'status': int
        }

        self.attribute_map = {
            'errors': 'errors',
            'type': 'type',
            'size': 'size',
            'status': 'status'
        }
        self._errors = errors
        self._type = type
        self._size = size
        self._status = status

    @classmethod
    def from_dict(cls, dikt) -> 'Status404NotFound':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The status_404_not_found of this Status404NotFound.  # noqa: E501
        :rtype: Status404NotFound
        """
        return util.deserialize_model(dikt, cls)

    @property
    def errors(self) -> List[Status404NotFoundErrors]:
        """Gets the errors of this Status404NotFound.


        :return: The errors of this Status404NotFound.
        :rtype: List[Status404NotFoundErrors]
        """
        return self._errors

    @errors.setter
    def errors(self, errors: List[Status404NotFoundErrors]):
        """Sets the errors of this Status404NotFound.


        :param errors: The errors of this Status404NotFound.
        :type errors: List[Status404NotFoundErrors]
        """

        self._errors = errors

    @property
    def type(self) -> str:
        """Gets the type of this Status404NotFound.


        :return: The type of this Status404NotFound.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this Status404NotFound.


        :param type: The type of this Status404NotFound.
        :type type: str
        """

        self._type = type

    @property
    def size(self) -> int:
        """Gets the size of this Status404NotFound.


        :return: The size of this Status404NotFound.
        :rtype: int
        """
        return self._size

    @size.setter
    def size(self, size: int):
        """Sets the size of this Status404NotFound.


        :param size: The size of this Status404NotFound.
        :type size: int
        """

        self._size = size

    @property
    def status(self) -> int:
        """Gets the status of this Status404NotFound.


        :return: The status of this Status404NotFound.
        :rtype: int
        """
        return self._status

    @status.setter
    def status(self, status: int):
        """Sets the status of this Status404NotFound.


        :param status: The status of this Status404NotFound.
        :type status: int
        """

        self._status = status

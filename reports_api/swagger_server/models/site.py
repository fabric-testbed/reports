# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from reports_api.swagger_server.models.base_model_ import Model
from reports_api.swagger_server.models.host import Host  # noqa: F401,E501
from reports_api.swagger_server import util


class Site(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, name: str=None, hosts: List[Host]=None):  # noqa: E501
        """Site - a model defined in Swagger

        :param name: The name of this Site.  # noqa: E501
        :type name: str
        :param hosts: The hosts of this Site.  # noqa: E501
        :type hosts: List[Host]
        """
        self.swagger_types = {
            'name': str,
            'hosts': List[Host]
        }

        self.attribute_map = {
            'name': 'name',
            'hosts': 'hosts'
        }
        self._name = name
        self._hosts = hosts

    @classmethod
    def from_dict(cls, dikt) -> 'Site':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The site of this Site.  # noqa: E501
        :rtype: Site
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self) -> str:
        """Gets the name of this Site.


        :return: The name of this Site.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this Site.


        :param name: The name of this Site.
        :type name: str
        """

        self._name = name

    @property
    def hosts(self) -> List[Host]:
        """Gets the hosts of this Site.


        :return: The hosts of this Site.
        :rtype: List[Host]
        """
        return self._hosts

    @hosts.setter
    def hosts(self, hosts: List[Host]):
        """Sets the hosts of this Site.


        :param hosts: The hosts of this Site.
        :type hosts: List[Host]
        """

        self._hosts = hosts

# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from reports_api.swagger_server.models.base_model_ import Model
from reports_api.swagger_server.models.project_users import ProjectUsers  # noqa: F401,E501
from reports_api.swagger_server import util


class Project(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, project_id: str=None, project_name: str=None, users: ProjectUsers=None):  # noqa: E501
        """Project - a model defined in Swagger

        :param project_id: The project_id of this Project.  # noqa: E501
        :type project_id: str
        :param project_name: The project_name of this Project.  # noqa: E501
        :type project_name: str
        :param users: The users of this Project.  # noqa: E501
        :type users: ProjectUsers
        """
        self.swagger_types = {
            'project_id': str,
            'project_name': str,
            'users': ProjectUsers
        }

        self.attribute_map = {
            'project_id': 'project_id',
            'project_name': 'project_name',
            'users': 'users'
        }
        self._project_id = project_id
        self._project_name = project_name
        self._users = users

    @classmethod
    def from_dict(cls, dikt) -> 'Project':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The project of this Project.  # noqa: E501
        :rtype: Project
        """
        return util.deserialize_model(dikt, cls)

    @property
    def project_id(self) -> str:
        """Gets the project_id of this Project.


        :return: The project_id of this Project.
        :rtype: str
        """
        return self._project_id

    @project_id.setter
    def project_id(self, project_id: str):
        """Sets the project_id of this Project.


        :param project_id: The project_id of this Project.
        :type project_id: str
        """

        self._project_id = project_id

    @property
    def project_name(self) -> str:
        """Gets the project_name of this Project.


        :return: The project_name of this Project.
        :rtype: str
        """
        return self._project_name

    @project_name.setter
    def project_name(self, project_name: str):
        """Sets the project_name of this Project.


        :param project_name: The project_name of this Project.
        :type project_name: str
        """

        self._project_name = project_name

    @property
    def users(self) -> ProjectUsers:
        """Gets the users of this Project.


        :return: The users of this Project.
        :rtype: ProjectUsers
        """
        return self._users

    @users.setter
    def users(self, users: ProjectUsers):
        """Sets the users of this Project.


        :param users: The users of this Project.
        :type users: ProjectUsers
        """

        self._users = users

# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from reports_api.swagger_server.models.base_model_ import Model
from reports_api.swagger_server import util


class Component(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, component_id: str=None, node_id: str=None, component_node_id: str=None, type: str=None, model: str=None, bdfs: List[str]=None):  # noqa: E501
        """Component - a model defined in Swagger

        :param component_id: The component_id of this Component.  # noqa: E501
        :type component_id: str
        :param node_id: The node_id of this Component.  # noqa: E501
        :type node_id: str
        :param component_node_id: The component_node_id of this Component.  # noqa: E501
        :type component_node_id: str
        :param type: The type of this Component.  # noqa: E501
        :type type: str
        :param model: The model of this Component.  # noqa: E501
        :type model: str
        :param bdfs: The bdfs of this Component.  # noqa: E501
        :type bdfs: List[str]
        """
        self.swagger_types = {
            'component_id': str,
            'node_id': str,
            'component_node_id': str,
            'type': str,
            'model': str,
            'bdfs': List[str]
        }

        self.attribute_map = {
            'component_id': 'component_id',
            'node_id': 'node_id',
            'component_node_id': 'component_node_id',
            'type': 'type',
            'model': 'model',
            'bdfs': 'bdfs'
        }
        self._component_id = component_id
        self._node_id = node_id
        self._component_node_id = component_node_id
        self._type = type
        self._model = model
        self._bdfs = bdfs

    @classmethod
    def from_dict(cls, dikt) -> 'Component':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The component of this Component.  # noqa: E501
        :rtype: Component
        """
        return util.deserialize_model(dikt, cls)

    @property
    def component_id(self) -> str:
        """Gets the component_id of this Component.


        :return: The component_id of this Component.
        :rtype: str
        """
        return self._component_id

    @component_id.setter
    def component_id(self, component_id: str):
        """Sets the component_id of this Component.


        :param component_id: The component_id of this Component.
        :type component_id: str
        """

        self._component_id = component_id

    @property
    def node_id(self) -> str:
        """Gets the node_id of this Component.


        :return: The node_id of this Component.
        :rtype: str
        """
        return self._node_id

    @node_id.setter
    def node_id(self, node_id: str):
        """Sets the node_id of this Component.


        :param node_id: The node_id of this Component.
        :type node_id: str
        """

        self._node_id = node_id

    @property
    def component_node_id(self) -> str:
        """Gets the component_node_id of this Component.


        :return: The component_node_id of this Component.
        :rtype: str
        """
        return self._component_node_id

    @component_node_id.setter
    def component_node_id(self, component_node_id: str):
        """Sets the component_node_id of this Component.


        :param component_node_id: The component_node_id of this Component.
        :type component_node_id: str
        """

        self._component_node_id = component_node_id

    @property
    def type(self) -> str:
        """Gets the type of this Component.


        :return: The type of this Component.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this Component.


        :param type: The type of this Component.
        :type type: str
        """

        self._type = type

    @property
    def model(self) -> str:
        """Gets the model of this Component.


        :return: The model of this Component.
        :rtype: str
        """
        return self._model

    @model.setter
    def model(self, model: str):
        """Sets the model of this Component.


        :param model: The model of this Component.
        :type model: str
        """

        self._model = model

    @property
    def bdfs(self) -> List[str]:
        """Gets the bdfs of this Component.


        :return: The bdfs of this Component.
        :rtype: List[str]
        """
        return self._bdfs

    @bdfs.setter
    def bdfs(self, bdfs: List[str]):
        """Sets the bdfs of this Component.


        :param bdfs: The bdfs of this Component.
        :type bdfs: List[str]
        """

        self._bdfs = bdfs

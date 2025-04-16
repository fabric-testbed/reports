#!/usr/bin/env python3
# MIT License
#
# Copyright (component) 2020 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)
import logging
from datetime import datetime, timedelta

from fss_utils.jwt_validate import JWTValidator

from analytics_api.common.configuration import Configuration
from analytics_api.common.log_helper import LogHelper
from analytics_api.security.token_validator import TokenValidator

logging.TRACE = 5
logging.addLevelName(logging.TRACE, "TRACE")
logging.Logger.trace = lambda inst, msg, *args, **kwargs: inst.log(logging.TRACE, msg, *args, **kwargs)
logging.trace = lambda msg, *args, **kwargs: logging.log(logging.TRACE, msg, *args, **kwargs)


class Globals:
    config_file = "config.yml"
    RPC_TIMEOUT = 0

    def __init__(self):
        self._config = Configuration(self.config_file)
        self.log = self.make_logger()
        self._jwt_validator = None
        self._token_validator = None

        CREDMGR_CERTS = self.config.oauth_config.get("jwks-url", None)
        CREDMGR_KEY_REFRESH = self.config.oauth_config.get("key-refresh", None)
        CREDMGR_TRL_REFRESH = self.config.oauth_config.get("trl-refresh", '00:01:00')
        self.log.info(f'Initializing JWT Validator to use {CREDMGR_CERTS} endpoint, '
                      f'refreshing keys every {CREDMGR_KEY_REFRESH} HH:MM:SS refreshing '
                      f'token revoke list every {CREDMGR_TRL_REFRESH} HH:MM:SS')
        t = datetime.strptime(CREDMGR_KEY_REFRESH, "%H:%M:%S")
        self._jwt_validator = JWTValidator(url=CREDMGR_CERTS,
                                           refresh_period=timedelta(hours=t.hour, minutes=t.minute, seconds=t.second))
        from urllib.parse import urlparse
        t = datetime.strptime(CREDMGR_KEY_REFRESH, "%H:%M:%S")
        self._token_validator = TokenValidator(credmgr_host=str(urlparse(CREDMGR_CERTS).hostname),
                                               refresh_period=timedelta(hours=t.hour, minutes=t.minute, seconds=t.second),
                                               jwt_validator=self.jwt_validator)

    def make_logger(self):
        """
        Detects the path and level for the log file from the actor config and sets
        up a logger. Instead of detecting the path and/or level from the
        config, a custom path and/or level for the log file can be passed as
        optional arguments.

       :return: logging.Logger object
        """
        log_config = self.config.logging_config
        if log_config is None:
            raise RuntimeError('No logging  config information available')

        log_dir = self.config.logging_config.get("log-directory", ".")
        log_file = self.config.logging_config.get("log-file", "analytics.log")
        log_level = self.config.logging_config.get("log-level", None)
        log_retain = int(self.config.logging_config.get("log-retain", 50))
        log_size = int(self.config.logging_config.get("log-size", 5000000))
        logger = self.config.logging_config.get("logger", "analytics")

        return LogHelper.make_logger(log_dir=log_dir, log_file=log_file, log_level=log_level, log_retain=log_retain,
                                     log_size=log_size, logger=logger)

    @property
    def jwt_validator(self) -> JWTValidator:
        return self._jwt_validator

    @property
    def token_validator(self) -> TokenValidator:
        return self._token_validator

    @property
    def config(self) -> Configuration:
        return self._config



class GlobalsSingleton:
    """
    Global Singleton class
    """
    __instance = None

    def __init__(self):
        if self.__instance is not None:
            raise Exception("Singleton can't be created twice !")

    def get(self):
        """
        Actually create an instance
        """
        if self.__instance is None:
            self.__instance = Globals()
        return self.__instance

    get = classmethod(get)

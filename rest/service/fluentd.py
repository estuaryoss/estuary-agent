import datetime
import os
import platform

from about import properties
from rest.api.constants.env_constants import EnvConstants
from rest.utils.env_startup import EnvStartup


class Fluentd:

    def __init__(self, logger):
        self.logger = logger

    def emit(self, tag, msg, level="DEBUG"):
        message = self.__enrichlog(level, msg)
        response = self.__send(tag, message)
        return {"emit": response,
                "message": message}

    @staticmethod
    def __enrichlog(level_code, msg):
        return {
            "name": properties.get('name'),
            "port": EnvStartup.get_instance().get(EnvConstants.PORT),
            "version": properties.get('version'),
            "uname": list(platform.uname()),
            "python": platform.python_version(),
            "pid": os.getpid(),
            "level_code": level_code,
            "msg": msg,
            "timestamp": str(datetime.datetime.now()),
        }

    def __send(self, tag, msg):
        if EnvStartup.get_instance().get(EnvConstants.FLUENTD_IP_PORT):
            return str(self.logger.emit(tag, msg)).lower()

        return "fluentd logging not enabled"

#!/usr/bin/env python3
import multiprocessing
import os
from pathlib import Path

from rest.api.constants.env_constants import EnvConstants
from rest.api.constants.env_init import EnvInit
from rest.api.definitions import command_detached_init
from rest.api.loghelpers.message_dumper import MessageDumper
from rest.api.routes import app
from rest.api.routes import fluentd_utils
from rest.environment.environment import Environment
from rest.service.eureka import Eureka
from rest.utils.env_startup import EnvStartup
from rest.utils.io_utils import IOUtils

if __name__ == "__main__":
    # fix for pyinstaller
    multiprocessing.freeze_support()

    host = '0.0.0.0'
    port = EnvStartup.get_instance().get(EnvConstants.PORT)
    fluentd_tag = "startup"
    message_dumper = MessageDumper()
    io_utils = IOUtils()

    if EnvStartup.get_instance().get(EnvConstants.EUREKA_SERVER):
        Eureka(EnvStartup.get_instance().get(EnvConstants.EUREKA_SERVER)).register_app(
            EnvStartup.get_instance().get(EnvConstants.APP_IP_PORT))

    io_utils.create_dir(Path(EnvInit.TEMPLATES_DIR))
    io_utils.create_dir(Path(EnvInit.VARS_DIR))

    file = EnvInit.COMMAND_DETACHED_FILENAME

    try:
        command_detached_init["pid"] = os.getpid()
        io_utils.write_to_file_dict(Path(file), command_detached_init)
    except Exception as e:
        raise e

    environ_dump = message_dumper.dump_message(Environment.get_instance().get_env_and_virtual_env())
    ip_port_dump = message_dumper.dump_message({"host": host, "port": port})

    app.logger.debug({"msg": environ_dump})
    app.logger.debug({"msg": ip_port_dump})
    app.logger.debug({"msg": EnvStartup.get_instance()})

    fluentd_utils.emit(tag=fluentd_tag, msg=environ_dump)

    app.run(host=host, port=port)

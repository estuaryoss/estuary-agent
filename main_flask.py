#!/usr/bin/env python3
import multiprocessing
import os
from pathlib import Path

from rest.api import EurekaRegistrator
from rest.api.constants.env_constants import EnvConstants
from rest.api.definitions import test_info_init
from rest.api.logginghelpers.message_dumper import MessageDumper
from rest.api.routes import app
from rest.api.routes import fluentd_utils
from rest.utils.env_startup import EnvStartup
from rest.utils.io_utils import IOUtils

if __name__ == "__main__":
    # fix for pyinstaller
    multiprocessing.freeze_support()

    host = '0.0.0.0'
    port = EnvStartup.get_instance().get("port")
    fluentd_tag = "startup"
    variables = "testinfo.json"
    message_dumper = MessageDumper()
    io_utils = IOUtils()

    if EnvStartup.get_instance().get("eureka_server"):
        EurekaRegistrator(EnvStartup.get_instance().get("eureka_server")).register_app(
            EnvStartup.get_instance().get("app_ip_port"))

    io_utils.create_dir(Path(EnvConstants.TEMPLATES_PATH))
    io_utils.create_dir(Path(EnvConstants.VARIABLES_PATH))

    file = EnvConstants.VARIABLES_PATH + "/" + variables

    try:
        test_info_init["pid"] = os.getpid()
        io_utils.write_to_file_dict(Path(file), test_info_init)
    except Exception as e:
        raise e

    environ_dump = message_dumper.dump_message(dict(os.environ))
    ip_port_dump = message_dumper.dump_message({"host": host, "port": port})

    app.logger.debug({"msg": environ_dump})
    app.logger.debug({"msg": ip_port_dump})
    app.logger.debug({"msg": EnvStartup.get_instance()})

    fluentd_utils.emit(tag=fluentd_tag, msg=environ_dump)

    app.run(host=host, port=port)

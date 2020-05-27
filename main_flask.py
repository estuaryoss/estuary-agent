#!/usr/bin/env python3

import os
from pathlib import Path

from about import properties
from rest.api.constants.env_constants import EnvConstants
from rest.api.definitions import test_info_init
from rest.api.logginghelpers.message_dumper import MessageDumper
from rest.api.routes import app
from rest.api.routes import fluentd_utils
from rest.utils.io_utils import IOUtils

if __name__ == "__main__":
    port = properties["port"]
    host = '0.0.0.0'
    fluentd_tag = "startup"
    variables = "testinfo.json"

    message_dumper = MessageDumper()
    io_utils = IOUtils()

    if os.environ.get('PORT'):
        port = int(os.environ.get("PORT"))  # override port  if set from env

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

    fluentd_utils.emit(tag=fluentd_tag, msg=environ_dump)

    app.run(host=host, port=port)

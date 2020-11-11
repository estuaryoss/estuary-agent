import platform

import psutil

from rest.utils.io_utils import IOUtils

properties = {
    "name": "estuary-agent",
    "version": "4.3.0",
    "description": "Run your shell commands via REST API",
    "author": "Catalin Dinuta",
    "platforms": ["Linux", "Raspbian", "Mac", "Windows"],
    "license": "Apache-2.0"
}

about_system = {
    "system": platform.system(),
    "layer": "Docker" if IOUtils.does_file_exist("/.dockerenv") else "Virtual Machine",
    "hostname": platform.uname().node,
    "platform": platform.platform(),
    "release": platform.release(),
    "architecture": platform.architecture()[0],
    "machine": platform.machine(),
    "cpu": platform.processor(),
    "ram": str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB",
    "version": platform.version(),
    "python": platform.python_version()
}

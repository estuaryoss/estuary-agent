import platform

import psutil

from rest.utils.io_utils import IOUtils

properties = {
    "name": "estuary-agent",
    "version": "4.4.0",
    "description": "Run your shell commands via REST API",
    "author": "Catalin Dinuta",
    "platforms": ["Linux", "Raspbian", "Mac", "Windows"],
    "license": "Apache-2.0"
}

about_system = {
    "system": platform.system(),
    "platform": platform.platform(),
    "release": platform.release(),
    "version": platform.version(),
    "architecture": platform.architecture()[0],
    "machine": platform.machine(),
    "layer": "Docker" if IOUtils.does_file_exist("/.dockerenv") else "Machine",
    "hostname": platform.uname().node,
    "cpu": platform.processor(),
    "ram": str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB",
    "python": platform.python_version()
}

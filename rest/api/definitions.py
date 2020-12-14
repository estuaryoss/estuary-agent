import datetime
import os

from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    '/swagger/swagger.yml/',
    config={
        'app_name': "estuary-agent"
    },
)

command_detached_init = {
    "started": False,
    "finished": False,
    "id": "none",
    "pid": os.getpid(),
    "startedat": str(datetime.datetime.now()),
    "finishedat": str(datetime.datetime.now()),
    "duration": 0.000000,
    "commands": {}
}

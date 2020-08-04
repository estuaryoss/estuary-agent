import datetime
import os

from flask_swagger_ui import get_swaggerui_blueprint

unmodifiable_env_vars = {
    "TEMPLATES_DIR": os.environ.get('TEMPLATES_DIR'),
    "VARS_DIR": os.environ.get('VARS_DIR'),
    "PORT": os.environ.get('PORT'),
    "WORKSPACE": os.environ.get('WORKSPACE')
}

SWAGGER_URL = '/api/docs'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    '/swagger/swagger.yml/',
    config={
        'app_name': "estuary-agent"
    },
)

test_info_init = {
    "finished": False,
    "started": False,
    "startedat": str(datetime.datetime.now()),
    "finishedat": str(datetime.datetime.now()),
    "duration": 0.000000,
    "id": "none",
    "pid": 0,
    "commands": {}
}

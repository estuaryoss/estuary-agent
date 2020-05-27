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
        'app_name': "estuary-testrunner"
    },
)

test_info_init = {
    "finished": "false",
    "started": "false",
    "startedat": "none",
    "finishedat": "none",
    "duration": "none",
    "id": "none",
    "pid": "none",
    "commands": {}
}

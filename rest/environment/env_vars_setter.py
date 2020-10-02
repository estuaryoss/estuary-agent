import json

from rest.service.restapi import RestApi


class EnvVarsSetter:

    def __init__(self, conn, config):
        """
        Env var setter through REST API
        conn: a dict connection: ip, port, protocol, etc.  Example in routes.py
        config: Yaml config description on what env to have and what/in which order to run
        """
        self.service = RestApi(conn)
        self.yaml_config = config
        self.env_key = "env"

    def set_env_vars(self, headers):
        env_vars_dict = self.get_env_vars()
        return self.service.post(data=json.dumps(env_vars_dict), headers=headers)

    def get_env_vars(self):
        env_vars_dict = {}
        if self.yaml_config.get(self.env_key) is not None:
            env_vars_dict = {k: str(v) for k, v in self.yaml_config.get(self.env_key).items()}
        return env_vars_dict

    def get_env_key(self):
        return self.env_key

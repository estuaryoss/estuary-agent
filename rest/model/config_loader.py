import yaml


class ConfigLoader:
    def __init__(self, config):
        """ Loads the yaml config """
        self.config = config

    def yaml(self):
        return yaml.dump(self.__dict__)

    @staticmethod
    def load(data):
        return ConfigLoader(yaml.safe_load(data))

    def get_config(self):
        return self.config

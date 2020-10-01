import yaml


class ConfigLoader:
    __in_order_fields = ["before_script", "script", "after_script"]
    __mandatory_fields = ["script"]

    def __init__(self, config):
        self.config = config

    def yaml(self):
        return yaml.dump(self.__dict__)

    @staticmethod
    def load(data):
        return ConfigLoader(yaml.safe_load(data))

    def get_cmds_in_order(self):
        self.__check_config()
        commands_list_in_order = []
        for section in self.config:
            [commands_list_in_order.append(cmd) for cmd in self.config.get(section) if
             section in self.__in_order_fields]

        return commands_list_in_order

    def __check_config(self):
        for elem in self.__mandatory_fields:
            if not self.config.get(elem):
                raise Exception(f"Mandatory section '{elem}' not found.")

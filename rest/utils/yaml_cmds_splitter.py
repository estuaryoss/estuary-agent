class YamlCommandsSplitter:
    __in_order_fields = ["before_script", "script", "after_script"]
    __mandatory_fields = ["script"]

    def __init__(self, config):
        """ Generates list of commands in order from yaml """
        self.config = config

    def get_cmds_in_order(self):
        self.__check_config()
        commands_list_in_order = []
        for section in self.__in_order_fields:
            if self.config.get(section) is not None:
                [commands_list_in_order.append(cmd) for cmd in self.config.get(section)]

        return commands_list_in_order

    def __check_config(self):
        for elem in self.__mandatory_fields:
            if not self.config.get(elem):
                raise Exception(f"Mandatory section '{elem}' was not found or it was empty.")

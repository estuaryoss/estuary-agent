class ConfigDescriptor:

    @staticmethod
    def description(description, config):
        """ Wrapper for api description in case of the endpoints that are using yaml configurations"""

        return {
            "description": description,
            "config": config
        }

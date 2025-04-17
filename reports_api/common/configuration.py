import yaml


class Configuration:
    def __init__(self, file_name: str):
        self.config_file = file_name
        self.config_dict = None
        with open(self.config_file) as f:
            self.config_dict = yaml.safe_load(f)

    @property
    def runtime_config(self):
        return self.config_dict.get("runtime", {})

    @property
    def logging_config(self):
        return self.config_dict.get("logging", {})

    @property
    def core_api_config(self):
        return self.config_dict.get("core_api", {})

    @property
    def oauth_config(self):
        return self.config_dict.get("oauth", {})

    @property
    def database_config(self):
        return self.config_dict.get("database", {})
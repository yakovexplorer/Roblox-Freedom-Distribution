import data_transfer
import util.resource
import util.versions
import tomli


class base_type:
    def __init__(self, path: str) -> None:
        self.config_path = util.resource.retr_config_full_path(path)
        with open(self.config_path, 'rb') as f:
            self.data_dict: dict = tomli.load(f)

        self.data_transferer = data_transfer.transferer()

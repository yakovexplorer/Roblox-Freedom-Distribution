
from . import _logic, structure
import util.resource
import util.versions
import functools
import tomli


class obj_type(structure.config_type, _logic.base_type):
    def __init__(self, path: str = util.resource.DEFAULT_CONFIG_PATH) -> None:
        _logic.base_type.__init__(
            self,
            path=path,
        )

        structure.config_type.__init__(
            self,
            root=self,
            current_typ=structure.config_type,
            **self.data_dict,
        )


@functools.cache
def get_cached_config(path: str = util.resource.DEFAULT_CONFIG_PATH) -> obj_type:
    obj = obj_type(path)
    return obj

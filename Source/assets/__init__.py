from . import extract, returns, material, serialisers, queue
from util.types import structs, wrappers
import util.const
import functools
import shutil
import os


class asseter:
    def __init__(
        self,
        dir_path: str,
        redirects: structs.asset_redirects,
        clear_on_start: bool,
    ) -> None:
        self.dir_path = dir_path
        self.redirects = redirects
        self.queuer = queue.queuer()

        if os.path.isdir(dir_path):
            if clear_on_start:
                shutil.rmtree(dir_path)
                os.makedirs(dir_path)
        else:
            os.makedirs(dir_path)

        if not clear_on_start:
            # Deletes cache from assets which should redirect so that the config file remains correct.
            for redir_id in redirects:
                path = self.get_asset_path(redir_id)
                if os.path.isfile(path):
                    os.remove(path)

    @functools.cache
    def get_asset_path(self, asset_id: int | str) -> str:
        return os.path.normpath(
            os.path.join(
                self.dir_path,
                (
                    f'{asset_id:011d}'
                    if isinstance(asset_id, int) else
                    asset_id
                ),
            )
        )

    def _load_file(self, path: str) -> bytes | None:
        if not os.path.isfile(path):
            return None

        with open(path, 'rb') as f:
            return f.read()

    def _save_file(self, path: str, data: bytes) -> None:
        with open(path, 'wb') as f:
            f.write(data)

    def _load_online_asset(self, asset_id: int) -> bytes | None:
        data = self.queuer.get(asset_id, extract.download_rōblox_asset)
        if data is None:
            return None

        data = serialisers.parse(data)
        return data

    def resolve_asset_id(self, id_str: str | None) -> int | None:
        if id_str is None:
            return None
        try:
            return int(id_str)
        except ValueError:
            return None

    def resolve_asset_version_id(self, id_str: str | None) -> int | None:
        # Don't assume this is true for production Rōblox:
        # RFD treats 'asset version ids' the same way as just plain 'version ids'.
        return self.resolve_asset_id(id_str)

    def resolve_asset_query(self, query: dict[str, str]) -> int | str:
        funcs = [
            (query.get('id'), self.resolve_asset_id),
            (query.get('assetversionid'), self.resolve_asset_version_id),
        ]

        for (prop_val, func) in funcs:
            if prop_val is None:
                continue
            result = func(prop_val)
            if result is not None:
                return result
        for (prop_val, func) in funcs:
            if prop_val is not None:
                return prop_val
        raise Exception('Unable to extract asset id from URL query.')

    def add_asset(self, asset_id: int | str, data: bytes) -> None:
        redirect = self.redirects.get(asset_id)
        if redirect is not None:
            raise Exception('File does not exist.')
        path = self.get_asset_path(asset_id)
        self._save_file(path, data)

    @functools.cache
    def is_blocklisted(self, asset_id: int | str) -> bool:
        '''
        This is to make sure that unauthorised clients can't get private files.
        '''
        asset_path = self.get_asset_path(asset_id)
        place_path = self.get_asset_path(util.const.PLACE_ID_CONST)
        if asset_path == place_path:
            return True
        return False

    def _load_asset_num(self, asset_id: int) -> bytes | None:
        return self._load_online_asset(asset_id)

    def _load_asset_str(self, asset_id: str) -> bytes | None:
        if asset_id.startswith(material.const.ID_PREFIX):
            return material.load_asset(asset_id)
        return None

    def _load_redir_asset(self, redirect: structs.asset_redirect) -> returns.base_type:
        if redirect.uri is not None:
            if redirect.uri.is_online:
                return returns.construct(
                    redirect_url=redirect.uri.value,
                )
            with open(redirect.uri.value, 'rb') as f:
                return returns.construct(
                    data=f.read(),
                )
        elif redirect.cmd_line is not None:
            # NOTE: redirect asset ids which share the same command line may also share the same output dump.
            # This happens when both assets are loaded near the same time.
            return returns.construct(
                data=self.queuer.get(
                    redirect.cmd_line,
                    extract.process_command_line,
                ),
            )
        else:
            return returns.construct()

    def _load_asset(self, asset_id: int | str) -> returns.base_type:
        redirect = self.redirects.get(asset_id)
        if redirect is not None:
            return self._load_redir_asset(redirect)
        if isinstance(asset_id, str):
            return returns.construct(data=self._load_asset_str(asset_id))
        elif isinstance(asset_id, int):
            return returns.construct(data=self._load_asset_num(asset_id))

    def get_asset(self, asset_id: int | str, bypass_blacklist: bool = False) -> returns.base_type:
        if not bypass_blacklist and self.is_blocklisted(asset_id):
            return returns.construct()

        asset_path = self.get_asset_path(asset_id)
        local_data = self._load_file(asset_path)
        if local_data:
            return returns.construct(data=local_data)

        result_data = self._load_asset(asset_id)
        if isinstance(result_data, returns.ret_data):
            self._save_file(asset_path, result_data.data)
        return result_data

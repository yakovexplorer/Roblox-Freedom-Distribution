import web_server._logic as web_server_logic
import config.structure
import config

# Make sure all API endpoints are working without taking anything therefrom.
from .endpoints import _


def make_server(
    port: web_server_logic.port_typ,
    game_config: config.obj_type,
    *args,
    **kwargs,
) -> web_server_logic.web_server:
    cls = web_server_logic.web_server_ssl if port.is_ssl else web_server_logic.web_server
    return cls(port, game_config, *args, **kwargs)

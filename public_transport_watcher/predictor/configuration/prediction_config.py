from public_transport_watcher.utils import get_env_variable

PREDICTION_CONFIG = {
    "graph": {
        "network_path": get_env_variable("NETWORK_PATH"),
    }
}

import os

from public_transport_watcher.utils import get_env_variable

PREDICTION_CONFIG = {
    "graph": {
        "base_network_path": get_env_variable("BASE_NETWORK_PATH"),
        "weighted_network_path": get_env_variable("WEIGHTED_NETWORK_PATH"),
        "adjust_station_weights": {
            "weight_factor": 0.1,
            "min_factor": 0.5,
            "max_factor": 1.5,
        },
    },
    "arima": {
        "graphs_dir": "graphs",
        "params_station_file": os.path.join(os.path.dirname(__file__), "station_arima_params.json"),
        "default_order": (2, 1, 2),
        "p_range": range(0, 3),
        "d_range": range(0, 2),
        "q_range": range(0, 3),
        "use_enhanced_prediction": True,
    },
}

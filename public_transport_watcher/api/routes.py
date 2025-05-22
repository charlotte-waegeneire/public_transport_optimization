from flask import Flask, jsonify, request

from public_transport_watcher.api.logger import log_request
from public_transport_watcher.predictor.graph_builder import GraphBuilder

app = Flask(__name__)
graph_builder = GraphBuilder()


@app.route("/api/v1/routes/optimal", methods=["GET"])
@log_request
def find_optimal_route():
    try:
        start_coords = request.args.get("start_coords")
        end_coords = request.args.get("end_coords")

        if not start_coords or not end_coords:
            return jsonify({"error": "Missing required parameters: start_coords or end_coords"}), 400

        # Parse coordinates
        try:
            start_coords = eval(start_coords)
            end_coords = eval(end_coords)

            # Validate coordinate format
            if not (
                isinstance(start_coords, tuple)
                and len(start_coords) == 2
                and isinstance(end_coords, tuple)
                and len(end_coords) == 2
            ):
                return jsonify({"error": "Invalid coordinate format. Expected (lat, lon)"}), 400

        except Exception as e:
            return jsonify({"error": f"Invalid coordinate format: {str(e)}"}), 400

        # Find optimal route
        route_info = graph_builder.find_optimal_route(start_coords, end_coords)

        return jsonify(route_info), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

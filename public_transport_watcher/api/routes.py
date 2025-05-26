from flask import Flask, jsonify, request
from sqlalchemy import String, func

from public_transport_watcher.api.logger import log_request
from public_transport_watcher.db.models.geography import Address, Street
from public_transport_watcher.predictor.graph_builder import GraphBuilder
from public_transport_watcher.utils import get_db_session, get_query_result

app = Flask(__name__)
graph_builder = GraphBuilder()

mapping_stations = get_query_result("mapping_stations")


@app.route("/api/v1/routes/optimal", methods=["GET"])
@log_request
def find_route():
    try:
        start_coords = request.args.get("start_coords")
        end_coords = request.args.get("end_coords")
        use_weighted = request.args.get("use_weighted")

        if not start_coords or not end_coords:
            return jsonify({"error": "Missing required parameters: start_coords or end_coords"}), 400

        try:
            start_coords = eval(start_coords)
            end_coords = eval(end_coords)

            if not (
                isinstance(start_coords, tuple)
                and len(start_coords) == 2
                and isinstance(end_coords, tuple)
                and len(end_coords) == 2
            ):
                return jsonify({"error": "Invalid coordinate format. Expected (lat, lon)"}), 400

        except Exception as e:
            return jsonify({"error": f"Invalid coordinate format: {str(e)}"}), 400

        route_info = graph_builder.find_optimal_route(start_coords, end_coords, use_weighted=use_weighted)

        return jsonify(route_info), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/v1/routes/search_address_coordinates", methods=["GET"])
@log_request
def search_address_coordinates():
    try:
        search_query = request.args.get("query")

        if not search_query:
            return jsonify({"error": "Missing required parameter: query"}), 400

        limit = request.args.get("limit", 10)
        try:
            limit = int(limit)
            if limit <= 0 or limit > 100:
                limit = 10
        except ValueError:
            limit = 10

        session = get_db_session()

        try:
            search_words = search_query.lower().split()
            search_pattern = f"%{'%'.join(search_words)}%"

            results = (
                session.query(Address.number, Street.name, Street.arrondissement, Address.latitude, Address.longitude)
                .join(Street, Address.street_id == Street.id)
                .filter(
                    func.concat(
                        func.coalesce(Address.number, ""),
                        " ",
                        func.coalesce(Street.name, ""),
                        " ",
                        func.coalesce(Street.arrondissement.cast(String), ""),
                    ).ilike(search_pattern)
                )
                .filter(
                    Address.latitude.isnot(None),
                    Address.longitude.isnot(None),
                )
                .order_by(func.concat(Address.number, Street.name, Street.arrondissement))
                .limit(limit)
                .all()
            )

            addresses = []
            for result in results:
                number, street_name, arrondissement, lat, lon = result

                address_parts = []
                if number:
                    address_parts.append(str(number))
                if street_name:
                    address_parts.append(street_name)
                if arrondissement:
                    address_parts.append(f"{arrondissement}e arrondissement")

                address_string = " ".join(address_parts)

                addresses.append(
                    {
                        "address": address_string,
                        "latitude": float(lat) if lat else None,
                        "longitude": float(lon) if lon else None,
                    }
                )

            return jsonify({"addresses": addresses, "total_found": len(addresses)}), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

import random
import time
from typing import Any, Dict, List, Optional

import requests


def _make_api_call(params: dict) -> Optional[Dict[Any, Any]]:
    """
    Make API calls to the public transport watcher endpoints.

    Args:
        params: Dictionary containing:
            - 'endpoint': str - Either 'optimal_route' or 'search_address'
            - 'base_url': str - Base URL of your Flask app (e.g., 'http://localhost:5000')
            - Other endpoint-specific parameters

    Returns:
        Dictionary with API response or None if request fails
    """
    endpoint = params.get("endpoint")
    base_url = params.get("base_url", "http://localhost:5000")

    if not endpoint:
        raise ValueError("Missing required parameter: endpoint")

    try:
        if endpoint == "optimal_route":
            url = f"{base_url}/api/v1/routes/optimal"
            query_params = {
                "start_coords": params.get("start_coords"),
                "end_coords": params.get("end_coords"),
                "use_weighted": params.get("use_weighted"),
            }
            query_params = {k: v for k, v in query_params.items() if v is not None}

            response = requests.get(url, params=query_params)

        elif endpoint == "search_address":
            url = f"{base_url}/api/v1/routes/search_address_coordinates"
            query_params = {"query": params.get("query"), "limit": params.get("limit", 10)}
            query_params = {k: v for k, v in query_params.items() if v is not None}

            response = requests.get(url, params=query_params)

        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else None,
            "success": response.status_code < 400,
        }

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {"status_code": 500, "response": None, "success": False, "error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"status_code": 500, "response": None, "success": False, "error": str(e)}


def generate_valid_coordinates() -> List[str]:
    """Generate valid Paris coordinates as strings."""
    paris_coords = [
        "(48.8566, 2.3522)",  # Notre-Dame
        "(48.8584, 2.2945)",  # Eiffel Tower
        "(48.8606, 2.3376)",  # Louvre
        "(48.8738, 2.2950)",  # Arc de Triomphe
        "(48.8529, 2.3499)",  # Latin Quarter
        "(48.8867, 2.3431)",  # Montmartre
        "(48.8448, 2.3738)",  # Bastille
        "(48.8656, 2.3212)",  # Tuileries
        "(48.8416, 2.3723)",  # Marais
        "(48.8503, 2.3739)",  # République
        "(48.8323, 2.3559)",  # Panthéon
        "(48.8467, 2.3287)",  # Saint-Germain
        "(48.8690, 2.3387)",  # Opéra
        "(48.8790, 2.3470)",  # Pigalle
        "(48.8270, 2.3780)",  # Gobelins
    ]
    return paris_coords


def generate_invalid_coordinates() -> List[str]:
    """Generate invalid coordinate formats to trigger 400 errors."""
    invalid_coords = [
        "invalid_format",
        "(48.8566)",
        "(48.8566, 2.3522, extra)",
        "[48.8566, 2.3522]",
        "48.8566, 2.3522",
        "(abc, def)",
        "",
        "()",
    ]
    return invalid_coords


def generate_search_queries() -> List[str]:
    """Generate valid search queries for address search."""
    queries = [
        "rue de la paix",
        "avenue des champs elysees",
        "boulevard saint germain",
        "place de la bastille",
        "rue de rivoli",
        "avenue montaigne",
        "rue du faubourg saint honore",
        "place vendome",
        "rue saint antoine",
        "boulevard haussmann",
        "rue de la roquette",
        "avenue daumesnil",
        "rue oberkampf",
        "boulevard voltaire",
        "rue de belleville",
        "avenue parmentier",
        "rue de charonne",
        "boulevard richard lenoir",
        "rue de la republique",
        "place des vosges",
    ]
    return queries


def generate_invalid_search_queries() -> List[str]:
    """Generate invalid or empty search queries."""
    return [
        "",
        "   ",
        "xyz123nonexistent",
        "!@#$%^&*()",
    ]


def generate_seed_data(base_url: str = "http://localhost:5001", total_calls: int = 100, failure_rate: float = 0.15):
    """
    Generate seed data by making API calls.

    Args:
        base_url: Base URL of the API
        total_calls: Total number of API calls to make
        failure_rate: Percentage of calls that should fail (0.0 to 1.0)
    """
    print(f"Starting seed data generation with {total_calls} calls...")
    print(f"Target failure rate: {failure_rate:.1%}")

    valid_coords = generate_valid_coordinates()
    invalid_coords = generate_invalid_coordinates()
    valid_queries = generate_search_queries()
    invalid_queries = generate_invalid_search_queries()

    successful_calls = 0
    failed_calls = 0
    target_failures = int(total_calls * failure_rate)

    for i in range(total_calls):
        should_fail = failed_calls < target_failures and random.random() < 0.5

        endpoint_type = random.choice(["optimal_route", "search_address"])

        try:
            if endpoint_type == "optimal_route":
                if should_fail:
                    params = {
                        "endpoint": "optimal_route",
                        "base_url": base_url,
                        "start_coords": random.choice(invalid_coords),
                        "end_coords": random.choice(valid_coords),
                        "use_weighted": random.choice(["true", "false"]),
                    }
                else:
                    params = {
                        "endpoint": "optimal_route",
                        "base_url": base_url,
                        "start_coords": random.choice(valid_coords),
                        "end_coords": random.choice(valid_coords),
                        "use_weighted": random.choice(["true", "false", None]),
                    }

            else:
                if should_fail:
                    params = {
                        "endpoint": "search_address",
                        "base_url": base_url,
                        "query": random.choice(invalid_queries),
                        "limit": random.choice([5, 10, 20, -1, "invalid"]),  # -1 and 'invalid' might cause issues
                    }
                else:
                    params = {
                        "endpoint": "search_address",
                        "base_url": base_url,
                        "query": random.choice(valid_queries),
                        "limit": random.choice([5, 10, 20, 50]),
                    }

            print(f"Call {i + 1}/{total_calls}: {endpoint_type} ({'FAIL' if should_fail else 'SUCCESS'})")
            result = _make_api_call(params)

            if result:
                if result["success"]:
                    successful_calls += 1
                    print(f"  ✓ Status: {result['status_code']}")
                else:
                    failed_calls += 1
                    print(f"  ✗ Status: {result['status_code']}")
            else:
                failed_calls += 1
                print("  ✗ Request failed completely")

            time.sleep(random.uniform(0.1, 2.0))

        except Exception as e:
            failed_calls += 1
            print(f"  ✗ Exception: {e}")

    print("\nSeed data generation completed!")
    print(f"Total calls: {total_calls}")
    print(f"Successful calls: {successful_calls}")
    print(f"Failed calls: {failed_calls}")
    print(f"Actual failure rate: {failed_calls / total_calls:.1%}")
    print("\nCheck your database logs in the 'services' schema for the generated data.")


if __name__ == "__main__":
    BASE_URL = "http://localhost:5001"
    TOTAL_CALLS = 100
    FAILURE_RATE = 0.15

    generate_seed_data(base_url=BASE_URL, total_calls=TOTAL_CALLS, failure_rate=FAILURE_RATE)

import requests
import os
from dotenv import load_dotenv

load_dotenv()


def fetch_generic_api_data(url, headers=None, params=None, method="GET"):
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            raise ValueError("Méthode HTTP non supportée.")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête API: {e}")
        return None

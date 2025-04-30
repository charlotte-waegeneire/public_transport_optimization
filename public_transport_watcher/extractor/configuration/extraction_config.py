EXTRACTION_CONFIG = {
    "navigo": {
        "files": {
            2022: ["s1", "s2"],
            2023: ["s1", "s2"],
            2024: ["s1", {"s2": ["3", "4"]}],
        },
        "batch_size": 100000,
    },
    "stations": {
        "batch_size": 100,
    },
    "addresses": {
        "batch_size": 1000,
    },
    "pollution": {
        "pollutants": ["NO2", "O3", "PM2.5"],
        "limits": {
            # See https://www.airparif.fr/la-reglementation-en-france
            "NO2": 40,
            "O3": 120,
            "PM2.5": 25,
        },
    },
    "weather": {
        "station": "ME099",
    },
    "schedule": {
        "batch_size": 5000,
    },
}

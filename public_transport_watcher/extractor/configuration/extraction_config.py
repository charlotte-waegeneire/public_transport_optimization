EXTRACTION_CONFIG = {
    "navigo": {
        "files": {
            2022: ["s1", "s2"],
            2023: ["s1", "s2"],
            2024: ["s1", {"s2": ["3", "4"]}],
        },
        "batch_size": 50000,
    },
    "stations": {
        "batch_size": 100,
    },
    "addresses": {
        "batch_size": 1000,
    },
}

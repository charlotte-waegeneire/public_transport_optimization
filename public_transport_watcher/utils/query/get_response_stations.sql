WITH deduplicated_logs AS (
    SELECT DISTINCT ON (
        response::json->'route_info'->'segments'->0->>'from_station_name',
        response::json->'route_info'->'segments'->-1->>'to_station_name',
        DATE_TRUNC('second', timestamp)
    )
    response::json->'route_info'->'segments'->0->>'from_station_name' as departure_station,
    response::json->'route_info'->'segments'->-1->>'to_station_name' as arrival_station
    FROM services.log
    WHERE request_path = '/api/v1/routes/optimal'
        AND response IS NOT NULL
        AND response ~ '^\s*\{'
        AND response::json->'route_info' IS NOT NULL
    ORDER BY
        response::json->'route_info'->'segments'->0->>'from_station_name',
        response::json->'route_info'->'segments'->-1->>'to_station_name',
        DATE_TRUNC('second', timestamp),
        timestamp DESC
),
station_usage AS (
    SELECT
        departure_station as station_name,
        COUNT(*) as count_usage,
        'departure' as usage_type
    FROM deduplicated_logs
    WHERE departure_station IS NOT NULL
    GROUP BY departure_station

    UNION ALL

    SELECT
        arrival_station as station_name,
        COUNT(*) as count_usage,
        'arrival' as usage_type
    FROM deduplicated_logs
    WHERE arrival_station IS NOT NULL
    GROUP BY arrival_station
)
SELECT
    station_name,
    COALESCE(SUM(CASE WHEN usage_type = 'departure' THEN count_usage END), 0) as departures,
    COALESCE(SUM(CASE WHEN usage_type = 'arrival' THEN count_usage END), 0) as arrivals
FROM station_usage
WHERE station_name IS NOT NULL
GROUP BY station_name
ORDER BY (COALESCE(SUM(CASE WHEN usage_type = 'departure' THEN count_usage END), 0) +
          COALESCE(SUM(CASE WHEN usage_type = 'arrival' THEN count_usage END), 0)) DESC;
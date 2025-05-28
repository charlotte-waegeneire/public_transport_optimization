WITH hourly_traffic AS (
    SELECT
        EXTRACT(DOW FROM timestamp) as day_of_week,
        EXTRACT(HOUR FROM timestamp) as hour_of_day,
        COUNT(CASE WHEN request_path = '/api/v1/routes/optimal' THEN 1 END) as requests_count
    FROM services.log
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY EXTRACT(DOW FROM timestamp), EXTRACT(HOUR FROM timestamp)
),
peak_traffic AS (
    SELECT
        day_of_week as peak_day,
        hour_of_day as peak_hour,
        requests_count as max_requests,
        ROW_NUMBER() OVER (ORDER BY requests_count DESC) as rn
    FROM hourly_traffic
)
SELECT
    peak_day,
    peak_hour,
    max_requests
FROM peak_traffic
WHERE rn = 1;
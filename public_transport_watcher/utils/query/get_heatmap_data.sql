SELECT
    EXTRACT(DOW FROM timestamp) as day_of_week,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    COUNT(*) as requests
FROM services.log
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(DOW FROM timestamp), EXTRACT(HOUR FROM timestamp)
ORDER BY day_of_week, hour_of_day;
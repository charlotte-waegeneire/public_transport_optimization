SELECT
    EXTRACT(DOW FROM tb.start_timestamp) as day_of_week,
    EXTRACT(HOUR FROM tb.start_timestamp) as hour_bin,
    AVG(t.validations) as avg_validations,
    SUM(t.validations) as total_validations
FROM transport.traffic t
JOIN transport.time_bin tb ON t.time_bin_id = tb.id
WHERE t.validations IS NOT NULL
GROUP BY EXTRACT(DOW FROM tb.start_timestamp), EXTRACT(HOUR FROM tb.start_timestamp)
ORDER BY day_of_week, hour_bin;
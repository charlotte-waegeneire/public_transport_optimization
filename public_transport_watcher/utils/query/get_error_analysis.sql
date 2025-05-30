SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    s.code as error_type,
    COUNT(*) as error_count
FROM services.log l
JOIN services.status s ON l.status_id = s.id
WHERE s.code >= 400
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), s.code
ORDER BY hour, s.code;
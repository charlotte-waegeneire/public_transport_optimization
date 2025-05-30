SELECT
    s.code,
    s.description,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(l.execution_time)::numeric, 2) as avg_response_time
FROM services.log l
JOIN services.status s ON l.status_id = s.id
WHERE s.code >= 400
AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY s.code, s.description
ORDER BY error_count DESC;
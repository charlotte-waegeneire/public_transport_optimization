SELECT
    request_path,
    m.name as method,
    ROUND(AVG(execution_time)::numeric, 3) as avg_time,
    ROUND(MAX(execution_time)::numeric, 3) as max_time
FROM services.log l
JOIN services.method m ON l.method_id = m.id
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY request_path, m.name
HAVING COUNT(*) >= 10
ORDER BY avg_time DESC
LIMIT 10;
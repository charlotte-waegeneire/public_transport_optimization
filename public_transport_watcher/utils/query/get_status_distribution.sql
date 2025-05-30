SELECT
    s.code,
    s.description,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM services.log l
JOIN services.status s ON l.status_id = s.id
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY s.code, s.description
ORDER BY count DESC;
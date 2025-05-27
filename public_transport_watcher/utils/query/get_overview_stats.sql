SELECT
    COUNT(CASE WHEN request_path = '/api/v1/routes/optimal' THEN 1 END) as total_requests,
    COUNT(DISTINCT DATE(timestamp)) as active_days,
    AVG(execution_time) as avg_response_time,
    COUNT(DISTINCT ip_address) as unique_visitors
FROM services.log
WHERE timestamp >= NOW() - INTERVAL '7 days';
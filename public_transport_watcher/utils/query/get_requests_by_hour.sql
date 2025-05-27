WITH filtered_requests AS (
  SELECT
    timestamp,
    execution_time,
    request_path,
    LAG(timestamp) OVER (
      PARTITION BY ip_address, user_agent, request_path
      ORDER BY timestamp
    ) as prev_timestamp
  FROM services.log l
  WHERE timestamp >= NOW() - INTERVAL '24 hours'
    AND timestamp IS NOT NULL
)
SELECT
  DATE_TRUNC('hour', timestamp) as hour,
  COUNT(CASE WHEN request_path = '/api/v1/routes/optimal' THEN 1 END) as requests_count,
  AVG(execution_time) as avg_response_time
FROM filtered_requests
WHERE prev_timestamp IS NULL
   OR timestamp - prev_timestamp > INTERVAL '2 seconds'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour;
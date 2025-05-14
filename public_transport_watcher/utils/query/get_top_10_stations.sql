SELECT
    s.name AS station_name
    , COUNT(*) AS count
FROM
    transport.traffic t
JOIN
    transport.station s
ON
    t.station_id = s.id
GROUP BY
    s.name
ORDER BY
    count DESC
LIMIT 10;
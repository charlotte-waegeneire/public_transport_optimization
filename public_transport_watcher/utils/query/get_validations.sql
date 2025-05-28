SELECT
    s.name AS station_name,
    s.latitude,
    s.longitude,
    SUM(t.validations) AS validations
FROM
    transport.traffic t
JOIN
    transport.station s ON t.station_id = s.id
WHERE
    s.latitude IS NOT NULL
    AND s.longitude IS NOT NULL
    AND t.validations IS NOT NULL
GROUP BY
    s.id, s.name, s.latitude, s.longitude
ORDER BY
    validations DESC;
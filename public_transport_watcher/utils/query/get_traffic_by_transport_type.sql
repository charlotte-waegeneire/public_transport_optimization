SELECT
    c.name as transport_type,
    ts.name as station_name,
    SUM(t.validations) as total_validations,
    AVG(t.validations) as avg_validations
FROM transport.traffic t
JOIN transport.station ts ON t.station_id = ts.id
JOIN transport.schedule s ON ts.id = s.station_id
JOIN transport.transport tr ON s.transport_id = tr.id
JOIN transport.categ c ON tr.type_id = c.id
WHERE t.validations IS NOT NULL
GROUP BY c.name, ts.name
HAVING SUM(t.validations) > 1000
ORDER BY c.name, total_validations DESC;
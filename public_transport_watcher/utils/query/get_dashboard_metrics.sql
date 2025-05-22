SELECT
    (SELECT SUM(validations) FROM transport.traffic WHERE validations IS NOT NULL) as total_validations,
    (SELECT COUNT(DISTINCT station_id) FROM transport.traffic WHERE validations IS NOT NULL) as active_stations,
    (SELECT COUNT(DISTINCT tr.id)
     FROM transport.transport tr
     JOIN transport.schedule s ON tr.id = s.transport_id) as active_lines,
    (SELECT AVG(daily_total)
     FROM (
         SELECT DATE(tb.start_timestamp) as day, SUM(t.validations) as daily_total
         FROM transport.traffic t
         JOIN transport.time_bin tb ON t.time_bin_id = tb.id
         WHERE t.validations IS NOT NULL
         GROUP BY DATE(tb.start_timestamp)
     ) daily_stats) as avg_daily_validations;
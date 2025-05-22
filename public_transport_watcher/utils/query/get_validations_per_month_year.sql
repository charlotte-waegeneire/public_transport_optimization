-- SELECT
--     EXTRACT(YEAR FROM start_timestamp) AS year
--     , EXTRACT(MONTH FROM start_timestamp) AS month
--     , COUNT(*) AS count
-- FROM
--     transport.traffic t
-- JOIN
--     transport.time_bin tb
-- ON
--     t.time_bin_id = tb.id
-- GROUP BY
--     year,
--     month
-- ORDER BY
--     year,
--     month;

-- Vue pour optimiser les performances
CREATE VIEW transport.station_transport_mapping AS
SELECT DISTINCT
    station_id,
    transport_id,
    type_id
FROM transport.schedule s
JOIN transport.transport t ON s.transport_id = t.id;

SELECT
    EXTRACT(YEAR FROM tb.start_timestamp) AS year,
    EXTRACT(MONTH FROM tb.start_timestamp) AS month,
    c.name AS transport_type,
    SUM(tr.validations) AS count
FROM
    transport.traffic tr
JOIN
    transport.time_bin tb ON tr.time_bin_id = tb.id
JOIN
    transport.station_transport_mapping stm ON tr.station_id = stm.station_id
JOIN
    transport.categ c ON stm.type_id = c.id
WHERE
    tr.validations IS NOT NULL
GROUP BY
    EXTRACT(YEAR FROM tb.start_timestamp),
    EXTRACT(MONTH FROM tb.start_timestamp),
    c.name
ORDER BY
    year,
    month,
    c.name;
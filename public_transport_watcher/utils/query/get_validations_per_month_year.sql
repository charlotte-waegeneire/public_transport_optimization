SELECT
    EXTRACT(YEAR FROM start_timestamp) AS year
    , EXTRACT(MONTH FROM start_timestamp) AS month
    , COUNT(*) AS count
FROM
    transport.traffic t
JOIN
    transport.time_bin tb
ON
    t.time_bin_id = tb.id
GROUP BY
    year,
    month
ORDER BY
    year,
    month;
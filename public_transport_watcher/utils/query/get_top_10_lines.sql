WITH station_traffic AS (
    SELECT
        station_id,
        SUM(validations) AS total_station_validations
    FROM transport.traffic
    WHERE validations IS NOT NULL
    GROUP BY station_id
    LIMIT 1000
),
station_transport AS (
    SELECT DISTINCT
        st.station_id,
        st.total_station_validations,
        tr.id as transport_id,
        tr.name,
        c.name as categ_name
    FROM station_traffic st
    JOIN transport.schedule sch ON sch.station_id = st.station_id
    JOIN transport.transport tr ON sch.transport_id = tr.id
    LEFT JOIN transport.categ c ON tr.type_id = c.id
),
ranked_lines AS (
    SELECT
        COALESCE(name, CONCAT(categ_name, ' ', transport_id)) AS line_name,
        SUM(total_station_validations) AS total_validations
    FROM station_transport
    GROUP BY transport_id, name, categ_name
    ORDER BY SUM(total_station_validations) DESC
    LIMIT 10
)
SELECT
    ROW_NUMBER() OVER (ORDER BY total_validations DESC) as rank,
    CONCAT(ROW_NUMBER() OVER (ORDER BY total_validations DESC), '. ', line_name) AS line_name_ranked,
    line_name,
    total_validations
FROM ranked_lines
ORDER BY rank;
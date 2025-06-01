WITH date_range AS (
            SELECT generate_series(
                DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months'),
                DATE_TRUNC('month', CURRENT_DATE),
                '1 month'::interval
            )::date as month
        ),
        traffic_data AS (
            SELECT
                DATE_TRUNC('month', tb.start_timestamp::date) as month,
                COUNT(*) as traffic_records
            FROM transport.traffic t
            JOIN transport.time_bin tb ON t.time_bin_id = tb.id
            WHERE tb.start_timestamp::date >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', tb.start_timestamp::date)
        )
        SELECT
            dr.month,
            COALESCE(td.traffic_records, 0) as traffic_records,
            (SELECT COUNT(*) FROM transport.schedule) as schedule_records,  -- Total constant
            CASE WHEN td.traffic_records > 0 THEN 1 ELSE 0 END as has_traffic,
            CASE WHEN (SELECT COUNT(*) FROM transport.schedule) > 0 THEN 1 ELSE 0 END as has_schedule
        FROM date_range dr
        LEFT JOIN traffic_data td ON dr.month = td.month
        ORDER BY dr.month DESC;
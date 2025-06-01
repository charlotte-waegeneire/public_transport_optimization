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
        ),
        schedule_data AS (
            SELECT
                DATE_TRUNC('month', CURRENT_DATE) as month,
                COUNT(*) as schedule_records
            FROM transport.schedule s
            WHERE s.id IS NOT NULL
        )
        SELECT
            dr.month,
            COALESCE(td.traffic_records, 0) as traffic_records,
            COALESCE(sd.schedule_records, 0) as schedule_records,
            CASE WHEN td.traffic_records > 0 THEN 1 ELSE 0 END as has_traffic,
            CASE WHEN sd.schedule_records > 0 THEN 1 ELSE 0 END as has_schedule
        FROM date_range dr
        LEFT JOIN traffic_data td ON dr.month = td.month
        CROSS JOIN schedule_data sd
        ORDER BY dr.month DESC;
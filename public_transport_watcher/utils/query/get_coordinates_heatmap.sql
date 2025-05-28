WITH config AS (
                SELECT
                    48.815::FLOAT as paris_lat_min,
                    48.902::FLOAT as paris_lat_max,
                    2.224::FLOAT as paris_lon_min,
                    2.469::FLOAT as paris_lon_max,
                    30 as days_back,
                    2 as min_requests_per_point
            ),
            coordinate_extraction AS (
                SELECT
                    r.log_id,
                    p.name as param_name,
                    p.value,
                    CAST(
                        TRIM(split_part(split_part(p.value, '(', 2), ',', 1))
                        AS FLOAT
                    ) as latitude,
                    CAST(
                        TRIM(split_part(split_part(p.value, ',', 2), ')', 1))
                        AS FLOAT
                    ) as longitude
                FROM services.request r
                JOIN services.parameter p ON r.parameter_id = p.id
                WHERE p.name IN ('start_coords', 'end_coords')
                AND p.value LIKE '(%%,%%)'
            ),
            all_coordinates AS (
                SELECT
                    ce.log_id,
                    ce.latitude,
                    ce.longitude,
                    l.timestamp,
                    c.min_requests_per_point
                FROM coordinate_extraction ce
                JOIN services.log l ON ce.log_id = l.id
                CROSS JOIN config c
                WHERE ce.latitude IS NOT NULL
                AND ce.longitude IS NOT NULL
                AND ce.latitude BETWEEN c.paris_lat_min AND c.paris_lat_max
                AND ce.longitude BETWEEN c.paris_lon_min AND c.paris_lon_max
                AND l.timestamp >= NOW() - INTERVAL '1 day' * c.days_back
            )
            SELECT
                ROUND(latitude::numeric, 4) as latitude,
                ROUND(longitude::numeric, 4) as longitude,
                COUNT(*) as request_count
            FROM all_coordinates
            GROUP BY ROUND(latitude::numeric, 4), ROUND(longitude::numeric, 4)
            HAVING COUNT(*) >= (SELECT min_requests_per_point FROM config LIMIT 1)
            ORDER BY request_count DESC;
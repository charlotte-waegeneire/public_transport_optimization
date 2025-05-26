SELECT
    t.id as transport_id,
    t.name as transport_name
FROM transport.categ c
    JOIN transport.transport t ON c.id = t.type_id
ORDER BY t.id;
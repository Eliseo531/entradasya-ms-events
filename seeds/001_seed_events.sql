-- Seeds: 001_seed_events.sql
-- Base de datos: events_db
-- Descripción: Eventos y sectores de prueba para entorno de desarrollo y pruebas de integración

-- Evento 1: Concierto de Rock Nacional (PUBLISHED)
INSERT INTO events (id, organizer_id, title, description, venue, event_date, image_url, status)
VALUES (
    'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
    '11111111-1111-1111-1111-111111111111',
    'Concierto de Rock Nacional',
    'Gran concierto de bandas locales de rock y artistas invitados.',
    'Teatro al Aire Libre',
    '2026-12-15 20:00:00+00',
    'https://images.unsplash.com/photo-1470225620780-dba8ba36b745',
    'PUBLISHED'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    venue = EXCLUDED.venue,
    event_date = EXCLUDED.event_date,
    image_url = EXCLUDED.image_url,
    status = EXCLUDED.status;

-- Sectores para Evento 1
INSERT INTO sectors (id, event_id, name, capacity, available_spots, price)
VALUES
    ('3f2e1d0c-4b5a-6a7b-8c9d-0e1f2a3b4c5d', 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'VIP', 150, 150, 200.00),
    ('4f2e1d0c-4b5a-6a7b-8c9d-0e1f2a3b4c5e', 'b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d', 'General', 500, 500, 80.00)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    capacity = EXCLUDED.capacity,
    available_spots = EXCLUDED.available_spots,
    price = EXCLUDED.price;

-- Evento 2: Festival Internacional de Jazz (PUBLISHED)
INSERT INTO events (id, organizer_id, title, description, venue, event_date, image_url, status)
VALUES (
    'c2b3a4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d',
    '11111111-1111-1111-1111-111111111111',
    'Festival Internacional de Jazz',
    'Tres noches del mejor jazz contemporáneo y fusión latinoamericana.',
    'Centro Cultural Central',
    '2026-11-28 19:30:00+00',
    'https://images.unsplash.com/photo-1511192336575-5a79af67a629',
    'PUBLISHED'
) ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    status = EXCLUDED.status;

-- Sectores para Evento 2
INSERT INTO sectors (id, event_id, name, capacity, available_spots, price)
VALUES
    ('5a6b7c8d-9e0f-1a2b-3c4d-5e6f7a8b9c0d', 'c2b3a4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d', 'Platea Baja', 200, 200, 150.00),
    ('6b7c8d9e-0f1a-2b3c-4d5e-6f7a8b9c0d1e', 'c2b3a4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d', 'Platea Alta', 300, 300, 90.00)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    capacity = EXCLUDED.capacity,
    available_spots = EXCLUDED.available_spots,
    price = EXCLUDED.price;

-- Evento 3: Conferencia Tecnológica DevSecOps 2026 (DRAFT)
INSERT INTO events (id, organizer_id, title, description, venue, event_date, image_url, status)
VALUES (
    'd3c4b5a6-e7f8-9a0b-1c2d-3e4f5a6b7c8d',
    '11111111-1111-1111-1111-111111111111',
    'Conferencia Tecnológica DevSecOps 2026',
    'Tendencias en seguridad en el ciclo de vida del software y cloud native.',
    'Auditorio Paraninfo Universitario',
    '2026-12-05 09:00:00+00',
    'https://images.unsplash.com/photo-1540575467063-178a50c2df87',
    'DRAFT'
) ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status;

-- Sector para Evento 3
INSERT INTO sectors (id, event_id, name, capacity, available_spots, price)
VALUES
    ('7c8d9e0f-1a2b-3c4d-5e6f-7a8b9c0d1e2f', 'd3c4b5a6-e7f8-9a0b-1c2d-3e4f5a6b7c8d', 'Entrada General', 350, 350, 50.00)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    capacity = EXCLUDED.capacity,
    available_spots = EXCLUDED.available_spots,
    price = EXCLUDED.price;

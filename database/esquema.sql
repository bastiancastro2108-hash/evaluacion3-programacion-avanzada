-- =====================================================================
-- EVALUACIÓN N°3 · Programación Avanzada · I CRIM Sistemas de Armas
-- Script de base de datos (Supabase / PostgreSQL)
-- Crea las tablas, sus relaciones y carga los 10 ingredientes y 10 recetas.
-- =====================================================================

-- Se eliminan en orden inverso a sus dependencias para poder re-ejecutar
DROP TABLE IF EXISTS orden_detalle CASCADE;
DROP TABLE IF EXISTS ordenes CASCADE;
DROP TABLE IF EXISTS receta_ingredientes CASCADE;
DROP TABLE IF EXISTS recetas CASCADE;
DROP TABLE IF EXISTS ingredientes CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- ---------------------------------------------------------------------
-- 1. CATÁLOGO DE INGREDIENTES (tabla entregada en el ejercicio)
-- porciones_unidad = cuántas porciones (personas) rinde 1 unidad de compra
-- Ajustes indicados en clase: cebolla = 4 personas, tomate = 4 personas por kg.
-- ---------------------------------------------------------------------
CREATE TABLE ingredientes (
    id                SERIAL PRIMARY KEY,
    nombre            VARCHAR(50) UNIQUE NOT NULL,
    costo             INT NOT NULL CHECK (costo > 0),             -- $ por unidad de compra
    unidad_compra     VARCHAR(20) NOT NULL,                       -- unidad, paquete, kg, litro, empaque
    utilidad          VARCHAR(50) NOT NULL,                       -- texto original de la tabla
    porciones_unidad  INT NOT NULL CHECK (porciones_unidad > 0)   -- rendimiento en porciones
);

INSERT INTO ingredientes (nombre, costo, unidad_compra, utilidad, porciones_unidad) VALUES
('Cebolla',       500,  'unidad',  '4 personas',              4),
('Arroz',         1500, 'paquete', '10 personas por paquete', 10),
('Tuto de pollo', 1200, 'unidad',  '1 por persona',           1),
('Carne molida',  1500, 'paquete', '4 personas por paquete',  4),
('Papa',          1000, 'kg',      '4 personas por kg',       4),
('Tomate',        1500, 'kg',      '4 personas por kg',       4),
('Fideos',        1200, 'paquete', '4 personas por paquete',  4),
('Lechuga',       1000, 'unidad',  '10 personas por lechuga', 10),
('Huevo',         4500, 'empaque', '12 personas por empaque', 12),
('Aceite',        1000, 'litro',   '10 personas por litro',   10);

-- ---------------------------------------------------------------------
-- 2. RECETAS Y SUS INGREDIENTES (relación N a N)
-- Una receta tiene varios ingredientes y un ingrediente está en varias recetas.
-- ---------------------------------------------------------------------
CREATE TABLE recetas (
    id               SERIAL PRIMARY KEY,
    nombre           VARCHAR(80) UNIQUE NOT NULL,
    base_comensales  INT NOT NULL DEFAULT 4 CHECK (base_comensales > 0)
);

CREATE TABLE receta_ingredientes (
    id              SERIAL PRIMARY KEY,
    receta_id       INT NOT NULL REFERENCES recetas(id) ON DELETE CASCADE,
    ingrediente_id  INT NOT NULL REFERENCES ingredientes(id),
    porciones       INT NOT NULL CHECK (porciones > 0),   -- porciones usadas para base_comensales
    UNIQUE (receta_id, ingrediente_id)
);

INSERT INTO recetas (nombre) VALUES
('Arroz con Pollo y Ensalada'),
('Carne Molida con Papas'),
('Tallarines con Salsa de Tomate'),
('Tortilla de Papas y Cebolla'),
('Pollo Salteado con Verduras'),
('Charquican Simple'),
('Fideos con Huevo y Tomate'),
('Carne Molida con Arroz y Ensalada'),
('Papas Cocidas con Huevo y Lechuga'),
('Arroz Graneado con Huevo y Cebolla');

-- Cantidades en PORCIONES para 4 comensales, según cada receta.
-- Lechuga y cebolla: la receta dice "1 unidad"; se registran como 4 porciones
-- (1 por comensal), criterio indicado en clase.
-- "Pollo (trutro/pechuga)" de las recetas corresponde a "Tuto de pollo".
-- Se insertan por NOMBRE (no por id) para que el script sea legible.
INSERT INTO receta_ingredientes (receta_id, ingrediente_id, porciones)
SELECT r.id, i.id, v.porciones
FROM (VALUES
    ('Arroz con Pollo y Ensalada',        'Tuto de pollo', 4),
    ('Arroz con Pollo y Ensalada',        'Arroz',         4),
    ('Arroz con Pollo y Ensalada',        'Lechuga',       4),
    ('Arroz con Pollo y Ensalada',        'Aceite',        4),
    ('Carne Molida con Papas',            'Carne molida',  4),
    ('Carne Molida con Papas',            'Papa',          6),
    ('Carne Molida con Papas',            'Cebolla',       4),
    ('Carne Molida con Papas',            'Aceite',        4),
    ('Tallarines con Salsa de Tomate',    'Fideos',        4),
    ('Tallarines con Salsa de Tomate',    'Tomate',        4),
    ('Tallarines con Salsa de Tomate',    'Cebolla',       4),
    ('Tallarines con Salsa de Tomate',    'Aceite',        4),
    ('Tortilla de Papas y Cebolla',       'Papa',          6),
    ('Tortilla de Papas y Cebolla',       'Cebolla',       4),
    ('Tortilla de Papas y Cebolla',       'Huevo',         6),
    ('Tortilla de Papas y Cebolla',       'Aceite',        4),
    ('Pollo Salteado con Verduras',       'Tuto de pollo', 4),
    ('Pollo Salteado con Verduras',       'Tomate',        3),
    ('Pollo Salteado con Verduras',       'Cebolla',       4),
    ('Pollo Salteado con Verduras',       'Aceite',        4),
    ('Charquican Simple',                 'Papa',          6),
    ('Charquican Simple',                 'Lechuga',       4),
    ('Charquican Simple',                 'Cebolla',       4),
    ('Charquican Simple',                 'Aceite',        4),
    ('Fideos con Huevo y Tomate',         'Fideos',        4),
    ('Fideos con Huevo y Tomate',         'Huevo',         4),
    ('Fideos con Huevo y Tomate',         'Tomate',        3),
    ('Fideos con Huevo y Tomate',         'Aceite',        4),
    ('Carne Molida con Arroz y Ensalada', 'Carne molida',  4),
    ('Carne Molida con Arroz y Ensalada', 'Arroz',         4),
    ('Carne Molida con Arroz y Ensalada', 'Lechuga',       4),
    ('Carne Molida con Arroz y Ensalada', 'Tomate',        2),
    ('Papas Cocidas con Huevo y Lechuga', 'Papa',          6),
    ('Papas Cocidas con Huevo y Lechuga', 'Huevo',         4),
    ('Papas Cocidas con Huevo y Lechuga', 'Lechuga',       4),
    ('Papas Cocidas con Huevo y Lechuga', 'Aceite',        4),
    ('Arroz Graneado con Huevo y Cebolla','Arroz',         4),
    ('Arroz Graneado con Huevo y Cebolla','Huevo',         4),
    ('Arroz Graneado con Huevo y Cebolla','Cebolla',       4),
    ('Arroz Graneado con Huevo y Cebolla','Aceite',        4)
) AS v(receta, ingrediente, porciones)
JOIN recetas r      ON r.nombre = v.receta
JOIN ingredientes i ON i.nombre = v.ingrediente;

-- ---------------------------------------------------------------------
-- 3. ÓRDENES DE SERVICIO Y DETALLE DE MERMAS
-- ordenes: un registro por servicio (menú + comensales + totales + estado)
-- orden_detalle: un registro por ingrediente de esa orden
-- ---------------------------------------------------------------------
CREATE TABLE ordenes (
    id               SERIAL PRIMARY KEY,
    fecha            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    receta_id        INT NOT NULL REFERENCES recetas(id),
    comensales       INT NOT NULL CHECK (comensales > 0),
    costo_total      NUMERIC(12,2) NOT NULL,
    costo_por_plato  NUMERIC(12,2) NOT NULL,
    precio_venta     NUMERIC(12,2) NOT NULL,     -- por plato, con 25% de ganancia
    perdida_merma    NUMERIC(12,2) NOT NULL,     -- suma de la pérdida de todos los ingredientes
    usuario          VARCHAR(30) NOT NULL,
    -- Ciclo de vida: la orden nace 'pendiente' y pasa a 'preparada' cuando cocina
    -- la termina. Solo las preparadas cuentan en las métricas del administrador.
    estado             VARCHAR(12) NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente', 'preparada')),
    fecha_preparacion  TIMESTAMP WITH TIME ZONE
);

CREATE TABLE orden_detalle (
    id              SERIAL PRIMARY KEY,
    orden_id        INT NOT NULL REFERENCES ordenes(id) ON DELETE CASCADE,
    ingrediente_id  INT NOT NULL REFERENCES ingredientes(id),
    porciones_usadas  INT NOT NULL,              -- porciones a usar (redondeadas hacia arriba)
    unidades          INT NOT NULL,              -- unidades de compra enteras (math.ceil)
    merma             INT NOT NULL,              -- porciones sobrantes
    costo           NUMERIC(12,2) NOT NULL,      -- compra × costo unitario
    perdida         NUMERIC(12,2) NOT NULL       -- valor en $ de la merma
);

-- ---------------------------------------------------------------------
-- 4. USUARIOS Y ROLES
-- La clave se guarda como hash SHA-256 (nunca en texto plano).
-- Los usuarios se crean aparte, en el SQL Editor, para no dejar claves en el repositorio.
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id          SERIAL PRIMARY KEY,
    usuario     VARCHAR(30) UNIQUE NOT NULL,
    clave_hash  CHAR(64) NOT NULL,
    rol         VARCHAR(20) NOT NULL CHECK (rol IN ('cocina', 'administrador'))
);

-- ---------------------------------------------------------------------
-- 5. PERMISOS PARA LA API
-- Los proyectos nuevos de Supabase no dan acceso automático a las tablas
-- creadas por SQL. Se concede SOLO a service_role (la key secreta que usa
-- la app desde el servidor). Las keys públicas (anon) quedan sin acceso.
-- Las SEQUENCES se necesitan para que los SERIAL generen ids al insertar.
-- ---------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
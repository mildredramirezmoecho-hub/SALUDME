-- =====================================================================
-- Migración: añade la columna de preparación a la tabla 'recetas'
-- Base de datos: SaludMe
-- Este script SOLO es necesario si la aplicación no pudo crear la
-- columna automáticamente al arrancar (ver app.py).
-- =====================================================================

USE SaludMe;

-- Comprobar antes de ejecutar que la columna no exista:
-- SELECT COUNT(*) FROM information_schema.COLUMNS
--  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recetas'
--    AND COLUMN_NAME = 'instrucciones';

ALTER TABLE recetas ADD COLUMN instrucciones TEXT NULL AFTER ingredientes;

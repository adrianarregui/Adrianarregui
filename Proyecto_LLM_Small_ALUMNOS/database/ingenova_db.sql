CREATE DATABASE IF NOT EXISTS ingenova_db;
USE ingenova_db;

CREATE TABLE IF NOT EXISTS edificios_datacenter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(100) NOT NULL,
    capacidad_racks INT NOT NULL,
    consumo_electrico_mw DECIMAL(5,2) NOT NULL,
    estado_operativo VARCHAR(20) NOT NULL
);

TRUNCATE TABLE edificios_datacenter;

INSERT INTO edificios_datacenter (nombre, ubicacion, capacidad_racks, consumo_electrico_mw, estado_operativo) VALUES
('Edificio A', 'Madrid Norte', 1200, 15.50, 'ACTIVO'),
('Edificio B', 'Madrid Sur', 800, 10.20, 'ACTIVO'),
('Edificio C', 'Barcelona', 2500, 32.00, 'ACTIVO'),
('Edificio D', 'Valencia', 500, 6.50, 'MANTENIMIENTO'),
('Edificio E', 'Sevilla', 1500, 20.00, 'ACTIVO'),
('Edificio F', 'Bilbao', 900, 11.80, 'CONSTRUCCION');

-- Fernando 28/04/2024

-- Crear tabla Personas
CREATE TABLE Personas (
    documento INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    telefono VARCHAR(20),
    observaciones TEXT,
    tipo_persona VARCHAR(20) NOT NULL
);

-- Crear tabla Pedidos
CREATE TABLE Pedidos (
    id_pedido SERIAL PRIMARY KEY,
    usuario_documento INT REFERENCES Personas(documento),
    direccion_origen VARCHAR(255),
    direccion_destino VARCHAR(255),
    latitud_origen FLOAT,
    latitud_destino FLOAT,
    longitud_origen FLOAT,
    longitud_destino FLOAT,
    ventana_origen_start TIMESTAMP,
    ventana_origen_end TIMESTAMP,
    ventana_destino_start TIMESTAMP,
    ventana_destino_end TIMESTAMP,
    hora_ingresado TIMESTAMP NOT NULL,
    prioridad INT NOT NULL CHECK (prioridad >= 1),
    acompañante BOOLEAN NOT NULL,
    observaciones TEXT
);

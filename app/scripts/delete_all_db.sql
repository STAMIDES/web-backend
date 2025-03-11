--no borra usuarios

DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Desactivar temporalmente las restricciones de clave foránea
    SET session_replication_role = 'replica';

    -- Recorrer todas las tablas excepto 'usuarios' y eliminar los datos
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'usuarios') 
    LOOP
        EXECUTE 'DELETE FROM ' || quote_ident(r.tablename) || ' CASCADE;';
    END LOOP;

    -- Restaurar las restricciones de clave foránea
    SET session_replication_role = 'origin';
END $$;

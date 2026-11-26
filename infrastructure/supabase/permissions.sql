-- Ejecutar como postgres después de las migraciones de SRC, antes de habilitar el servidor.
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'src_app') THEN
        CREATE ROLE src_app NOLOGIN;
    END IF;
END;
$$;

ALTER ROLE src_app SET statement_timeout = '3s';

REVOKE ALL ON TABLE public.users, public.sessions, public.rooms,
    public.room_members, public.schedules, public.schedule_blocks, public.alembic_version
FROM PUBLIC, anon, authenticated, service_role;

GRANT USAGE ON SCHEMA public TO src_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.users, public.sessions, public.rooms,
    public.room_members, public.schedules, public.schedule_blocks TO src_app;
GRANT SELECT ON TABLE public.alembic_version TO src_app;

CREATE SCHEMA IF NOT EXISTS src_auth;
REVOKE ALL ON SCHEMA src_auth FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA src_auth TO src_app;

CREATE OR REPLACE FUNCTION src_auth.identity_id(confirmed_email text)
RETURNS uuid LANGUAGE sql STABLE STRICT SECURITY DEFINER SET search_path = ''
AS $$
    SELECT id FROM auth.users
    WHERE email = $1 AND email_confirmed_at IS NOT NULL AND deleted_at IS NULL
      AND (banned_until IS NULL OR banned_until <= pg_catalog.now());
$$;

CREATE OR REPLACE FUNCTION src_auth.identity_email(identity uuid)
RETURNS text LANGUAGE sql STABLE STRICT SECURITY DEFINER SET search_path = ''
AS $$
    SELECT email FROM auth.users
    WHERE id = $1 AND email_confirmed_at IS NOT NULL AND deleted_at IS NULL
      AND (banned_until IS NULL OR banned_until <= pg_catalog.now());
$$;

CREATE OR REPLACE FUNCTION src_auth.delete_identity(identity uuid)
RETURNS boolean LANGUAGE sql VOLATILE STRICT SECURITY DEFINER SET search_path = ''
AS $$
    WITH removed AS (
        DELETE FROM auth.users
        WHERE id = $1 AND deleted_at IS NULL
          AND NOT EXISTS (SELECT FROM public.users WHERE id = $1)
        RETURNING id
    )
    SELECT EXISTS (SELECT FROM removed);
$$;

REVOKE ALL ON FUNCTION src_auth.identity_id(text), src_auth.identity_email(uuid),
    src_auth.delete_identity(uuid) FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION src_auth.identity_id(text), src_auth.identity_email(uuid),
    src_auth.delete_identity(uuid) TO src_app;

COMMIT;

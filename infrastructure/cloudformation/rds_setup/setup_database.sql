-- https://aws.amazon.com/blogs/database/managing-postgresql-users-and-roles/
-- Revoke privileges from 'public' role
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE "appDevDb" FROM PUBLIC;

CREATE SCHEMA app;

-- Read-only role
CREATE ROLE readonly;
GRANT CONNECT ON DATABASE "appDevDb" TO readonly;
GRANT USAGE ON SCHEMA app TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO readonly;

-- Read/write role
CREATE ROLE readwrite;
GRANT CONNECT ON DATABASE "appDevDb" TO readwrite;
GRANT USAGE, CREATE ON SCHEMA app TO readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA app TO readwrite;
GRANT TEMPORARY ON DATABASE "appDevDb" TO readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO readwrite;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE ON SEQUENCES TO readwrite;

-- Users creation
CREATE USER app_ro WITH PASSWORD 'app_ro';
CREATE USER app_rw WITH PASSWORD 'app_rw';

-- Grant privileges to users
GRANT readonly TO app_ro;
GRANT readwrite TO app_rw;
ALTER DATABASE "appDevDb" SET SEARCH_PATH TO app;


-- -----------------
-- PostGIS extension
-- -----------------
create extension postgis with schema app;

--------------------
--  COPY CSV FROM S3
--------------------
CREATE EXTENSION aws_s3 CASCADE;
--GRANT USAGE ON SCHEMA aws_s3 TO readwrite;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA aws_s3 TO readwrite;

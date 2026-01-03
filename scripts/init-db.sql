-- ═══════════════════════════════════════════════════════════
-- KRONOS Database Initialization
-- Creates schemas for each microservice
-- ═══════════════════════════════════════════════════════════

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for each microservice
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS leaves;
CREATE SCHEMA IF NOT EXISTS expenses;
CREATE SCHEMA IF NOT EXISTS config;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS hr_reporting;
CREATE SCHEMA IF NOT EXISTS wallet;
CREATE SCHEMA IF NOT EXISTS time_wallet;

-- Grant privileges
GRANT ALL ON SCHEMA auth TO kronos;
GRANT ALL ON SCHEMA leaves TO kronos;
GRANT ALL ON SCHEMA expenses TO kronos;
GRANT ALL ON SCHEMA config TO kronos;
GRANT ALL ON SCHEMA notifications TO kronos;
GRANT ALL ON SCHEMA audit TO kronos;
GRANT ALL ON SCHEMA hr_reporting TO kronos;
GRANT ALL ON SCHEMA wallet TO kronos;
GRANT ALL ON SCHEMA time_wallet TO kronos;

-- Set search path
ALTER DATABASE kronos SET search_path TO public, auth, leaves, expenses, config, notifications, audit, hr_reporting, wallet, time_wallet;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'KRONOS database initialized with schemas: auth, leaves, expenses, config, notifications, audit, hr_reporting, wallet, time_wallet';
END
$$;


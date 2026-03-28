-- ═══════════════════════════════════════════════════════════════════════════
-- MiccoRAG-v2 — Auth / Admin / Dashboard schema initialisation
-- Runs automatically when PostgreSQL first starts (docker-entrypoint-initdb.d)
-- Safe to re-run: all statements use IF NOT EXISTS / ON CONFLICT DO NOTHING
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Extensions ───────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLES
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Departments ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_departments_name ON departments (name);

-- ─── Users ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(50)  NOT NULL DEFAULT 'Nhân viên',
    department_id   INTEGER      REFERENCES departments(id) ON DELETE SET NULL,
    avatar          VARCHAR(500),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email      ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role       ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_department ON users (department_id);

-- ─── Knowledge Entries (for Admin management) ─────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(500) NOT NULL,
    content_html    TEXT         NOT NULL DEFAULT '',
    content_text    TEXT         NOT NULL DEFAULT '',
    category        VARCHAR(100) NOT NULL DEFAULT 'Chung',
    tags            JSONB        NOT NULL DEFAULT '[]'::jsonb,
    owner_id        INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id   INTEGER      REFERENCES departments(id) ON DELETE SET NULL,
    visibility      VARCHAR(20)  NOT NULL DEFAULT 'internal',
    status          VARCHAR(20)  NOT NULL DEFAULT 'Active',
    ingest_status   VARCHAR(20)  DEFAULT 'pending',
    ingest_error    TEXT,
    approval_status VARCHAR(20)  NOT NULL DEFAULT 'pending_approval',
    approved_by_id  INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    approved_at     TIMESTAMPTZ,
    approval_note   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_owner  ON knowledge_entries (owner_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_entries (status);

-- ═══════════════════════════════════════════════════════════════════════════
-- DASHBOARD FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

/*
-- ─── DASHBOARD FUNCTIONS (Depends on 'documents' table) ───────────────────────────
-- These are handled by the backend migration if needed.
CREATE OR REPLACE FUNCTION get_dashboard_stats(p_department_id INTEGER DEFAULT NULL)
RETURNS TABLE (
    total_files     BIGINT,
    storage_used    BIGINT,
    recent_uploads  BIGINT,
    team_members    BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM documents WHERE p_department_id IS NULL)::BIGINT,
        (SELECT COALESCE(SUM(file_size), 0) FROM documents WHERE p_department_id IS NULL)::BIGINT,
        (SELECT COUNT(*) FROM documents WHERE created_at >= NOW() - INTERVAL '7 days')::BIGINT,
        (SELECT COUNT(*) FROM users WHERE (p_department_id IS NULL OR department_id = p_department_id))::BIGINT;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_uploads_over_time(p_department_id INTEGER DEFAULT NULL)
RETURNS TABLE (
    month_name   TEXT,
    upload_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TO_CHAR(gs.month, 'Mon') AS month_name,
        COALESCE(cnt.total, 0)::BIGINT
    FROM (
        SELECT generate_series(
            DATE_TRUNC('month', NOW()) - INTERVAL '5 months',
            DATE_TRUNC('month', NOW()),
            '1 month'::interval
        ) AS month
    ) gs
    LEFT JOIN (
        SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) AS total
        FROM documents
        WHERE p_department_id IS NULL
        GROUP BY 1
    ) cnt ON gs.month = cnt.month
    ORDER BY gs.month ASC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_storage_by_type(p_department_id INTEGER DEFAULT NULL)
RETURNS TABLE (
    doc_type    VARCHAR,
    total_bytes BIGINT,
    file_count  BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.file_type::VARCHAR,
        COALESCE(SUM(d.file_size), 0)::BIGINT,
        COUNT(*)::BIGINT
    FROM documents d
    WHERE p_department_id IS NULL
    GROUP BY d.file_type
    ORDER BY 2 DESC;
END;
$$ LANGUAGE plpgsql;

-- ─── System Chat Logs (Depends on 'knowledge_bases' table) ────────────────────────
-- Handled by backend app.main lifespan
CREATE TABLE IF NOT EXISTS system_chat_logs (
    id            SERIAL PRIMARY KEY,
    workspace_id  INTEGER      NOT NULL,
    ip_address    VARCHAR(50),
    timestamp     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    response_time FLOAT        NOT NULL,
    question      TEXT         NOT NULL,
    answer        TEXT         NOT NULL,
    method        VARCHAR(50)  NOT NULL
);
*/

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED DATA — default departments
-- ═══════════════════════════════════════════════════════════════════════════
INSERT INTO departments (name, description) VALUES
    ('Kế toán',      'Phòng Kế toán - Tài chính'),
    ('Nhân sự',      'Phòng Nhân sự'),
    ('Kỹ thuật',     'Phòng Kỹ thuật - Công nghệ'),
    ('Kinh doanh',   'Phòng Kinh doanh - Marketing'),
    ('Pháp chế',     'Phòng Pháp chế - Hợp đồng'),
    ('Ban Giám đốc', 'Ban lãnh đạo công ty')
ON CONFLICT (name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════
DO $$ BEGIN
    RAISE NOTICE '✅ MiccoRAG-v2 auth/admin/dashboard schema ready';
END $$;

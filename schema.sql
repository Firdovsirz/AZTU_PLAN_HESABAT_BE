-- AZTU Plan Hesabat — full schema (PostgreSQL)
-- Order matters: tables referenced by FKs are created first.

BEGIN;

-- ---------------------------------------------------------------
-- faculty
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faculty (
    id           SERIAL PRIMARY KEY,
    faculty_code VARCHAR   NOT NULL UNIQUE,
    faculty_name VARCHAR   NOT NULL UNIQUE,
    created_at   TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_faculty_id ON faculty (id);

-- ---------------------------------------------------------------
-- cafedras
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cafedras (
    id           SERIAL PRIMARY KEY,
    faculty_code VARCHAR   NOT NULL,
    cafedra_code VARCHAR   NOT NULL UNIQUE,
    cafedra_name VARCHAR   NOT NULL UNIQUE,
    created_at   TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_cafedras_id ON cafedras (id);

-- ---------------------------------------------------------------
-- departments
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id              SERIAL PRIMARY KEY,
    department_code VARCHAR   NOT NULL UNIQUE,
    department_name VARCHAR   NOT NULL UNIQUE,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_departments_id ON departments (id);

-- ---------------------------------------------------------------
-- duties
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS duties (
    id         SERIAL PRIMARY KEY,
    duty_code  INTEGER   NOT NULL UNIQUE,
    duty_name  VARCHAR   NOT NULL UNIQUE,
    org_type   VARCHAR   NOT NULL DEFAULT 'faculty',
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_duties_id ON duties (id);

-- ---------------------------------------------------------------
-- auth
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth (
    id         SERIAL PRIMARY KEY,
    fin_kod    VARCHAR   NOT NULL UNIQUE,
    role       INTEGER   NOT NULL,
    password   VARCHAR   NOT NULL,
    approved   BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    otp        INTEGER
);
CREATE INDEX IF NOT EXISTS ix_auth_id ON auth (id);

-- ---------------------------------------------------------------
-- users
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    fin_kod         VARCHAR   NOT NULL UNIQUE,
    email           VARCHAR   NOT NULL,
    name            VARCHAR   NOT NULL,
    surname         VARCHAR   NOT NULL,
    father_name     VARCHAR   NOT NULL,
    faculty_code    VARCHAR   REFERENCES faculty(faculty_code),
    cafedra_code    VARCHAR   REFERENCES cafedras(cafedra_code),
    department_code VARCHAR   REFERENCES departments(department_code),
    duty_code       INTEGER   NOT NULL,
    is_execution    BOOLEAN   NOT NULL DEFAULT FALSE,
    approved        BOOLEAN   DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);

-- ---------------------------------------------------------------
-- activity_types
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_types (
    id                 SERIAL PRIMARY KEY,
    activity_type_code INTEGER   NOT NULL UNIQUE,
    activity_type_name VARCHAR   NOT NULL UNIQUE,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP,
    approved           BOOLEAN   NOT NULL DEFAULT FALSE,
    fin_kod            VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_activity_types_id ON activity_types (id);

-- ---------------------------------------------------------------
-- assessment
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessment (
    id               SERIAL PRIMARY KEY,
    assessment_score INTEGER   NOT NULL UNIQUE,
    score_name       TEXT      NOT NULL,
    score_desc       TEXT      NOT NULL,
    created_at       TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_assessment_id ON assessment (id);

-- ---------------------------------------------------------------
-- work_plan
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS work_plan (
    id                      SERIAL PRIMARY KEY,
    fin_kod                 VARCHAR   NOT NULL,
    work_plan_serial_number VARCHAR   NOT NULL,
    work_year               INTEGER   NOT NULL,
    work_row_number         INTEGER   NOT NULL,
    activity_type_code      VARCHAR   NOT NULL,
    activity_type_name      VARCHAR,
    work_desc               VARCHAR,
    deadline                TIMESTAMP,
    created_at              TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_work_plan_id ON work_plan (id);

-- ---------------------------------------------------------------
-- hesabat
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hesabat (
    id                      SERIAL PRIMARY KEY,
    fin_kod                 VARCHAR NOT NULL,
    work_plan_serial_number VARCHAR,
    activity_doc_path       VARCHAR,
    done_percentage         VARCHAR,
    assessment_score        INTEGER,
    admin_assessment        INTEGER,
    ai_assessment           INTEGER,
    activity_type_code      INTEGER NOT NULL,
    activity_type_name      VARCHAR,
    submitted_at            TIMESTAMP,
    duration_analysis       INTEGER,
    note                    VARCHAR,
    submitted               BOOLEAN DEFAULT FALSE,
    done                    BOOLEAN DEFAULT FALSE,
    done_at                 TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_hesabat_id ON hesabat (id);

COMMIT;

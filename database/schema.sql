-- ============================================================
-- EAGL DATABASE SCHEMA
-- Run this file once to create the database and all tables
-- Command to run: mysql -u root -p < schema.sql
-- ============================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS eagle_db;
USE eagle_db;

-- Create a MySQL user:
CREATE USER IF NOT EXISTS 'eagle_user'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON eagle_db.* TO 'eagle_user'@'localhost';
FLUSH PRIVILEGES;

-- ============================================================
-- TABLE 1: users
-- Stores all 4 roles: admin, manager, field_coordinator, delivery_coordinator
-- manager_id is NULL for admin and manager
-- manager_id is filled for coordinators (points to their manager)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    name             VARCHAR(100),
    email            VARCHAR(100) UNIQUE,
    password         VARCHAR(255),
    role             ENUM('admin', 'manager', 'field_coordinator', 'delivery_coordinator'),
    mobile           VARCHAR(15),
    manager_id       INT,
    is_first_login   TINYINT(1) DEFAULT 1,
    created_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Note: Password here should be hashed in production using a setup script. 
-- For development, we keep this, but the application will hash new passwords.
-- Admin User password below is 'dhanu123'
INSERT IGNORE INTO users (name, email, password, role, mobile, manager_id, is_first_login) VALUES
('Admin User', 'dhanushgudivada@gmail.com', 'admin123', 'admin', NULL, NULL, 0);

-- ============================================================
-- TABLE 2: areas
-- ============================================================
CREATE TABLE IF NOT EXISTS areas (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    area_name       VARCHAR(100),
    district        VARCHAR(100),
    poverty_percent DECIMAL(5,2),
    manager_id      INT,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 3: funds
-- ============================================================
CREATE TABLE IF NOT EXISTS funds (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    manager_id    INT,
    total_amount  DECIMAL(10,2),
    spent_amount  DECIMAL(10,2) DEFAULT 0.00,
    created_at    DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 4: sub_areas
-- ============================================================
CREATE TABLE IF NOT EXISTS sub_areas (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    area_id          INT,
    sub_area_name    VARCHAR(100),
    coordinator1_id  INT,
    manager_id       INT,
    assigned_date    DATE,
    created_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (area_id)         REFERENCES areas(id) ON DELETE CASCADE,
    FOREIGN KEY (coordinator1_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id)      REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 5: attendance
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    coordinator_id  INT,
    sub_area_id     INT,
    check_in_time   DATETIME DEFAULT NOW(),
    is_present      BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sub_area_id)    REFERENCES sub_areas(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 6: beneficiaries
-- ============================================================
CREATE TABLE IF NOT EXISTS beneficiaries (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    family_name     VARCHAR(100),
    sub_area_id     INT,
    family_members  INT,
    annual_income   DECIMAL(10,2),
    collector_id    INT,
    is_approved     BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (sub_area_id)  REFERENCES sub_areas(id) ON DELETE CASCADE,
    FOREIGN KEY (collector_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 7: eligible_families
-- ============================================================
CREATE TABLE IF NOT EXISTS eligible_families (
    id                  INT PRIMARY KEY AUTO_INCREMENT,
    beneficiary_id      INT NOT NULL,
    per_capita_income   DECIMAL(10,2),
    approval_threshold  DECIMAL(10,2),
    approved_by         INT,
    approved_at         DATETIME DEFAULT NOW(),
    delivery_status     ENUM('pending', 'delivered', 'completed') DEFAULT 'pending',
    created_at          DATETIME DEFAULT NOW(),
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by)    REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 8: coordinator2_assignments
-- ============================================================
CREATE TABLE IF NOT EXISTS coordinator2_assignments (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    manager_id       INT NOT NULL,
    coordinator2_id  INT NOT NULL,
    beneficiary_id   INT NOT NULL,
    sub_area_id      INT,
    assigned_date    DATE,
    status           ENUM('pending', 'delivered', 'completed') DEFAULT 'pending',
    created_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id)       REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coordinator2_id)  REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (beneficiary_id)   REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (sub_area_id)      REFERENCES sub_areas(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 9: livestock_delivery
-- ============================================================
CREATE TABLE IF NOT EXISTS livestock_delivery (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    beneficiary_id   INT,
    coordinator2_id  INT,
    livestock_type   VARCHAR(100),
    delivered        BOOLEAN DEFAULT FALSE,
    upskill_done     BOOLEAN DEFAULT FALSE,
    notes            VARCHAR(255),
    updated_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (beneficiary_id)  REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (coordinator2_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create some indexes for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_manager ON users(manager_id);
CREATE INDEX idx_areas_manager ON areas(manager_id);
CREATE INDEX idx_sub_areas_manager ON sub_areas(manager_id);
CREATE INDEX idx_sub_areas_area ON sub_areas(area_id);
CREATE INDEX idx_beneficiaries_sub_area ON beneficiaries(sub_area_id);

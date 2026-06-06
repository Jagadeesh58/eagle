-- ============================================================
-- EAGL DATABASE SCHEMA
-- Run this file once to create the database and all tables
-- Command to run: mysql -u root -p < schema.sql
-- ============================================================

-- Create a MySQL user:
CREATE USER IF NOT EXISTS 'eagle_user'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON eagle_db.* TO 'eagle_user'@'localhost';
FLUSH PRIVILEGES;

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS eagle_db;
USE eagle_db;

-- ============================================================
-- TABLE 1: users
-- Stores all 4 roles: admin, manager, coordinator1, coordinator2
-- manager_id is NULL for admin and manager
-- manager_id is filled for coordinators (points to their manager)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100),
    email       VARCHAR(100) UNIQUE,
    password    VARCHAR(255),
    role        ENUM('admin', 'manager', 'coordinator1', 'coordinator2'),
    manager_id  INT,
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- Seed admin credentials so the system can be accessed after database creation.
INSERT IGNORE INTO users (name, email, password, role, manager_id) VALUES
('Admin User', 'dhanush@gmail.com', 'dhanu123', 'admin', NULL),
('Admin User', 'dhanushgudivada@gmail.com', 'dhanu123', 'admin', NULL);

-- ============================================================
-- TABLE 2: areas
-- Admin uploads poverty area data and assigns each area to a manager
-- poverty_percent tells how severe poverty is in that area
-- ============================================================
CREATE TABLE IF NOT EXISTS areas (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    area_name       VARCHAR(100),
    district        VARCHAR(100),
    poverty_percent DECIMAL(5,2),
    manager_id      INT,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- ============================================================
-- TABLE 3: funds
-- Admin assigns total_amount budget to each manager
-- spent_amount increases every time a livestock is delivered
-- remaining balance = total_amount - spent_amount
-- ============================================================
CREATE TABLE IF NOT EXISTS funds (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    manager_id    INT,
    total_amount  DECIMAL(10,2),
    spent_amount  DECIMAL(10,2) DEFAULT 0.00,
    created_at    DATETIME DEFAULT NOW(),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- ============================================================
-- TABLE 4: sub_areas
-- Manager breaks his big area into smaller sub areas
-- Each sub area is assigned to a coordinator1
-- area_id links back to the main areas table
-- ============================================================
CREATE TABLE IF NOT EXISTS sub_areas (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    area_id          INT,
    sub_area_name    VARCHAR(100),
    coordinator1_id  INT,
    manager_id       INT,
    assigned_date    DATE,
    created_at       DATETIME DEFAULT NOW(),
    FOREIGN KEY (area_id)         REFERENCES areas(id),
    FOREIGN KEY (coordinator1_id) REFERENCES users(id),
    FOREIGN KEY (manager_id)      REFERENCES users(id)
);

-- ============================================================
-- TABLE 5: attendance
-- Coordinator1 checks in every morning with GPS coordinates
-- Manager verifies coordinates match the assigned sub area
-- is_present starts as FALSE, manager sets TRUE after verification
-- DECIMAL(9,6) for GPS gives accuracy up to 6 decimal places
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    coordinator_id  INT,
    sub_area_id     INT,
    check_in_time   DATETIME DEFAULT NOW(),
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    is_present      BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (coordinator_id) REFERENCES users(id),
    FOREIGN KEY (sub_area_id)    REFERENCES sub_areas(id)
);

-- ============================================================
-- TABLE 6: beneficiaries
-- Coordinator1 collects each family's details in the field
-- is_approved starts FALSE
-- Manager filters using per capita = annual_income / family_members
-- Manager sets is_approved = TRUE for qualifying families
-- Coordinator2 sees only approved families for delivery
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
    FOREIGN KEY (sub_area_id)  REFERENCES sub_areas(id),
    FOREIGN KEY (collector_id) REFERENCES users(id)
);

-- ============================================================
-- TABLE 7: eligible_families
-- Manager approves beneficiaries and inserts them here with per-capita income
-- This keeps the original beneficiaries table clean (raw field data only)
-- Coordinator2 queries this table to see who needs livestock delivery
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
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id),
    FOREIGN KEY (approved_by)    REFERENCES users(id)
);

-- ============================================================
-- TABLE 8: coordinator_live_tracking
-- Coordinator1's phone sends GPS every few minutes while in the field
-- Manager queries latest row per coordinator to see live location
-- ============================================================
CREATE TABLE IF NOT EXISTS coordinator_live_tracking (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    coordinator_id  INT NOT NULL,
    sub_area_id     INT,
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    recorded_at     DATETIME DEFAULT NOW(),
    FOREIGN KEY (coordinator_id) REFERENCES users(id),
    FOREIGN KEY (sub_area_id)    REFERENCES sub_areas(id)
);

-- ============================================================
-- TABLE 9: coordinator2_assignments
-- Manager assigns approved families to coordinator2 for delivery
-- status tracks progress: pending → delivered → completed
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
    FOREIGN KEY (manager_id)       REFERENCES users(id),
    FOREIGN KEY (coordinator2_id)  REFERENCES users(id),
    FOREIGN KEY (beneficiary_id)   REFERENCES beneficiaries(id),
    FOREIGN KEY (sub_area_id)      REFERENCES sub_areas(id)
);

-- ============================================================
-- TABLE 10: livestock_delivery
-- Coordinator2 delivers livestock and trains approved families
-- delivered and upskill_done tracked separately
-- because delivery and training happen on different days
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
    FOREIGN KEY (beneficiary_id)  REFERENCES beneficiaries(id),
    FOREIGN KEY (coordinator2_id) REFERENCES users(id)
);


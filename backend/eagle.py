# eagle.py
# This file handles ALL database operations for the EAGL system.
# It connects to MySQL and provides simple functions to read/write data.
# main.py calls these functions - it never writes SQL directly.

import mysql.connector  # library to connect Python with MySQL database

class EaglDB:

    # ------------------------------------------------------------
    # CONNECT TO DATABASE
    # This runs once when the app starts.
    # Change host, user, password, database to match your MySQL setup.
    # ------------------------------------------------------------
    def __init__(self):
        self.connection = mysql.connector.connect(
            host     = 'localhost',   # MySQL is running on this machine
            port     = 3306,          # default MySQL port
            user     = 'eagle_user',        # MySQL username
            password = '1234',        # MySQL password
            database = 'eagle_db'      # the database we created in schema.sql
        )
        # dictionary=True means rows come back as {column: value} instead of plain tuples
        self.cursor = self.connection.cursor(dictionary=True)

    # ------------------------------------------------------------
    # THREE HELPER FUNCTIONS used by everything below
    # ------------------------------------------------------------

    # Use this to INSERT / UPDATE / DELETE  (changes data)
    def run_query(self, sql, values=()):
        self.cursor.execute(sql, values)   # run the SQL
        self.connection.commit()           # save the change to disk
        return self.cursor.lastrowid       # return the auto-generated id of the new row

    # Use this to SELECT one row
    def get_one(self, sql, values=()):
        self.cursor.execute(sql, values)
        return self.cursor.fetchone()      # returns one row, or None if not found

    # Use this to SELECT many rows
    def get_many(self, sql, values=()):
        self.cursor.execute(sql, values)
        return self.cursor.fetchall()      # returns a list of rows

    # ============================================================
    # USERS
    # ============================================================

    def get_all_users(self):
        return self.get_many("SELECT * FROM users")

    def get_user_by_email(self, email):
        return self.get_one("SELECT * FROM users WHERE email = %s", (email,))

    def get_user_by_id(self, user_id):
        return self.get_one("SELECT * FROM users WHERE id = %s", (user_id,))

    def get_coordinators_under_manager(self, manager_id):
        return self.get_many("SELECT * FROM users WHERE manager_id = %s", (manager_id,))

    def login(self, email, password):
        return self.get_one("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))

    def add_user(self, name, email, password, role, manager_id):
        sql = "INSERT INTO users (name, email, password, role, manager_id) VALUES (%s, %s, %s, %s, %s)"
        return self.run_query(sql, (name, email, password, role, manager_id))

    def update_user(self, user_id, name, email, password, role, manager_id):
        self.run_query("UPDATE users SET name = %s, email = %s, password = %s, role = %s, manager_id = %s WHERE id = %s", (name, email, password, role, manager_id, user_id))

    def delete_user(self, user_id):
        self.run_query("DELETE FROM users WHERE id = %s", (user_id,))


    # ============================================================
    # AREAS
    # ============================================================

    def get_all_areas(self):
        return self.get_many("SELECT * FROM areas")

    def get_area_by_id(self, area_id):
        return self.get_one("SELECT * FROM areas WHERE id = %s", (area_id,))

    def get_areas_by_manager(self, manager_id):
        return self.get_many("SELECT * FROM areas WHERE manager_id = %s", (manager_id,))

    def add_area(self, area_name, district, poverty_percent, manager_id):
        sql = "INSERT INTO areas (area_name, district, poverty_percent, manager_id) VALUES (%s, %s, %s, %s)"
        return self.run_query(sql, (area_name, district, poverty_percent, manager_id))

    def update_area_manager(self, area_id, new_manager_id):
        self.run_query("UPDATE areas SET manager_id = %s WHERE id = %s", (new_manager_id, area_id))

    def delete_area(self, area_id):
        self.run_query("DELETE FROM areas WHERE id = %s", (area_id,))


    # ============================================================
    # FUNDS
    # ============================================================

    def get_all_funds(self):
        return self.get_many("SELECT * FROM funds")

    def get_fund_by_id(self, fund_id):
        return self.get_one("SELECT * FROM funds WHERE id = %s", (fund_id,))

    def get_fund_by_manager(self, manager_id):
        return self.get_one("SELECT * FROM funds WHERE manager_id = %s", (manager_id,))

    def add_fund(self, manager_id, total_amount):
        sql = "INSERT INTO funds (manager_id, total_amount) VALUES (%s, %s)"
        return self.run_query(sql, (manager_id, total_amount))

    def deduct_from_fund(self, manager_id, amount_spent):
        # Adds the spent amount to the running total of spent_amount
        self.run_query("UPDATE funds SET spent_amount = spent_amount + %s WHERE manager_id = %s", (amount_spent, manager_id))

    def delete_fund(self, fund_id):
        self.run_query("DELETE FROM funds WHERE id = %s", (fund_id,))


    # ============================================================
    # SUB AREAS
    # ============================================================

    def get_all_sub_areas(self):
        return self.get_many("SELECT * FROM sub_areas")

    def get_sub_area_by_id(self, subarea_id):
        return self.get_one("SELECT * FROM sub_areas WHERE id = %s", (subarea_id,))

    def get_sub_areas_by_area(self, area_id):
        return self.get_many("SELECT * FROM sub_areas WHERE area_id = %s", (area_id,))

    def get_sub_areas_by_coordinator(self, coordinator1_id):
        return self.get_many("SELECT * FROM sub_areas WHERE coordinator1_id = %s", (coordinator1_id,))

    def add_sub_area(self, area_id, sub_area_name, coordinator1_id, manager_id, assigned_date):
        sql = "INSERT INTO sub_areas (area_id, sub_area_name, coordinator1_id, manager_id, assigned_date) VALUES (%s, %s, %s, %s, %s)"
        return self.run_query(sql, (area_id, sub_area_name, coordinator1_id, manager_id, assigned_date))

    def reassign_sub_area(self, subarea_id, new_coordinator_id):
        self.run_query("UPDATE sub_areas SET coordinator1_id = %s WHERE id = %s", (new_coordinator_id, subarea_id))

    def delete_sub_area(self, subarea_id):
        self.run_query("DELETE FROM sub_areas WHERE id = %s", (subarea_id,))


    # ============================================================
    # ATTENDANCE
    # ============================================================

    def get_attendance_by_id(self, att_id):
        return self.get_one("SELECT * FROM attendance WHERE id = %s", (att_id,))

    def get_attendance_by_coordinator(self, coordinator_id):
        return self.get_many("SELECT * FROM attendance WHERE coordinator_id = %s", (coordinator_id,))

    def get_todays_attendance(self, coordinator_id):
        # CURDATE() returns today's date in MySQL
        sql = "SELECT * FROM attendance WHERE coordinator_id = %s AND DATE(check_in_time) = CURDATE()"
        return self.get_one(sql, (coordinator_id,))

    def add_attendance(self, coordinator_id, sub_area_id, latitude, longitude):
        sql = "INSERT INTO attendance (coordinator_id, sub_area_id, latitude, longitude) VALUES (%s, %s, %s, %s)"
        return self.run_query(sql, (coordinator_id, sub_area_id, latitude, longitude))

    def mark_present(self, att_id):
        # Manager calls this after verifying GPS location
        self.run_query("UPDATE attendance SET is_present = TRUE WHERE id = %s", (att_id,))

    def delete_attendance(self, att_id):
        self.run_query("DELETE FROM attendance WHERE id = %s", (att_id,))


    # ============================================================
    # BENEFICIARIES
    # ============================================================

    def get_beneficiary_by_id(self, ben_id):
        return self.get_one("SELECT * FROM beneficiaries WHERE id = %s", (ben_id,))

    def get_beneficiaries_by_collector(self, collector_id):
        return self.get_many("SELECT * FROM beneficiaries WHERE collector_id = %s", (collector_id,))

    def get_approved_beneficiaries(self):
        return self.get_many("SELECT * FROM beneficiaries WHERE is_approved = TRUE")

    def filter_beneficiaries_by_income(self, sub_area_id, per_capita_limit):
        # per capita = annual_income divided by number of family members
        # returns families below the income limit, poorest first
        sql = """
            SELECT * FROM beneficiaries
            WHERE sub_area_id = %s
            AND (annual_income / family_members) <= %s
            ORDER BY (annual_income / family_members) ASC
        """
        return self.get_many(sql, (sub_area_id, per_capita_limit))

    def add_beneficiary(self, family_name, sub_area_id, family_members, annual_income, collector_id):
        sql = "INSERT INTO beneficiaries (family_name, sub_area_id, family_members, annual_income, collector_id) VALUES (%s, %s, %s, %s, %s)"
        return self.run_query(sql, (family_name, sub_area_id, family_members, annual_income, collector_id))

    def approve_beneficiary(self, ben_id):
        # Manager sets is_approved = TRUE after reviewing the family's details
        self.run_query("UPDATE beneficiaries SET is_approved = TRUE WHERE id = %s", (ben_id,))

    def delete_beneficiary(self, ben_id):
        self.run_query("DELETE FROM beneficiaries WHERE id = %s", (ben_id,))


    # ============================================================
    # LIVESTOCK DELIVERY
    # ============================================================

    def get_delivery_by_id(self, del_id):
        return self.get_one("SELECT * FROM livestock_delivery WHERE id = %s", (del_id,))

    def get_deliveries_by_coordinator(self, coordinator2_id):
        return self.get_many("SELECT * FROM livestock_delivery WHERE coordinator2_id = %s", (coordinator2_id,))

    def get_all_deliveries(self):
        return self.get_many("SELECT * FROM livestock_delivery")

    def add_delivery(self, beneficiary_id, coordinator2_id, livestock_type):
        sql = "INSERT INTO livestock_delivery (beneficiary_id, coordinator2_id, livestock_type) VALUES (%s, %s, %s)"
        return self.run_query(sql, (beneficiary_id, coordinator2_id, livestock_type))

    def mark_delivered(self, del_id, notes):
        # Coordinator2 updates this after physically delivering the livestock
        self.run_query("UPDATE livestock_delivery SET delivered = TRUE, notes = %s WHERE id = %s", (notes, del_id))

    def mark_upskill_done(self, del_id, notes):
        # Coordinator2 updates this after completing the training session
        self.run_query("UPDATE livestock_delivery SET upskill_done = TRUE, notes = %s WHERE id = %s", (notes, del_id))

    def delete_delivery(self, del_id):
        self.run_query("DELETE FROM livestock_delivery WHERE id = %s", (del_id,))


    # ============================================================
    # ELIGIBLE FAMILIES
    # ============================================================

    def get_eligible_family_by_id(self, ef_id):
        return self.get_one("SELECT * FROM eligible_families WHERE id = %s", (ef_id,))

    def get_all_eligible_families(self):
        return self.get_many("SELECT * FROM eligible_families")

    def get_eligible_by_status(self, status):
        return self.get_many("SELECT * FROM eligible_families WHERE delivery_status = %s", (status,))

    def add_eligible_family(self, beneficiary_id, per_capita_income, approval_threshold, approved_by):
        sql = """INSERT INTO eligible_families
                 (beneficiary_id, per_capita_income, approval_threshold, approved_by)
                 VALUES (%s, %s, %s, %s)"""
        return self.run_query(sql, (beneficiary_id, per_capita_income, approval_threshold, approved_by))

    def update_delivery_status(self, ef_id, status):
        self.run_query("UPDATE eligible_families SET delivery_status = %s WHERE id = %s", (status, ef_id))

    def delete_eligible_family(self, ef_id):
        self.run_query("DELETE FROM eligible_families WHERE id = %s", (ef_id,))


    # ============================================================
    # COORDINATOR LIVE TRACKING
    # ============================================================

    def add_location(self, coordinator_id, sub_area_id, latitude, longitude):
        sql = "INSERT INTO coordinator_live_tracking (coordinator_id, sub_area_id, latitude, longitude) VALUES (%s, %s, %s, %s)"
        return self.run_query(sql, (coordinator_id, sub_area_id, latitude, longitude))

    def get_latest_location(self, coordinator_id):
        # Returns the most recent GPS ping for a coordinator
        sql = """SELECT * FROM coordinator_live_tracking
                 WHERE coordinator_id = %s
                 ORDER BY recorded_at DESC LIMIT 1"""
        return self.get_one(sql, (coordinator_id,))

    def get_all_latest_locations(self):
        # Returns the latest location for every coordinator (manager dashboard)
        sql = """SELECT t1.* FROM coordinator_live_tracking t1
                 INNER JOIN (
                     SELECT coordinator_id, MAX(recorded_at) AS latest
                     FROM coordinator_live_tracking GROUP BY coordinator_id
                 ) t2 ON t1.coordinator_id = t2.coordinator_id AND t1.recorded_at = t2.latest"""
        return self.get_many(sql)


    # ============================================================
    # COORDINATOR2 ASSIGNMENTS
    # ============================================================

    def get_assignment_by_id(self, assign_id):
        return self.get_one("SELECT * FROM coordinator2_assignments WHERE id = %s", (assign_id,))

    def get_assignments_by_coordinator2(self, coordinator2_id):
        return self.get_many("SELECT * FROM coordinator2_assignments WHERE coordinator2_id = %s", (coordinator2_id,))

    def get_assignments_by_manager(self, manager_id):
        return self.get_many("SELECT * FROM coordinator2_assignments WHERE manager_id = %s", (manager_id,))

    def add_assignment(self, manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date):
        sql = """INSERT INTO coordinator2_assignments
                 (manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date)
                 VALUES (%s, %s, %s, %s, %s)"""
        return self.run_query(sql, (manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date))

    def update_assignment_status(self, assign_id, status):
        self.run_query("UPDATE coordinator2_assignments SET status = %s WHERE id = %s", (status, assign_id))

    def delete_assignment(self, assign_id):
        self.run_query("DELETE FROM coordinator2_assignments WHERE id = %s", (assign_id,))

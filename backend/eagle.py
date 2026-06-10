import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import bcrypt

load_dotenv()

class EaglDB:

    def __init__(self):
        # Create a connection pool to handle concurrent requests
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="eagle_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "eagle_user"),
            password=os.getenv("DB_PASS", "1234"),
            database=os.getenv("DB_NAME", "eagle_db")
        )

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError:
            return False

    def get_connection(self):
        return self.pool.get_connection()

    def run_query(self, sql, values=()):
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_one(self, sql, values=()):
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, values)
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_many(self, sql, values=()):
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, values)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    # ============================================================
    # USERS
    # ============================================================

    def get_all_users(self):
        return self.get_many("SELECT id, name, email, role, mobile, manager_id, is_first_login, created_at FROM users")

    def get_user_by_email(self, email):
        return self.get_one("SELECT * FROM users WHERE email = %s", (email,))

    def get_user_by_id(self, user_id):
        # Don't return password hash in regular user fetches if not necessary, but login needs it.
        # Actually, let's return all columns, backend.py will strip it if needed.
        return self.get_one("SELECT * FROM users WHERE id = %s", (user_id,))

    def get_coordinators_under_manager(self, manager_id):
        return self.get_many("SELECT id, name, email, role, mobile, manager_id, is_first_login, created_at FROM users WHERE manager_id = %s", (manager_id,))

    def login(self, email, password):
        user = self.get_one("SELECT * FROM users WHERE email = %s", (email,))
        if user and self.verify_password(password, user['password']):
            # Remove password from returned dictionary for safety
            user.pop('password', None)
            return user
        # Fallback for plain text passwords before migration (optional, but good for transition)
        elif user and user['password'] == password:
            # Upgrade password hash transparently if plain text matched
            hashed = self.hash_password(password)
            self.run_query("UPDATE users SET password = %s WHERE id = %s", (hashed, user['id']))
            user.pop('password', None)
            return user
        return None

    def add_user(self, name, email, password, role, mobile, manager_id):
        hashed_pw = self.hash_password(password)
        sql = "INSERT INTO users (name, email, password, role, mobile, manager_id) VALUES (%s, %s, %s, %s, %s, %s)"
        return self.run_query(sql, (name, email, hashed_pw, role, mobile, manager_id))

    def update_user(self, user_id, name, email, password, role, mobile, manager_id):
        # If password is changed, hash it. If it's passed as is (already hashed), we'd need to handle that.
        # It's better if password updates are handled separately, but we'll adapt.
        current_user = self.get_user_by_id(user_id)
        if password and password != current_user['password']:
            password = self.hash_password(password)
            
        self.run_query("UPDATE users SET name = %s, email = %s, password = %s, role = %s, mobile = %s, manager_id = %s WHERE id = %s", 
                       (name, email, password, role, mobile, manager_id, user_id))

    def delete_user(self, user_id):
        self.run_query("DELETE FROM users WHERE id = %s", (user_id,))

    def change_password(self, user_id, new_password):
        hashed_pw = self.hash_password(new_password)
        self.run_query("UPDATE users SET password = %s, is_first_login = 0 WHERE id = %s", (hashed_pw, user_id))

    def update_user_profile(self, user_id, name, mobile):
        self.run_query("UPDATE users SET name = %s, mobile = %s WHERE id = %s", (name, mobile, user_id))

    def reset_first_login(self, user_id):
        self.run_query("UPDATE users SET is_first_login = 0 WHERE id = %s", (user_id,))

    # ============================================================
    # AREAS
    # ============================================================

    def get_all_areas(self):
        return self.get_many("SELECT * FROM areas")

    def get_area_by_id(self, area_id):
        return self.get_one("SELECT * FROM areas WHERE id = %s", (area_id,))

    def get_areas_by_manager(self, manager_id):
        return self.get_many("SELECT * FROM areas WHERE manager_id = %s", (manager_id,))

    def get_area_by_name(self, area_name):
        return self.get_one("SELECT * FROM areas WHERE area_name = %s", (area_name,))

    def add_area(self, area_name, district, poverty_percent, manager_id):
        sql = "INSERT INTO areas (area_name, district, poverty_percent, manager_id) VALUES (%s, %s, %s, %s)"
        return self.run_query(sql, (area_name, district, poverty_percent, manager_id))

    def update_area_manager(self, area_id, new_manager_id):
        self.run_query("UPDATE areas SET manager_id = %s WHERE id = %s", (new_manager_id, area_id))

    def update_area(self, area_id, area_name, district, poverty_percent, manager_id):
        sql = "UPDATE areas SET area_name=%s, district=%s, poverty_percent=%s, manager_id=%s WHERE id=%s"
        self.run_query(sql, (area_name, district, poverty_percent, manager_id, area_id))

    def delete_area(self, area_id):
        self.run_query("DELETE FROM areas WHERE id = %s", (area_id,))


    # ============================================================
    # FUNDS
    # ============================================================

    def get_all_funds(self):
        sql = """
            SELECT f.*,
                   u.name  AS manager_name,
                   a.area_name, a.district,
                   ROUND(f.total_amount - f.spent_amount, 2) AS remaining
            FROM funds f
            LEFT JOIN users u ON f.manager_id = u.id
            LEFT JOIN areas a ON f.area_id     = a.id
            ORDER BY f.created_at DESC
        """
        return self.get_many(sql)

    def get_fund_by_id(self, fund_id):
        sql = """
            SELECT f.*,
                   u.name AS manager_name,
                   a.area_name, a.district
            FROM funds f
            LEFT JOIN users u ON f.manager_id = u.id
            LEFT JOIN areas a ON f.area_id     = a.id
            WHERE f.id = %s
        """
        return self.get_one(sql, (fund_id,))

    def get_fund_by_manager(self, manager_id):
        sql = """
            SELECT f.*,
                   u.name AS manager_name,
                   a.area_name, a.district,
                   ROUND(f.total_amount - f.spent_amount, 2) AS remaining
            FROM funds f
            LEFT JOIN users u ON f.manager_id = u.id
            LEFT JOIN areas a ON f.area_id     = a.id
            WHERE f.manager_id = %s
        """
        return self.get_one(sql, (manager_id,))

    def add_fund(self, manager_id, area_id, total_amount):
        """Create new fund — one per manager (enforced by UNIQUE constraint)."""
        sql = "INSERT INTO funds (manager_id, area_id, total_amount) VALUES (%s, %s, %s)"
        return self.run_query(sql, (manager_id, area_id, total_amount))

    def topup_fund(self, manager_id, area_id, amount):
        """Top-up an existing manager fund and optionally update area_id."""
        sql = """
            UPDATE funds
            SET total_amount = total_amount + %s,
                area_id = COALESCE(%s, area_id)
            WHERE manager_id = %s
        """
        self.run_query(sql, (amount, area_id, manager_id))
        return self.get_fund_by_manager(manager_id)

    def deduct_from_fund(self, manager_id, amount_spent):
        # Transactional deduction to prevent overdraft
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            conn.start_transaction()
            
            cursor.execute("SELECT total_amount, spent_amount FROM funds WHERE manager_id = %s FOR UPDATE", (manager_id,))
            fund = cursor.fetchone()
            
            if not fund:
                raise ValueError("Fund not found for manager")
                
            if fund['total_amount'] - fund['spent_amount'] < amount_spent:
                raise ValueError("Insufficient funds. Cannot overdraft.")
                
            cursor.execute("UPDATE funds SET spent_amount = spent_amount + %s WHERE manager_id = %s", (amount_spent, manager_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def delete_fund(self, fund_id):
        self.run_query("DELETE FROM funds WHERE id = %s", (fund_id,))

    # ============================================================
    # FUND ALLOCATIONS
    # ============================================================

    def get_fund_allocation_by_id(self, alloc_id):
        return self.get_one("SELECT * FROM fund_allocations WHERE id = %s", (alloc_id,))

    def get_fund_allocations_by_manager(self, manager_id):
        sql = """
            SELECT fa.*,
                   b.family_name AS ben_family_name,
                   b.family_members AS ben_family_members,
                   u.name AS allocated_by_name
            FROM fund_allocations fa
            JOIN beneficiaries b ON fa.beneficiary_id = b.id
            JOIN users u         ON fa.allocated_by   = u.id
            WHERE fa.manager_id = %s
            ORDER BY fa.allocated_at DESC
        """
        return self.get_many(sql, (manager_id,))

    def add_fund_allocation(self, fund_id, manager_id, beneficiary_id, family_name,
                            family_members, per_capita_income, amount_assigned, allocated_by):
        sql = """INSERT INTO fund_allocations
                 (fund_id, manager_id, beneficiary_id, family_name, family_members,
                  per_capita_income, amount_assigned, allocated_by)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        return self.run_query(sql, (fund_id, manager_id, beneficiary_id, family_name,
                                    family_members, per_capita_income, amount_assigned, allocated_by))


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

    def get_sub_areas_by_manager(self, manager_id):
        return self.get_many("SELECT * FROM sub_areas WHERE manager_id = %s", (manager_id,))

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

    def get_attendance_by_manager(self, manager_id):
        sql = """
            SELECT a.* FROM attendance a
            JOIN sub_areas sa ON a.sub_area_id = sa.id
            WHERE sa.manager_id = %s
        """
        return self.get_many(sql, (manager_id,))

    def get_todays_attendance(self, coordinator_id):
        sql = "SELECT * FROM attendance WHERE coordinator_id = %s AND DATE(check_in_time) = CURDATE()"
        return self.get_one(sql, (coordinator_id,))

    def add_attendance(self, coordinator_id, sub_area_id):
        sql = "INSERT INTO attendance (coordinator_id, sub_area_id) VALUES (%s, %s)"
        return self.run_query(sql, (coordinator_id, sub_area_id))

    def mark_present(self, att_id):
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

    def get_beneficiaries_by_manager(self, manager_id):
        sql = """
            SELECT b.* FROM beneficiaries b
            JOIN sub_areas sa ON b.sub_area_id = sa.id
            WHERE sa.manager_id = %s
        """
        return self.get_many(sql, (manager_id,))

    def filter_beneficiaries_by_income(self, sub_area_id, per_capita_limit):
        sql = """
            SELECT * FROM beneficiaries
            WHERE sub_area_id = %s
            AND (annual_income / NULLIF(family_members, 0)) <= %s
            ORDER BY (annual_income / NULLIF(family_members, 0)) ASC
        """
        return self.get_many(sql, (sub_area_id, per_capita_limit))

    def get_beneficiaries_by_manager_filtered(self, manager_id, area_id=None, sub_area_id=None, per_capita_max=None, is_approved=None):
        conditions = ["sa.manager_id = %s"]
        params = [manager_id]

        if area_id:
            conditions.append("sa.area_id = %s")
            params.append(area_id)

        if sub_area_id:
            conditions.append("b.sub_area_id = %s")
            params.append(sub_area_id)

        if per_capita_max is not None:
            conditions.append("(b.annual_income / NULLIF(b.family_members, 0)) <= %s")
            params.append(per_capita_max)

        if is_approved is True:
            conditions.append("b.is_approved = TRUE")
        elif is_approved is False:
            conditions.append("b.is_approved = FALSE")

        where = " AND ".join(conditions)
        sql = f"""
            SELECT b.*,
                   sa.sub_area_name,
                   sa.area_id,
                   a.area_name,
                   ROUND(b.annual_income / NULLIF(b.family_members, 0), 2) AS per_capita_income
            FROM beneficiaries b
            JOIN sub_areas sa ON b.sub_area_id = sa.id
            JOIN areas a ON sa.area_id = a.id
            WHERE {where}
            ORDER BY (b.annual_income / NULLIF(b.family_members, 0)) ASC
        """
        return self.get_many(sql, tuple(params))

    def add_beneficiary(self, family_name, sub_area_id, family_members, annual_income, collector_id):
        sql = "INSERT INTO beneficiaries (family_name, sub_area_id, family_members, annual_income, collector_id) VALUES (%s, %s, %s, %s, %s)"
        return self.run_query(sql, (family_name, sub_area_id, family_members, annual_income, collector_id))

    def approve_beneficiary(self, ben_id):
        self.run_query("UPDATE beneficiaries SET is_approved = TRUE WHERE id = %s", (ben_id,))

    def delete_beneficiary(self, ben_id):
        self.run_query("DELETE FROM beneficiaries WHERE id = %s", (ben_id,))


    # ============================================================
    # LIVESTOCK DELIVERY
    # ============================================================

    def get_delivery_by_id(self, del_id):
        sql = """
            SELECT ld.*, b.family_name, b.family_members
            FROM livestock_delivery ld
            LEFT JOIN beneficiaries b ON ld.beneficiary_id = b.id
            WHERE ld.id = %s
        """
        return self.get_one(sql, (del_id,))

    def get_deliveries_by_coordinator(self, coordinator2_id):
        sql = """
            SELECT ld.*, b.family_name, b.family_members,
                   sa.sub_area_name, a.area_name
            FROM livestock_delivery ld
            LEFT JOIN beneficiaries b ON ld.beneficiary_id = b.id
            LEFT JOIN sub_areas sa    ON b.sub_area_id = sa.id
            LEFT JOIN areas a         ON sa.area_id = a.id
            WHERE ld.coordinator2_id = %s
            ORDER BY ld.id DESC
        """
        return self.get_many(sql, (coordinator2_id,))

    def get_all_deliveries(self):
        sql = """
            SELECT ld.*, b.family_name, b.family_members
            FROM livestock_delivery ld
            LEFT JOIN beneficiaries b ON ld.beneficiary_id = b.id
            ORDER BY ld.id DESC
        """
        return self.get_many(sql)

    def add_delivery(self, beneficiary_id, coordinator2_id, livestock_type, notes=None):
        sql = """INSERT INTO livestock_delivery
                 (beneficiary_id, coordinator2_id, livestock_type, notes)
                 VALUES (%s, %s, %s, %s)"""
        return self.run_query(sql, (beneficiary_id, coordinator2_id, livestock_type, notes))

    def mark_delivered(self, del_id, notes):
        self.run_query("UPDATE livestock_delivery SET delivered = TRUE, notes = %s, updated_at = NOW() WHERE id = %s", (notes, del_id))

    def mark_upskill_done(self, del_id, notes):
        self.run_query("UPDATE livestock_delivery SET upskill_done = TRUE, notes = %s, updated_at = NOW() WHERE id = %s", (notes, del_id))

    def delete_delivery(self, del_id):
        self.run_query("DELETE FROM livestock_delivery WHERE id = %s", (del_id,))


    # ============================================================
    # ELIGIBLE FAMILIES
    # ============================================================

    def get_eligible_family_by_id(self, ef_id):
        return self.get_one("SELECT * FROM eligible_families WHERE id = %s", (ef_id,))

    def get_all_eligible_families(self):
        return self.get_many("SELECT * FROM eligible_families")

    def get_eligible_by_manager(self, manager_id):
        sql = """
            SELECT ef.*,
                   b.family_name, b.family_members, b.annual_income,
                   sa.sub_area_name, a.area_name,
                   u.name AS approved_by_name
            FROM eligible_families ef
            JOIN beneficiaries b  ON ef.beneficiary_id = b.id
            JOIN sub_areas sa     ON b.sub_area_id = sa.id
            JOIN areas a          ON sa.area_id = a.id
            LEFT JOIN users u     ON ef.approved_by = u.id
            WHERE ef.approved_by = %s
            ORDER BY ef.approved_at DESC
        """
        return self.get_many(sql, (manager_id,))

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
    # DELIVERY COORDINATOR ASSIGNMENTS
    # ============================================================

    def get_assignment_by_id(self, assign_id):
        sql = """
            SELECT ca.*,
                   b.family_name, b.family_members,
                   sa.sub_area_name,
                   u.name AS coordinator_name
            FROM coordinator2_assignments ca
            LEFT JOIN beneficiaries b ON ca.beneficiary_id = b.id
            LEFT JOIN sub_areas sa    ON ca.sub_area_id    = sa.id
            LEFT JOIN users u         ON ca.coordinator2_id = u.id
            WHERE ca.id = %s
        """
        return self.get_one(sql, (assign_id,))

    def get_assignments_by_coordinator2(self, coordinator2_id):
        sql = """
            SELECT ca.*,
                   b.family_name, b.family_members,
                   sa.sub_area_name
            FROM coordinator2_assignments ca
            LEFT JOIN beneficiaries b ON ca.beneficiary_id = b.id
            LEFT JOIN sub_areas sa    ON ca.sub_area_id    = sa.id
            WHERE ca.coordinator2_id = %s
            ORDER BY ca.id DESC
        """
        return self.get_many(sql, (coordinator2_id,))

    def get_assignments_by_manager(self, manager_id):
        sql = """
            SELECT ca.*,
                   b.family_name, b.family_members,
                   sa.sub_area_name,
                   u.name AS coordinator_name
            FROM coordinator2_assignments ca
            LEFT JOIN beneficiaries b ON ca.beneficiary_id = b.id
            LEFT JOIN sub_areas sa    ON ca.sub_area_id    = sa.id
            LEFT JOIN users u         ON ca.coordinator2_id = u.id
            WHERE ca.manager_id = %s
            ORDER BY ca.id DESC
        """
        return self.get_many(sql, (manager_id,))

    def add_assignment(self, manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date):
        sql = """INSERT INTO coordinator2_assignments
                 (manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date)
                 VALUES (%s, %s, %s, %s, %s)"""
        return self.run_query(sql, (manager_id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date))

    def update_assignment(self, id, coordinator2_id, beneficiary_id, sub_area_id, assigned_date):
        sql = """UPDATE coordinator2_assignments 
                 SET coordinator2_id=%s, beneficiary_id=%s, sub_area_id=%s, assigned_date=%s
                 WHERE id=%s"""
        self.run_query(sql, (coordinator2_id, beneficiary_id, sub_area_id, assigned_date, id))

    def update_assignment_status(self, assign_id, status):
        self.run_query("UPDATE coordinator2_assignments SET status = %s WHERE id = %s", (status, assign_id))

    def delete_assignment(self, assign_id):
        self.run_query("DELETE FROM coordinator2_assignments WHERE id = %s", (assign_id,))


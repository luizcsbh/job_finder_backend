import sqlite3
from abc import ABC, abstractmethod

from supabase import create_client

from src.config import (
    SQLITE_DB_PATH,
    STORAGE_PROVIDER,
    SUPABASE_FAVORITES_TABLE,
    SUPABASE_KEY,
    SUPABASE_URL,
    SUPABASE_USERS_TABLE,
)


class StorageRepository(ABC):
    @abstractmethod
    def get_user_by_id(self, user_id):
        pass

    @abstractmethod
    def get_user_by_email(self, email):
        pass

    @abstractmethod
    def create_user(self, email, password, name=None):
        pass

    @abstractmethod
    def update_user_password(self, email, new_password):
        pass

    @abstractmethod
    def update_user_profile(self, user_id, name, birth_date):
        pass

    @abstractmethod
    def update_user_resume_path(self, user_id, resume_path):
        pass

    @abstractmethod
    def get_favorite_urls(self, user_id):
        pass

    @abstractmethod
    def toggle_favorite(self, user_id, job_url):
        pass

    @abstractmethod
    def list_users(self):
        pass

    @abstractmethod
    def delete_user(self, user_id):
        pass

    @abstractmethod
    def update_user_admin_status(self, user_id, is_admin):
        pass


class SQLiteStorage(StorageRepository):
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._ensure_schema()

    def _ensure_schema(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            resume_path TEXT,
            name TEXT,
            birth_date TEXT,
            is_admin INTEGER DEFAULT 0
        )
        """)
        
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_url TEXT
        )
        """)

        self.conn.commit()

    def get_user_by_id(self, user_id):
        self.cursor.execute("SELECT id, email, password, resume_path, name, birth_date, is_admin FROM users WHERE id=?", (user_id,))
        row = self.cursor.fetchone()
        return _map_sqlite_user(row)

    def get_user_by_email(self, email):
        self.cursor.execute("SELECT id, email, password, resume_path, name, birth_date, is_admin FROM users WHERE email=?", (email,))
        row = self.cursor.fetchone()
        return _map_sqlite_user(row)

    def create_user(self, email, password, name=None):
        self.cursor.execute(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
            (email, password, name)
        )
        self.conn.commit()

    def update_user_password(self, email, new_password):
        self.cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        self.conn.commit()

    def update_user_profile(self, user_id, name, birth_date):
        self.cursor.execute("UPDATE users SET name=?, birth_date=? WHERE id=?", (name, birth_date, user_id))
        self.conn.commit()

    def update_user_admin_status(self, user_id, is_admin):
        self.cursor.execute("UPDATE users SET is_admin=? WHERE id=?", (1 if is_admin else 0, user_id))
        self.conn.commit()

    def update_user_resume_path(self, user_id, resume_path):
        self.cursor.execute("UPDATE users SET resume_path=? WHERE id=?", (resume_path, user_id))
        self.conn.commit()

    def get_favorite_urls(self, user_id):
        self.cursor.execute("SELECT job_url FROM favorites WHERE user_id=?", (user_id,))
        return [row[0] for row in self.cursor.fetchall()]

    def toggle_favorite(self, user_id, job_url):
        self.cursor.execute(
            "SELECT id FROM favorites WHERE user_id=? AND job_url=?",
            (user_id, job_url)
        )
        result = self.cursor.fetchone()

        if result:
            self.cursor.execute("DELETE FROM favorites WHERE id=?", (result[0],))
            self.conn.commit()
            return False

        self.cursor.execute(
            "INSERT INTO favorites (user_id, job_url) VALUES (?, ?)",
            (user_id, job_url)
        )
        self.conn.commit()
        return True

    def list_users(self):
        self.cursor.execute("SELECT id, email, name, is_admin FROM users")
        rows = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "is_admin": bool(row[3]),
                "created_at": None # SQLite doesn't have it by default in this schema
            }
            for row in rows
        ]

    def update_user_admin_status(self, user_id, is_admin):
        self.cursor.execute("UPDATE users SET is_admin=? WHERE id=?", (1 if is_admin else 0, user_id))
        self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM favorites WHERE user_id=?", (user_id,))
        self.cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        self.conn.commit()


class SupabaseStorage(StorageRepository):
    def __init__(self, url, key):
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY sao obrigatorios quando STORAGE_PROVIDER=supabase")

        self.client = create_client(url, key)

    def get_user_by_id(self, user_id):
        response = (
            self.client.table(SUPABASE_USERS_TABLE)
            .select("id, email, password, resume_path, name, birth_date, is_admin")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return _first_or_none(response.data)

    def get_user_by_email(self, email):
        response = (
            self.client.table(SUPABASE_USERS_TABLE)
            .select("id, email, password, resume_path, name, birth_date, is_admin")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        return _first_or_none(response.data)

    def create_user(self, email, password, name=None):
        try:
            # Try to sign up the user in Supabase Auth first
            # sign_up in v2.x expects email and password as keyword arguments
            self.client.auth.sign_up(email=email, password=password)
        except Exception as e:
            print(f"DEBUG: Supabase Auth sign_up skipped or failed: {e}")
            pass 

        # Always ensure user is in our custom tracking table
        self.client.table(SUPABASE_USERS_TABLE).insert({
            "email": email,
            "password": password,
            "name": name
        }).execute()

    def update_user_password(self, email, new_password):
        (
            self.client.table(SUPABASE_USERS_TABLE)
            .update({"password": new_password})
            .eq("email", email)
            .execute()
        )

    def update_user_profile(self, user_id, name, birth_date):
        (
            self.client.table(SUPABASE_USERS_TABLE)
            .update({"name": name, "birth_date": birth_date})
            .eq("id", user_id)
            .execute()
        )

    def update_user_resume_path(self, user_id, resume_path):
        (
            self.client.table(SUPABASE_USERS_TABLE)
            .update({"resume_path": resume_path})
            .eq("id", user_id)
            .execute()
        )

    def send_password_reset_email(self, email, redirect_url=None):
        try:
            # Clean up redirect_url
            if redirect_url and redirect_url.endswith("/"):
                redirect_url = redirect_url[:-1]

            # Best-effort to ensure user exists in Supabase native Auth table.
            # Using admin.create_user requires the service_role key.
            try:
                self.client.auth.admin.create_user({
                    "email": email, 
                    "password": "tempPassword!123", 
                    "email_confirm": True
                })
            except Exception:
                pass
                
            options = {}
            if redirect_url:
                options["redirect_to"] = redirect_url
                
            # reset_password_for_email in v2.x
            self.client.auth.reset_password_for_email(email, options)
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg:
                raise Exception("Limite de e-mails do Supabase excedido. Tente novamente mais tarde.")
            raise Exception(f"Erro ao solicitar recuperação: {str(e)}")

    def update_password_with_token(self, token, hashed_password, raw_password):
        try:
            # In Supabase v2, we can set the session with the token to perform authorized updates
            # or use the admin API to update via the token/user_id.
            # Since the recovery link gives us an access_token, we can use it to get the user.
            user_response = self.client.auth.get_user(token)
            if not user_response or not user_response.user:
                return False
                
            email = user_response.user.email
            user_id = user_response.user.id

            # 1. Update our application's tracking table
            self.update_user_password(email, hashed_password)
            
            # 2. Update Supabase native Auth password
            # If we have service_role, we update by ID
            self.client.auth.admin.update_user_by_id(
                user_id, 
                {"password": raw_password}
            )
            return True
        except Exception as e:
            print(f"DEBUG: Error updating password with token: {e}")
            return False

    def get_favorite_urls(self, user_id):
        response = (
            self.client.table(SUPABASE_FAVORITES_TABLE)
            .select("job_url")
            .eq("user_id", user_id)
            .execute()
        )
        return [row["job_url"] for row in response.data]

    def toggle_favorite(self, user_id, job_url):
        existing = (
            self.client.table(SUPABASE_FAVORITES_TABLE)
            .select("id")
            .eq("user_id", user_id)
            .eq("job_url", job_url)
            .limit(1)
            .execute()
        )

        current = _first_or_none(existing.data)
        if current:
            self.client.table(SUPABASE_FAVORITES_TABLE).delete().eq("id", current["id"]).execute()
            return False

        self.client.table(SUPABASE_FAVORITES_TABLE).insert({
            "user_id": user_id,
            "job_url": job_url
        }).execute()
        return True

    def list_users(self):
        from src.config import SUPABASE_USERS_TABLE
        res = self.client.table(SUPABASE_USERS_TABLE).select("id, email, name, created_at, is_admin").execute()
        return res.data

    def update_user_admin_status(self, user_id, is_admin):
        from src.config import SUPABASE_USERS_TABLE
        self.client.table(SUPABASE_USERS_TABLE).update({"is_admin": is_admin}).eq("id", user_id).execute()

    def delete_user(self, user_id):
        # Delete favorites first
        self.client.table(SUPABASE_FAVORITES_TABLE).delete().eq("user_id", user_id).execute()
        # Delete user record
        self.client.table(SUPABASE_USERS_TABLE).delete().eq("id", user_id).execute()



def get_storage():
    if STORAGE_PROVIDER == "supabase":
        return SupabaseStorage(SUPABASE_URL, SUPABASE_KEY)

    return SQLiteStorage(SQLITE_DB_PATH)



def _map_sqlite_user(row):
    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "password": row[2],
        "resume_path": row[3],
        "name": row[4],
        "birth_date": row[5],
        "is_admin": bool(row[6])
    }



def _first_or_none(rows):
    if not rows:
        return None

    return rows[0]

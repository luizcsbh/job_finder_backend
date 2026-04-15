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
    def create_user(self, email, password):
        pass

    @abstractmethod
    def update_user_password(self, email, new_password):
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
            resume_path TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_url TEXT
        )
        """)

        self.conn.commit()

    def get_user_by_id(self, user_id):
        self.cursor.execute("SELECT id, email, password, resume_path FROM users WHERE id=?", (user_id,))
        row = self.cursor.fetchone()
        return _map_sqlite_user(row)

    def get_user_by_email(self, email):
        self.cursor.execute("SELECT id, email, password, resume_path FROM users WHERE email=?", (email,))
        row = self.cursor.fetchone()
        return _map_sqlite_user(row)

    def create_user(self, email, password):
        self.cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, password)
        )
        self.conn.commit()

    def update_user_password(self, email, new_password):
        self.cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
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


class SupabaseStorage(StorageRepository):
    def __init__(self, url, key):
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY sao obrigatorios quando STORAGE_PROVIDER=supabase")

        self.client = create_client(url, key)

    def get_user_by_id(self, user_id):
        response = (
            self.client.table(SUPABASE_USERS_TABLE)
            .select("id, email, password, resume_path")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return _first_or_none(response.data)

    def get_user_by_email(self, email):
        response = (
            self.client.table(SUPABASE_USERS_TABLE)
            .select("id, email, password, resume_path")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        return _first_or_none(response.data)

    def create_user(self, email, password):
        self.client.table(SUPABASE_USERS_TABLE).insert({
            "email": email,
            "password": password
        }).execute()

    def update_user_password(self, email, new_password):
        (
            self.client.table(SUPABASE_USERS_TABLE)
            .update({"password": new_password})
            .eq("email", email)
            .execute()
        )

    def update_user_resume_path(self, user_id, resume_path):
        (
            self.client.table(SUPABASE_USERS_TABLE)
            .update({"resume_path": resume_path})
            .eq("id", user_id)
            .execute()
        )

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
        "resume_path": row[3]
    }



def _first_or_none(rows):
    if not rows:
        return None

    return rows[0]

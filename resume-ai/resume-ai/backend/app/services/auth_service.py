import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from app.config import settings


class AuthService:
    def __init__(self):
        self.secret_key = settings.AUTH_SECRET_KEY.encode("utf-8")
        self.token_expire_minutes = settings.AUTH_TOKEN_EXPIRE_MINUTES
        self.revoked_tokens = set()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "users.db")
        self._init_db()

    def _init_db(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                mobile_no TEXT,
                gender TEXT,
                profile_photo_url TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._ensure_column(cursor, "users", "mobile_no", "TEXT")
        self._ensure_column(cursor, "users", "gender", "TEXT")
        self._ensure_column(cursor, "users", "profile_photo_url", "TEXT")
        connection.commit()
        connection.close()

    def _ensure_column(self, cursor: sqlite3.Cursor, table: str, column: str, column_type: str):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    def _get_connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return f"{salt.hex()}${digest.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            salt_hex, digest_hex = password_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
            return hmac.compare_digest(actual, expected)
        except ValueError:
            return False

    def _sign_payload(self, payload_b64: str) -> str:
        digest = hmac.new(self.secret_key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    def create_access_token(self, email: str) -> str:
        expiration = datetime.now(timezone.utc) + timedelta(minutes=self.token_expire_minutes)
        payload = {"sub": email, "exp": int(expiration.timestamp())}
        payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
        signature = self._sign_payload(payload_b64)
        return f"{payload_b64}.{signature}"

    def decode_token(self, token: str):
        if token in self.revoked_tokens:
            return None

        try:
            payload_b64, signature = token.split(".", 1)
            expected_signature = self._sign_payload(payload_b64)
            if not hmac.compare_digest(signature, expected_signature):
                return None

            padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload_data = base64.urlsafe_b64decode(padded_payload.encode("utf-8"))
            payload = json.loads(payload_data)
            if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
                return None

            return payload
        except Exception:
            return None

    def create_user(self, full_name: str, email: str, password: str):
        normalized_email = email.strip().lower()
        password_hash = self._hash_password(password)
        created_at = datetime.now(timezone.utc).isoformat()

        connection = self._get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, mobile_no, gender, profile_photo_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (full_name.strip(), normalized_email, password_hash, None, None, None, created_at),
            )
            connection.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            connection.close()
            return None

        cursor.execute(
            "SELECT id, full_name, email, mobile_no, gender, profile_photo_url, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        connection.close()
        return dict(row) if row else None

    def authenticate_user(self, email: str, password: str):
        normalized_email = email.strip().lower()
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, full_name, email, password_hash, mobile_no, gender, profile_photo_url, created_at FROM users WHERE email = ?",
            (normalized_email,),
        )
        row = cursor.fetchone()
        connection.close()

        if not row:
            return None

        if not self._verify_password(password, row["password_hash"]):
            return None

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "mobile_no": row["mobile_no"],
            "gender": row["gender"],
            "profile_photo_url": row["profile_photo_url"],
            "created_at": row["created_at"],
        }

    def get_user_by_email(self, email: str):
        normalized_email = email.strip().lower()
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, full_name, email, mobile_no, gender, profile_photo_url, created_at FROM users WHERE email = ?",
            (normalized_email,),
        )
        row = cursor.fetchone()
        connection.close()
        return dict(row) if row else None

    def update_user_profile(self, user_id: int, full_name: str, email: str, mobile_no: str | None, gender: str | None):
        normalized_email = email.strip().lower()
        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (normalized_email, user_id))
        duplicate = cursor.fetchone()
        if duplicate:
            connection.close()
            return None, "Email already registered"

        cursor.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, mobile_no = ?, gender = ?
            WHERE id = ?
            """,
            (
                full_name.strip(),
                normalized_email,
                mobile_no.strip() if mobile_no else None,
                gender.strip() if gender else None,
                user_id,
            ),
        )
        connection.commit()

        cursor.execute(
            "SELECT id, full_name, email, mobile_no, gender, profile_photo_url, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        connection.close()
        return (dict(row) if row else None), None

    def update_profile_photo(self, user_id: int, file_bytes: bytes, content_type: str):
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        photo_url = f"data:{content_type};base64,{encoded}"

        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET profile_photo_url = ? WHERE id = ?",
            (photo_url, user_id),
        )
        connection.commit()
        cursor.execute(
            "SELECT id, full_name, email, mobile_no, gender, profile_photo_url, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        connection.close()
        return dict(row) if row else None

    def revoke_token(self, token: str):
        self.revoked_tokens.add(token)


auth_service = AuthService()
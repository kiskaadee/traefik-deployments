import os
import sqlite3
import secrets
import hashlib
import uuid
import jwt
import datetime
from typing import Optional, List
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from database import get_db

JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "access_token"

cookie_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)

class AuthService:
    @staticmethod
    def generate_salt() -> str:
        return secrets.token_hex(8)

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        combined = pass_hash + salt
        final_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        return f"$SHA${salt}${final_hash}"

    @staticmethod
    def verify_password(password: str, authme_hash: str) -> bool:
        try:
            parts = authme_hash.split("$")
            if len(parts) != 4 or parts[1] != "SHA":
                return False
            salt = parts[2]
            stored_hash = parts[3]
            
            pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            combined = pass_hash + salt
            computed_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    @staticmethod
    def create_jwt_token(username: str) -> str:
        payload = {
            "sub": username.lower(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_jwt_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("sub")
        except jwt.PyJWTError:
            return None

class PlayerService:
    @staticmethod
    def calculate_offline_uuid(username: str) -> str:
        # Minecraft Java offline player UUID computation: UUID.nameUUIDFromBytes(("OfflinePlayer:" + username).getBytes(UTF_8))
        data = f"OfflinePlayer:{username}"
        hash_digest = hashlib.md5(data.encode('utf-8')).digest()
        offline_uuid = uuid.UUID(bytes=hash_digest, version=3)
        return str(offline_uuid)

    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[dict]:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT rowid, id, username, realname, email, regdate, password FROM authme WHERE LOWER(username) = LOWER(?)", (username,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
            
        # Get role
        cursor.execute("SELECT role FROM user_roles WHERE LOWER(username) = LOWER(?)", (username,))
        role_row = cursor.fetchone()
        role = role_row["role"] if role_row else "player"
        
        conn.close()
        
        user_dict = dict(row)
        user_dict["role"] = role
        user_dict["uuid"] = cls.calculate_offline_uuid(user_dict["realname"])
        if user_dict["id"] is None:
            user_dict["id"] = user_dict["rowid"]
        return user_dict

    @classmethod
    def list_all_users(cls) -> List[dict]:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT rowid, id, username, realname, email, regdate FROM authme")
        players = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT username, role FROM user_roles")
        roles = {row["username"].lower(): row["role"] for row in cursor.fetchall()}
        
        conn.close()
        
        for p in players:
            p["role"] = roles.get(p["username"].lower(), "player")
            p["uuid"] = cls.calculate_offline_uuid(p["realname"])
            if p["id"] is None:
                p["id"] = p["rowid"]
            
        return players

    @classmethod
    def create_user(cls, username: str, password_raw: str, email: Optional[str] = None, role: str = "player") -> dict:
        salt = AuthService.generate_salt()
        authme_hash = AuthService.hash_password(password_raw, salt)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Calculate next ID manually since it isn't autoincremented natively by SQLite in AuthMe's default schema
        cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 as next_id FROM authme")
        next_id = cursor.fetchone()["next_id"]
        
        try:
            # Insert into authme
            cursor.execute(
                """
                INSERT INTO authme (id, username, realname, password, email, regdate) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (next_id, username.lower(), username, authme_hash, email, int(datetime.datetime.utcnow().timestamp() * 1000))
            )
            
            # Insert role
            cursor.execute(
                "INSERT OR REPLACE INTO user_roles (username, role) VALUES (?, ?)",
                (username.lower(), role)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise HTTPException(status_code=400, detail="Username already exists")
            
        conn.close()
        return {"id": next_id, "username": username.lower(), "role": role}

    @staticmethod
    def delete_user(username: str):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM authme WHERE LOWER(username) = LOWER(?)", (username,))
        cursor.execute("DELETE FROM user_roles WHERE LOWER(username) = LOWER(?)", (username,))
        cursor.execute("DELETE FROM reset_requests WHERE LOWER(username) = LOWER(?)", (username,))
        
        conn.commit()
        conn.close()

    @staticmethod
    def update_password(username: str, new_password_raw: str):
        salt = AuthService.generate_salt()
        new_hash = AuthService.hash_password(new_password_raw, salt)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE authme SET password = ? WHERE LOWER(username) = LOWER(?)", (new_hash, username))
        conn.commit()
        conn.close()

    @staticmethod
    def update_role(username: str, role: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO user_roles (username, role) VALUES (?, ?)", (username.lower(), role))
        conn.commit()
        conn.close()

class ResetRequestService:
    @staticmethod
    def create_request(username: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO reset_requests (username, status, requested_at) VALUES (?, 'pending', CURRENT_TIMESTAMP)",
            (username.lower(),)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def list_requests() -> List[dict]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, status, requested_at FROM reset_requests WHERE status = 'pending' ORDER BY requested_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def delete_request(username: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reset_requests WHERE LOWER(username) = LOWER(?)", (username,))
        conn.commit()
        conn.close()

# Dependency Injection helpers
def get_current_user(cookie: Optional[str] = Depends(cookie_scheme)) -> dict:
    if not cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    username = AuthService.decode_jwt_token(cookie)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        
    user = PlayerService.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return {"username": user["username"], "role": user["role"]}

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return current_user

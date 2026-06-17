from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from travelmind.config import settings
from travelmind.schemas import Location, RecommendationResponse, UserPreferences


class TravelMemory:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    center TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get_preferences(self, user_id: str = "default") -> UserPreferences:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return UserPreferences()
        return UserPreferences.model_validate_json(row[0])

    def save_preferences(self, preferences: UserPreferences, user_id: str = "default") -> None:
        payload = preferences.model_dump_json()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences(user_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id)
                DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, payload),
            )

    def save_history(
        self,
        center: Location,
        result: RecommendationResponse,
        user_id: str = "default",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO recommendation_history(user_id, center, result) VALUES (?, ?, ?)",
                (user_id, center.model_dump_json(), result.model_dump_json()),
            )

    def recent_history(self, user_id: str = "default", limit: int = 5) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT center, result, created_at
                FROM recommendation_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [{"center": json.loads(row[0]), "result": json.loads(row[1]), "created_at": row[2]} for row in rows]

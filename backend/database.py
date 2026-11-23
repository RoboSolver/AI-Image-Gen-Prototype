import sqlite3
import os
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / 'data' / 'history.db'

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        with self._conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    style TEXT,
                    aspect_ratio TEXT,
                    resolution TEXT,
                    num_images INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    images_json TEXT
                )
            ''')
    
    def add_generation(self, prompt, provider, style, aspect_ratio, resolution, num_images, images):
        import json
        with self._conn() as conn:
            cursor = conn.execute('''
                INSERT INTO generations (prompt, provider, style, aspect_ratio, resolution, num_images, images_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (prompt, provider, style, aspect_ratio, resolution, num_images, json.dumps(images)))
            return cursor.lastrowid
    
    def get_all_generations(self, limit=50, offset=0):
        with self._conn() as conn:
            rows = conn.execute('''
                SELECT * FROM generations
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset)).fetchall()
            return [dict(row) for row in rows]
    
    def get_generation(self, gen_id):
        with self._conn() as conn:
            row = conn.execute('SELECT * FROM generations WHERE id = ?', (gen_id,)).fetchone()
            return dict(row) if row else None
    
    def delete_generation(self, gen_id):
        with self._conn() as conn:
            conn.execute('DELETE FROM generations WHERE id = ?', (gen_id,))
    
    def clear_history(self):
        with self._conn() as conn:
            conn.execute('DELETE FROM generations')
    
    def get_count(self):
        with self._conn() as conn:
            return conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
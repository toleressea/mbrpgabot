import sqlite3
from typing import List, Optional, Tuple
import os
from datetime import datetime

DB_PATH = 'data.sqlite3'

def init_db():
    """Initialize the database and create tables if they don't exist."""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        
        # Create trigger for auto-updating updated_at
        conn.executescript('''
            CREATE TRIGGER IF NOT EXISTS update_plans_timestamp 
            AFTER UPDATE ON plans
            BEGIN
                UPDATE plans SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
        ''')
        conn.close()

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create
def create_plan(channel_id: int, plan_id: str, current_day: int = 0, paused: bool = False) -> int:
    """Create a new plan entry and return its ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO plans (channel_id, plan_id, current_day, paused, created_at, updated_at)
           VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)''',
        (channel_id, plan_id, current_day, paused)
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

# Read
def get_plan(plan_id: int) -> Optional[dict]:
    """Get a plan by its ID."""
    conn = get_db()
    plan = conn.execute('SELECT * FROM plans WHERE id = ?', (plan_id,)).fetchone()
    conn.close()
    return dict(plan) if plan else None

def get_plan_by_channel_and_plan(channel_id: int, plan_id: str) -> Optional[dict]:
    """Get all plans for a specific channel."""
    conn = get_db()
    plan = conn.execute('SELECT * FROM plans WHERE channel_id = ? AND plan_id = ?', (channel_id, plan_id)).fetchone()
    conn.close()
    return dict(plan) if plan else None

def get_plans_by_channel(channel_id: int) -> List[dict]:
    """Get all plans for a specific channel."""
    conn = get_db()
    plans = conn.execute('SELECT * FROM plans WHERE channel_id = ?', (channel_id,)).fetchall()
    conn.close()
    return [dict(p) for p in plans]

def get_all_plans() -> List[dict]:
    """Get all plans."""
    conn = get_db()
    plans = conn.execute('SELECT * FROM plans').fetchall()
    conn.close()
    return [dict(p) for p in plans]

# Update
def update_plan(plan_id: int, channel_id: int = None, plan_type: str = None, 
                current_day: int = None, paused: bool = None) -> bool:
    """Update a plan's details. Only updates provided fields."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Build update query dynamically based on provided fields
    update_fields = []
    values = []
    if channel_id is not None:
        update_fields.append('channel_id = ?')
        values.append(channel_id)
    if plan_type is not None:
        update_fields.append('plan_id = ?')
        values.append(plan_type)
    if current_day is not None:
        update_fields.append('current_day = ?')
        values.append(current_day)
    if paused is not None:
        update_fields.append('paused = ?')
        values.append(paused)
    
    if not update_fields:
        return False
    
    values.append(plan_id)
    query = f'UPDATE plans SET {", ".join(update_fields)} WHERE id = ?'
    cursor.execute(query, values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

# Delete
def delete_plan(plan_id: int) -> bool:
    """Delete a plan by its ID. Returns True if successful."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM plans WHERE id = ?', (plan_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

# Initialize the database when the module is imported
init_db()

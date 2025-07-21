import sqlite3
from passlib.hash import pbkdf2_sha256

class DatabaseManager:
    def __init__(self, db_name='scholarmind.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            
            # Users table
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT UNIQUE NOT NULL,
                         password_hash TEXT NOT NULL,
                         role TEXT NOT NULL,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Research history table
            c.execute('''CREATE TABLE IF NOT EXISTS research_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER NOT NULL,
                         topic TEXT NOT NULL,
                         content_type TEXT NOT NULL,
                         content TEXT NOT NULL,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY(user_id) REFERENCES users(id))''')
            
            # Create admin user if none exists
            c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            if c.fetchone()[0] == 0:
                admin_hash = pbkdf2_sha256.hash("admin123")
                c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                          ("admin", admin_hash, "admin"))
            
            conn.commit()

    def authenticate_user(self, username, password):
        """Authenticate a user"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            
            if user and pbkdf2_sha256.verify(password, user[2]):
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3],
                    'is_admin': user[3] == 'admin'
                }
            return None

    def add_user(self, username, password, role):
        """Add a new user"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                c = conn.cursor()
                password_hash = pbkdf2_sha256.hash(password)
                c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                          (username, password_hash, role))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def get_all_users(self):
        """Get all users"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, role FROM users ORDER BY created_at DESC")
            return c.fetchall()

    def save_research(self, user_id, topic, content_type, content):
        """Save research content to history"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO research_history (user_id, topic, content_type, content) VALUES (?, ?, ?, ?)",
                      (user_id, topic, content_type, content))
            conn.commit()

    def get_research_history(self, user_id, limit=50):
        """Get user's research history"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, topic, content_type, created_at 
                FROM research_history 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return c.fetchall()

    def get_research_content(self, history_id):
        """Get specific research content"""
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT content FROM research_history WHERE id = ?", (history_id,))
            result = c.fetchone()
            return result[0] if result else None
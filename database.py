import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "heart_disease.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── Bootstrap ──────────────────────────────────────────────────────────────────

def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    UNIQUE NOT NULL,
                password_hash   TEXT    NOT NULL,
                full_name       TEXT    NOT NULL,
                email           TEXT    DEFAULT '',
                specialization  TEXT    DEFAULT 'General Medicine',
                created_at      TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS patients (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id         TEXT    UNIQUE,
                full_name           TEXT    NOT NULL,
                date_of_birth       TEXT,
                gender              TEXT,
                phone               TEXT    DEFAULT '',
                email               TEXT    DEFAULT '',
                address             TEXT    DEFAULT '',
                emergency_contact   TEXT    DEFAULT '',
                medical_notes       TEXT    DEFAULT '',
                doctor_id           INTEGER,
                created_at          TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (doctor_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      INTEGER NOT NULL,
                doctor_id       INTEGER NOT NULL,
                result          INTEGER NOT NULL,
                confidence      REAL,
                input_features  TEXT,
                clinical_notes  TEXT    DEFAULT '',
                created_at      TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id)  REFERENCES users(id)
            );
        """)
        # Seed default admin account when db is empty
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, email, specialization) "
                "VALUES (?, ?, ?, ?, ?)",
                ("admin", _hash("admin123"), "Admin Doctor", "admin@hospital.com", "Cardiology"),
            )


# ── User CRUD ──────────────────────────────────────────────────────────────────

def get_user_by_username(username: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def verify_user(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if user and user["password_hash"] == _hash(password):
        return user
    return None


def create_user(username: str, password: str, full_name: str, email: str, specialization: str):
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, email, specialization) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, _hash(password), full_name, email, specialization),
            )
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."


# ── Patient CRUD ───────────────────────────────────────────────────────────────

def get_all_patients(doctor_id: int | None = None) -> list[dict]:
    with _connect() as conn:
        if doctor_id:
            rows = conn.execute(
                "SELECT * FROM patients WHERE doctor_id = ? ORDER BY full_name",
                (doctor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM patients ORDER BY full_name"
            ).fetchall()
        return [dict(r) for r in rows]


def get_patient(patient_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        return dict(row) if row else None


def search_patients(query: str, doctor_id: int | None = None) -> list[dict]:
    like = f"%{query}%"
    with _connect() as conn:
        if doctor_id:
            rows = conn.execute(
                "SELECT * FROM patients "
                "WHERE doctor_id = ? AND (full_name LIKE ? OR national_id LIKE ?) "
                "ORDER BY full_name",
                (doctor_id, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM patients "
                "WHERE full_name LIKE ? OR national_id LIKE ? "
                "ORDER BY full_name",
                (like, like),
            ).fetchall()
        return [dict(r) for r in rows]


def create_patient(
    national_id, full_name, dob, gender,
    phone, email, address, emergency_contact, medical_notes, doctor_id,
) -> tuple[int | None, str | None]:
    try:
        with _connect() as conn:
            cur = conn.execute(
                """INSERT INTO patients
                   (national_id, full_name, date_of_birth, gender, phone, email,
                    address, emergency_contact, medical_notes, doctor_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (national_id, full_name, dob, gender, phone, email,
                 address, emergency_contact, medical_notes, doctor_id),
            )
            return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, "A patient with this National ID already exists."


def update_patient(
    patient_id, national_id, full_name, dob, gender,
    phone, email, address, emergency_contact, medical_notes,
) -> None:
    with _connect() as conn:
        conn.execute(
            """UPDATE patients
               SET national_id=?, full_name=?, date_of_birth=?, gender=?,
                   phone=?, email=?, address=?, emergency_contact=?, medical_notes=?
               WHERE id=?""",
            (national_id, full_name, dob, gender, phone, email,
             address, emergency_contact, medical_notes, patient_id),
        )


def delete_patient(patient_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))


# ── Prediction CRUD ────────────────────────────────────────────────────────────

def save_prediction(
    patient_id: int, doctor_id: int,
    result: int, confidence: float,
    input_features_json: str, clinical_notes: str = "",
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO predictions
               (patient_id, doctor_id, result, confidence, input_features, clinical_notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (patient_id, doctor_id, result, confidence, input_features_json, clinical_notes),
        )
        return cur.lastrowid


def get_patient_predictions(patient_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT pr.*, u.full_name AS doctor_name
               FROM predictions pr
               JOIN users u ON pr.doctor_id = u.id
               WHERE pr.patient_id = ?
               ORDER BY pr.created_at DESC""",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_predictions(doctor_id: int | None = None) -> list[dict]:
    with _connect() as conn:
        if doctor_id:
            rows = conn.execute(
                """SELECT pr.*, pt.full_name AS patient_name, u.full_name AS doctor_name
                   FROM predictions pr
                   JOIN patients pt ON pr.patient_id = pt.id
                   JOIN users u  ON pr.doctor_id  = u.id
                   WHERE pr.doctor_id = ?
                   ORDER BY pr.created_at DESC""",
                (doctor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT pr.*, pt.full_name AS patient_name, u.full_name AS doctor_name
                   FROM predictions pr
                   JOIN patients pt ON pr.patient_id = pt.id
                   JOIN users u  ON pr.doctor_id  = u.id
                   ORDER BY pr.created_at DESC"""
            ).fetchall()
        return [dict(r) for r in rows]


def get_stats(doctor_id: int | None = None) -> dict:
    with _connect() as conn:
        if doctor_id:
            patients  = conn.execute("SELECT COUNT(*) FROM patients    WHERE doctor_id=?",           (doctor_id,)).fetchone()[0]
            total     = conn.execute("SELECT COUNT(*) FROM predictions WHERE doctor_id=?",           (doctor_id,)).fetchone()[0]
            positive  = conn.execute("SELECT COUNT(*) FROM predictions WHERE doctor_id=? AND result=1", (doctor_id,)).fetchone()[0]
        else:
            patients  = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            total     = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            positive  = conn.execute("SELECT COUNT(*) FROM predictions WHERE result=1").fetchone()[0]
    return {
        "patients": patients,
        "total":    total,
        "positive": positive,
        "negative": total - positive,
    }

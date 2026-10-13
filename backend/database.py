import sqlite3
from pwdlib import PasswordHash
from datetime import datetime, timezone



SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def user_exists(empid):
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * 
        FROM Employee
        WHERE empId = (?); 
    """,(empid,),)
    res = cursor.fetchall()
    return res

def get_user_role(empid):
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role 
        FROM Employee 
        WHERE empId = (?)
    """,(empid,),)

    res = cursor.fetchone()
    return res

def get_user_hash(empid):
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password
        FROM Employee
        WHERE empId = (?);
    """,(empid,),)

    res = cursor.fetchall()
    return res

def add_user(name,password,role):
    hashed_password = get_password_hash(password)
    cursor.execute("""
        SELECT empId
        FROM Employee
        ORDER BY empID DESC
        LIMIT 1;
    """)

    id = cursor.fetchone()
    if id is None:
        id = (0,)
    cursor.execute("""
        INSERT INTO Employee
        VALUES (?,?,?,?);
    """,(id[0] + 1,name,hashed_password,role),)

def view_table():
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Employee")
    for row in cursor.fetchall():
        print(row)

def get_user_data(id):
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * 
        FROM Employee 
        WHERE empId = (?)
    """,(id,),)

    res = cursor.fetchone()
    return res


def init_audit_log():
    """Create the AuditLog table if it does not already exist."""
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AuditLog (
            log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id       INTEGER NOT NULL,
            role         TEXT,
            query        TEXT NOT NULL,
            response     TEXT,
            guardrail_blocked INTEGER DEFAULT 0,
            timestamp    TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def log_rag_request(emp_id: int, role: str, query: str, response: str, guardrail_blocked: bool = False):
    """Insert one audit record for a RAG query."""
    conn = sqlite3.connect("EmployeeDatabase.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO AuditLog (emp_id, role, query, response, guardrail_blocked, timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        emp_id,
        role,
        query,
        response,
        1 if guardrail_blocked else 0,
        datetime.now(timezone.utc).isoformat(),
    ))
    conn.commit()
    conn.close()

init_audit_log()

conn = sqlite3.connect("EmployeeDatabase.db")
cursor = conn.cursor()
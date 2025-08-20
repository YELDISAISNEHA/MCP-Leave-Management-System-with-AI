import os
import datetime as dt
import pymysql
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP

# Database connection
@contextmanager
def db_conn():
    conn = pymysql.connect(
        host="localhost",        
        user="root",             
        password="RGUKT123",     # change if needed
        database="LMS_DB"   # make sure this DB exists
    )
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    schema = [
        """
        CREATE TABLE IF NOT EXISTS Employees (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            annual_leave_balance INT NOT NULL DEFAULT 20,
            sick_leave_balance INT NOT NULL DEFAULT 10
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Leaves (
            id INT AUTO_INCREMENT PRIMARY KEY,
            empId INT NOT NULL,
            leave_type ENUM('Annual','Sick') NOT NULL,
            start_date DATE NOT NULL, 
            end_date DATE NOT NULL, 
            days INT NOT NULL,
            reason TEXT,
            status ENUM('Approved','Pending','Rejected') NOT NULL DEFAULT 'Approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empId) REFERENCES Employees(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
        """
    ]

    with db_conn() as conn:
        cur = conn.cursor()
        for stmt in schema:
            cur.execute(stmt)

        # Seed employees if not already present
        cur.execute("SELECT COUNT(1) FROM Employees")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO Employees (id, name, annual_leave_balance, sick_leave_balance) VALUES (%s, %s, %s, %s)",
                [
                    (1, "Alice", 20, 10),
                    (2, "Bob",   20, 10),
                ],
            )

def get_employee(empId: int):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, annual_leave_balance, sick_leave_balance FROM Employees WHERE id=%s",
            (empId,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "annual_leave_balance": row[2], "sick_leave_balance": row[3]}

def update_balance(empId: int, days: int, leave_type: str = "Annual"):
    col = "annual_leave_balance" if leave_type == "Annual" else "sick_leave_balance"
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE Employees SET {col} = {col} - %s WHERE id = %s",
            (days, empId),
        )

def insert_leave(empId: int, start_date: str, end_date: str, days: int, leave_type: str = "Annual", reason: str = ""):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Leaves (empId, leave_type, start_date, end_date, days, reason, status) VALUES (%s, %s, %s, %s, %s, %s, 'Approved')",
            (empId, leave_type, start_date, end_date, days, reason),
        )

def fetch_balance(empId: int):
    emp = get_employee(empId)
    if not emp:
        return None
    return {"Annual": emp["annual_leave_balance"], "Sick": emp["sick_leave_balance"]}

def fetch_history(empId: int):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT start_date, end_date, leave_type, days, status, created_at FROM Leaves WHERE empId=%s ORDER BY created_at DESC",
            (empId,),
        )
        return cur.fetchall()

mcp = FastMCP("LeaveManager")

@mcp.tool()
def get_leave_balance(empId: int):
    """Check how many leave days are left for the employee"""
    init_db()
    bal = fetch_balance(empId)
    if bal:
        return f"{empId} has {bal['Annual']} annual and {bal['Sick']} sick leave days remaining."
    return "Employee ID not found."

@mcp.tool()
def apply_leave(empId: int, start_date: str, end_date: str, leave_type: str = "Annual", reason: str = ""):
    """
    Apply leave for a period (start_date to end_date).
    Dates must be in YYYY-MM-DD format.
    """
    init_db()
    emp = get_employee(empId)
    if not emp:
        return "Employee ID not found."

    # Normalize leave_type
    leave_type = leave_type.capitalize()

    # Calculate days difference
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    requested_days = (end - start).days + 1

    bal = fetch_balance(empId)
    available_balance = bal[leave_type]

    if available_balance < requested_days:
        return f"Insufficient {leave_type} leave balance. You requested {requested_days} day(s) but have only {available_balance}."

    # Deduct balance and insert leave row
    update_balance(empId, requested_days, leave_type)
    insert_leave(empId, start_date, end_date, requested_days, leave_type, reason)

    new_bal = fetch_balance(empId)
    return f"Leave applied for {requested_days} day(s). Remaining balance: {new_bal[leave_type]}."

@mcp.tool()
def get_leave_history(empId: int):
    """Get leave history for the employee"""
    init_db()
    emp = get_employee(empId)
    if not emp:
        return "Employee ID not found."

    rows = fetch_history(empId)
    if not rows:
        return f"No leaves taken for {empId}."

    history = [
        f"{start} to {end} ({leave_type}, {days} day(s), {status}, created {created_at})"
        for (start, end, leave_type, days, status, created_at) in rows
    ]
    return f"Leave history for {empId}: " + "; ".join(history)

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}! How can I assist you with leave management today?"

if __name__ == "__main__":
    init_db()
    mcp.run()

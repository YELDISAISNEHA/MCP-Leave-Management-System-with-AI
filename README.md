# MCP-Leave-Management-System-with-AI
### 1. Objective
  This system is designed to manage employee leaves in a simple and automate with AI. 
  Instead of manually tracking balance leaves, approvals, and history in spreadsheets. 
  This system provides a centralized solution to track available balance leaves based on tyoe of leaves. 
  It also allows employees to apply for leave and deduct leaves automatically. It also maintains the history of leave applications of employees.
### 2. MCP Integration (Run Commands in PowerShell)
- Install Claude Desktop
- Install uv by running <kbd>pip install uv</kbd>
- Run <kbd>uv init my-first-mcp-server</kbd> to create a project directory
- Run <kbd>uv add "mcp[cli]"</kbd> to add mcp cli in your project
- Run <kbd>pip install --upgrade typer</kbd> to upgrade typer library to its latest version
- Copy and Paste main.py code in actual main.py which is created on running the command <kbd>uv init my-first-mcp-server</kbd>
### 3. Database Integration

```
- uv pip install mcp pymysql

CREATE DATABASE LMS_DB;

USE LMS_DB;

CREATE TABLE IF NOT EXISTS Employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    annual_leave_balance INT NOT NULL DEFAULT 20,
    sick_leave_balance INT NOT NULL DEFAULT 10
);

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
);

INSERT INTO Employees (id, name, annual_leave_balance, sick_leave_balance) VALUES(1, 'Alice Johnson', 20, 10);


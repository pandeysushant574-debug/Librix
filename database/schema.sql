-- ============================================================
-- LIBRIX - LIBRARY MANAGEMENT SYSTEM - SQLITE SCHEMA
-- Quality Goal: Q16 - Improve Testing
-- Converted from the original MySQL schema. Same 12 tables, same columns;
-- ENUMs became CHECK constraints, AUTO_INCREMENT became AUTOINCREMENT.
-- ============================================================
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('Admin','Librarian','Assistant')),
  status        TEXT DEFAULT 'Active' CHECK (status IN ('Active','Inactive')),
  email         TEXT,
  phone         TEXT,
  created_at    TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_users_role   ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE TABLE IF NOT EXISTS books (
  book_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  isbn           TEXT UNIQUE,
  title          TEXT NOT NULL,
  author         TEXT NOT NULL,
  category       TEXT,
  publisher      TEXT,
  edition        TEXT,
  year_published INTEGER,
  quantity       INTEGER NOT NULL DEFAULT 0,
  available_qty  INTEGER NOT NULL DEFAULT 0,
  reorder_level  INTEGER NOT NULL DEFAULT 2,
  shelf_location TEXT,
  description    TEXT,
  status         TEXT DEFAULT 'Available' CHECK (status IN ('Available','Unavailable','Inactive')),
  created_at     TEXT DEFAULT (datetime('now','localtime')),
  updated_at     TEXT DEFAULT (datetime('now','localtime')),
  CONSTRAINT chk_books_quantity     CHECK (quantity >= 0),
  CONSTRAINT chk_books_available    CHECK (available_qty >= 0),
  CONSTRAINT chk_books_avail_le_qty CHECK (available_qty <= quantity),
  CONSTRAINT chk_books_reorder      CHECK (reorder_level >= 0)
);
CREATE INDEX IF NOT EXISTS idx_books_title    ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author   ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
CREATE INDEX IF NOT EXISTS idx_books_status   ON books(status);

-- MySQL's "ON UPDATE CURRENT_TIMESTAMP" has no SQLite column syntax; a trigger does the same job.
CREATE TRIGGER IF NOT EXISTS trg_books_updated_at
AFTER UPDATE ON books FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE books SET updated_at = datetime('now','localtime') WHERE book_id = NEW.book_id;
END;

CREATE TABLE IF NOT EXISTS members (
  member_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  member_code     TEXT NOT NULL UNIQUE,
  name            TEXT NOT NULL,
  email           TEXT,
  phone           TEXT,
  address         TEXT,
  membership_date TEXT NOT NULL,
  expiry_date     TEXT,
  status          TEXT DEFAULT 'Active' CHECK (status IN ('Active','Inactive')),
  created_at      TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_members_name   ON members(name);
CREATE INDEX IF NOT EXISTS idx_members_status ON members(status);

CREATE TABLE IF NOT EXISTS issues (
  issue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id     INTEGER NOT NULL REFERENCES books(book_id),
  member_id   INTEGER NOT NULL REFERENCES members(member_id),
  issued_by   INTEGER NOT NULL REFERENCES users(user_id),
  issue_date  TEXT NOT NULL,
  due_date    TEXT NOT NULL,
  return_date TEXT,
  quantity    INTEGER NOT NULL DEFAULT 1,
  status      TEXT DEFAULT 'Issued' CHECK (status IN ('Issued','Returned','Overdue')),
  fine_amount REAL DEFAULT 0,
  created_at  TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_book   ON issues(book_id);
CREATE INDEX IF NOT EXISTS idx_issues_member ON issues(member_id);

CREATE TABLE IF NOT EXISTS returns (
  return_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id         INTEGER NOT NULL REFERENCES issues(issue_id),
  received_by      INTEGER NOT NULL REFERENCES users(user_id),
  return_date      TEXT NOT NULL,
  condition_status TEXT,
  fine_amount      REAL DEFAULT 0,
  remarks          TEXT
);

CREATE TABLE IF NOT EXISTS fines (
  fine_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id     INTEGER NOT NULL REFERENCES issues(issue_id),
  member_id    INTEGER NOT NULL REFERENCES members(member_id),
  days_late    INTEGER DEFAULT 0,
  rate_per_day REAL DEFAULT 5.00,
  amount       REAL DEFAULT 0,
  status       TEXT DEFAULT 'Unpaid' CHECK (status IN ('Unpaid','Paid','Waived')),
  created_at   TEXT DEFAULT (datetime('now','localtime')),
  paid_at      TEXT
);

CREATE TABLE IF NOT EXISTS test_cases (
  test_case_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  test_code       TEXT NOT NULL UNIQUE,
  module          TEXT NOT NULL,
  title           TEXT NOT NULL,
  description     TEXT,
  input_data      TEXT,
  expected_result TEXT NOT NULL,
  test_type       TEXT DEFAULT 'Unit' CHECK (test_type IN ('Unit','Functional','Regression')),
  priority        TEXT DEFAULT 'Medium' CHECK (priority IN ('High','Medium','Low')),
  created_by      INTEGER REFERENCES users(user_id),
  created_at      TEXT DEFAULT (datetime('now','localtime')),
  active          INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS test_results (
  result_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  test_case_id  INTEGER NOT NULL REFERENCES test_cases(test_case_id),
  actual_result TEXT,
  status        TEXT NOT NULL CHECK (status IN ('PASS','FAIL','ERROR')),
  executed_by   INTEGER REFERENCES users(user_id),
  executed_at   TEXT DEFAULT (datetime('now','localtime')),
  duration_ms   REAL,
  error_message TEXT,
  remarks       TEXT
);
CREATE INDEX IF NOT EXISTS idx_results_case ON test_results(test_case_id);

CREATE TABLE IF NOT EXISTS bug_logs (
  bug_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  bug_code      TEXT NOT NULL UNIQUE,
  reported_date TEXT NOT NULL,
  module        TEXT NOT NULL,
  title         TEXT NOT NULL,
  description   TEXT NOT NULL,
  severity      TEXT NOT NULL CHECK (severity IN ('Critical','High','Medium','Low')),
  priority      TEXT NOT NULL CHECK (priority IN ('High','Medium','Low')),
  status        TEXT DEFAULT 'Open' CHECK (status IN ('Open','In Progress','Fixed','Retest','Closed')),
  assigned_to   INTEGER REFERENCES users(user_id),
  root_cause    TEXT,
  fix_action    TEXT,
  retest_result TEXT,
  reported_by   INTEGER REFERENCES users(user_id),
  closed_date   TEXT
);
CREATE INDEX IF NOT EXISTS idx_bugs_module   ON bug_logs(module);
CREATE INDEX IF NOT EXISTS idx_bugs_severity ON bug_logs(severity);
CREATE INDEX IF NOT EXISTS idx_bugs_status   ON bug_logs(status);

CREATE TABLE IF NOT EXISTS boundary_tests (
  boundary_test_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  test_code         TEXT NOT NULL UNIQUE,
  module            TEXT NOT NULL,
  field_name        TEXT NOT NULL,
  min_value         TEXT,
  max_value         TEXT,
  below_boundary    TEXT,
  lower_boundary    TEXT,
  normal_value      TEXT,
  upper_boundary    TEXT,
  above_boundary    TEXT,
  expected_behavior TEXT NOT NULL,
  actual_behavior   TEXT,
  status            TEXT CHECK (status IN ('PASS','FAIL','ERROR')),
  executed_by       INTEGER REFERENCES users(user_id),
  executed_at       TEXT
);

CREATE TABLE IF NOT EXISTS system_logs (
  log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT DEFAULT (datetime('now','localtime')),
  user_id   INTEGER,
  username  TEXT,
  module    TEXT NOT NULL,
  action    TEXT NOT NULL,
  level     TEXT NOT NULL CHECK (level IN ('INFO','WARNING','ERROR','DEBUG')),
  message   TEXT NOT NULL,
  result    TEXT,
  details   TEXT
);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_module    ON system_logs(module);
CREATE INDEX IF NOT EXISTS idx_logs_level     ON system_logs(level);

CREATE TABLE IF NOT EXISTS audit_logs (
  audit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER,
  username    TEXT,
  action      TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id   INTEGER,
  old_value   TEXT,   -- JSON text
  new_value   TEXT,   -- JSON text
  timestamp   TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type);

# Librix — Library Management System (Python edition)

Quality Goal **Q16: Improve Testing**. The whole project is now **pure Python** — backend, database and
test suite — and it needs **nothing to install**: no PHP, no MySQL, no XAMPP, no `pip install`.
The look (colours, gradient, emoji icons) is unchanged, with a new liquid-glass finish and smooth motion.

## Run it

```bash
python app.py
```
Your browser opens at **http://localhost:8000/**. Sign in with:

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | Admin |
| `librarian` | `Librarian@123` | Librarian |
| `assistant` | `Assistant@123` | Assistant |

Needs Python 3.9 or newer (on Windows you can also double-click `run.bat`, on Mac/Linux use `./run.sh`).

Options: `python app.py --port 8080` · `--reset` (wipe the database and restore the demo data) · `--no-browser`.

## What changed from the PHP/MySQL version

| Before | Now |
|---|---|
| PHP 8 backend (controllers / services / validators / middleware) | Python package `librix/` with the **same layers and the same API** |
| MySQL via PDO | **SQLite** (single file `database/librix.db`, created and seeded automatically on first run) |
| bcrypt password hashes | PBKDF2-SHA256 (Python standard library) |
| `router.php` + XAMPP/Apache | built-in Python web server that serves the pages **and** the API on one port |
| PHP test files | `tests/test_librix.py` (`unittest`) |
| Frontend (HTML/CSS/JS, colours, emoji icons) | **Same**, plus `css/glass.css` and `js/transitions.js` |

Because the JSON API is identical, every page behaves as before.

## Project layout

```
app.py                 start here
librix/
  config.py            host, port, database path
  db.py                SQLite connection, transactions, first-run seeding
  security.py          password hashing, sessions
  helpers.py           ApiError, validation helpers, code generator (BUG-006, UT013 ...)
  validators.py        Book / Member / Issue / Test / Bug input validation
  logger.py            system_logs + audit_logs
  router.py            /api/... URL -> controller
  server.py            HTTP server (API + static files)
  controllers/         check permissions + input, call a service
  services/            business rules (issue/return/fines, unit tests, boundary tests, reports ...)
database/
  schema.sql           12 tables (SQLite)
  seed_data.json       demo data (users, books, members, issues, fines, tests, bugs, logs ...)
frontend/              HTML pages, css/ (style, glass), js/
tests/test_librix.py   20 automated tests
```

Request flow: `browser fetch() -> router -> controller -> service -> SQLite`. The frontend never touches the database.

## Roles
- **Admin** — everything, including user management and deleting bugs.
- **Librarian** — books, members, issue/return, fines, quality tools.
- **Assistant** — search, issue/return, read-only views.

## Run the tests
```bash
python -m unittest discover -s tests -v
```
Inside the app, the **Unit Test Cases** page runs UT001–UT012 and **Input Bounds** runs the six boundary
tests against the live code; results are stored in the database and shown on the Quality dashboard.

## The glass look and motion
- Every surface (sidebar, cards, tables, buttons, inputs, modals, toasts) is frosted glass with a rim light,
  a soft sheen and a highlight that follows the cursor; slow light orbs drift behind it.
- Page changes fade out and in; the active menu pill **slides** from the old item to the new one.
- Buttons lift on hover, press in on click and show a ripple; modals and toasts animate in and out;
  tables and cards appear in a short stagger.
- Respects the system "reduce motion" setting. To tweak anything, edit `frontend/css/glass.css`.

## Notes
- Sessions live in memory, so restarting the server signs everyone out (the data stays).
- To allow other devices on your network: `python app.py --host 0.0.0.0` (only on a network you trust).
- The original seed data had one malformed row (`BT-DATE-01`, one value short) that MySQL would have rejected;
  it is repaired in `seed_data.json`.

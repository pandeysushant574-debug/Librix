#!/usr/bin/env python3
"""
Librix - Library Management System
Run:   python app.py
Open:  http://localhost:8000/

No installation needed - uses only the Python standard library (Python 3.9+).
"""
import argparse
import sys
import webbrowser

from librix import config
from librix.db import init_db
from librix.server import make_server


def main() -> int:
    parser = argparse.ArgumentParser(description="Librix Library Management System")
    parser.add_argument("--host", default=config.HOST, help="interface to listen on (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=config.PORT, help="port (default 8000)")
    parser.add_argument("--reset", action="store_true", help="delete the database and re-create it with the demo data")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    args = parser.parse_args()

    if sys.version_info < (3, 9):
        print("Librix needs Python 3.9 or newer.")
        return 1

    first_run = not config.DB_PATH.exists()
    init_db(reset=args.reset)
    if args.reset:
        print("Database reset - demo data restored.")
    elif first_run:
        print(f"Created a new database with demo data: {config.DB_PATH}")

    try:
        server = make_server(args.host, args.port)
    except OSError as exc:
        print(f"Could not start on {args.host}:{args.port} - {exc}\nTry another port:  python app.py --port 8080")
        return 1

    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}/"
    print(f"\n  Librix is running ->  {url}")
    print("  Sign in with  admin / Admin@123   (or librarian / Librarian@123, assistant / Assistant@123)")
    print("  Press Ctrl+C to stop.\n")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Librix. Bye!")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

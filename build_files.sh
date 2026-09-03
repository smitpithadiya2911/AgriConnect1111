python3 -m pip install -r requirements.txt --break-system-packages

# Use a temporary SQLite DB for collectstatic — no MySQL needed during build
DATABASE_URL=sqlite:////tmp/db.sqlite3 python3 manage.py collectstatic --no-input --clear

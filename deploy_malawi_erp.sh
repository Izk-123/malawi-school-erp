#!/bin/bash
# ============================================================================
# Deploy Malawi School ERP to production
# Stack: Django + Channels (Daphne) + Celery + PostgreSQL + Redis + Nginx
#
# Usage:
#   ./deploy_malawi_erp.sh                 # normal deploy / update
#   ./deploy_malawi_erp.sh --reset-db      # DESTRUCTIVE: stop services,
#                                          # kill conns, drop + recreate DB.
#                                          # Only use before real data exists.
# ============================================================================
set -euo pipefail

PROJECT_NAME="malawi-erp"
PROJECT_DIR="/home/project/malawi_school_erp"
VENV_DIR="${PROJECT_DIR}/venv"
REPO_URL="https://github.com/Izk-123/malawi-school-erp.git"
BRANCH="main"

DOMAIN="school.pritechmw.com"
DB_NAME="malawi_erp_db"
DB_USER="malawi_erp_user"
DB_PASS="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"
DJANGO_SECRET="$(openssl rand -base64 48 | tr -d '/+=' | cut -c1-50)"
DAPHNE_PORT=8010

RESET_DB=0
if [ "${1:-}" = "--reset-db" ]; then
    RESET_DB=1
fi

echo "======================================================="
echo " Deploying Malawi School ERP"
echo "   Domain    : ${DOMAIN}"
echo "   Directory : ${PROJECT_DIR}"
echo "   DB        : ${DB_NAME} / ${DB_USER}"
echo "   DB pass   : ${DB_PASS}   (save this!)"
echo "   Reset DB? : ${RESET_DB}"
echo "======================================================="
sleep 2

# ----------------------------------------------------------------------------
# 0. Helper — append a key to .env only if it isn't already defined.
#    Lets us add new required settings without clobbering existing values.
# ----------------------------------------------------------------------------
ensure_env_var() {
    local key="$1" val="$2"
    if ! grep -qE "^${key}=" "${PROJECT_DIR}/.env"; then
        printf '%s=%s\n' "${key}" "${val}" >> "${PROJECT_DIR}/.env"
        echo "    + added ${key}"
    fi
}

# ----------------------------------------------------------------------------
# 1. Clone or update the repo
# ----------------------------------------------------------------------------
if [ ! -d "${PROJECT_DIR}/.git" ]; then
    echo ">>> Cloning repo…"
    git clone --branch "${BRANCH}" "${REPO_URL}" "${PROJECT_DIR}"
else
    echo ">>> Pulling latest code…"
    cd "${PROJECT_DIR}"
    git stash || true
    git pull origin "${BRANCH}"
    git stash pop || true
fi
cd "${PROJECT_DIR}"

# ----------------------------------------------------------------------------
# 2. Python venv + deps
# ----------------------------------------------------------------------------
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip wheel
pip install -r requirements.txt
pip install gunicorn psycopg2-binary   # gunicorn kept for utility; Daphne serves HTTP

# ----------------------------------------------------------------------------
# 3. .env — create on first deploy, then top up missing keys on every run.
#    NOTE: ENABLE_SELF_REGISTRATION defaults OFF in production. Flip to True
#    only after a deliberate decision (see settings.py governance block).
# ----------------------------------------------------------------------------
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo ">>> Writing .env (first-time)"
    cat > "${PROJECT_DIR}/.env" <<EOF
SECRET_KEY=${DJANGO_SECRET}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},204.168.251.91

# --- Absolute public URL (used to build invitation/claim links in SMS) ----
SITE_URL=https://${DOMAIN}

# --- Database -------------------------------------------------------------
DB_ENGINE=postgres
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DB_HOST=127.0.0.1
DB_PORT=5432

# --- Channels / Redis -----------------------------------------------------
CHANNEL_LAYER_BACKEND=redis
REDIS_URL=redis://127.0.0.1:6379/0

# --- Celery ---------------------------------------------------------------
CELERY_ALWAYS_EAGER=False

# --- Security -------------------------------------------------------------
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
CSRF_COOKIE_DOMAIN=${DOMAIN}

# --- Email (swap for your SMTP when ready) --------------------------------
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@${DOMAIN}
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# --- SMS ------------------------------------------------------------------
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=

# --- Payments (fill in when you have PayChangu credentials) ---------------
DEFAULT_PAYMENT_GATEWAY=paychangu
PAYCHANGU_ENABLED=True
PAYCHANGU_BASE_URL=https://api.paychangu.com
PAYCHANGU_SECRET_KEY=
PAYCHANGU_WEBHOOK_SECRET=
PAYCHANGU_TIMEOUT=15

# --- App toggles / governance --------------------------------------------
ENABLE_SELF_REGISTRATION=False
SELF_REGISTRATION_ALLOWED_ROLES=parent
INVITATION_TOKEN_VALIDITY_DAYS=7
HIGH_PRIVILEGE_COOLOFF_HOURS=24
PASSWORD_RESET_TIMEOUT=86400

# --- Attendance -----------------------------------------------------------
ATTENDANCE_EDIT_WINDOW_HOURS=24
ATTENDANCE_PAST_LIMIT_DAYS=7
ATTENDANCE_LOW_THRESHOLD=80
EOF
    chmod 600 "${PROJECT_DIR}/.env"
else
    echo ">>> .env exists — topping up any missing required keys"
fi

# Top up keys the new settings.py requires with no default. Makes the script
# idempotent across settings-file changes — never clobbers existing values.
ensure_env_var SITE_URL                        "https://${DOMAIN}"
ensure_env_var CSRF_TRUSTED_ORIGINS            "https://${DOMAIN}"
ensure_env_var CSRF_COOKIE_DOMAIN              "${DOMAIN}"
ensure_env_var ENABLE_SELF_REGISTRATION        "False"
ensure_env_var SELF_REGISTRATION_ALLOWED_ROLES "parent"
ensure_env_var INVITATION_TOKEN_VALIDITY_DAYS  "7"
ensure_env_var HIGH_PRIVILEGE_COOLOFF_HOURS    "24"
ensure_env_var PASSWORD_RESET_TIMEOUT          "86400"
chmod 600 "${PROJECT_DIR}/.env"

# ----------------------------------------------------------------------------
# 4. PostgreSQL role + database
# ----------------------------------------------------------------------------
sudo -u postgres psql <<SQL
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
      CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';
   ELSE
      ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASS}';
   END IF;
END
\$\$;
SQL

if [ "${RESET_DB}" -eq 1 ]; then
    echo ">>> --reset-db: stopping services and dropping ${DB_NAME}"

    # Stop anything holding a connection to the DB before dropdb.
    sudo systemctl stop daphne-${PROJECT_NAME} \
                      celery-worker-${PROJECT_NAME} \
                      celery-beat-${PROJECT_NAME} 2>/dev/null || true

    # Force-terminate any lingering backends on the target DB.
    sudo -u postgres psql -c \
      "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
        WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" > /dev/null

    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};"
fi

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" \
    | grep -q 1 || sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

# ----------------------------------------------------------------------------
# 5. Migrate  (with recovery briefing if the migration graph is out of sync)
# ----------------------------------------------------------------------------
set +e
python manage.py migrate --noinput
MIGRATE_RC=$?
set -e

if [ "${MIGRATE_RC}" -ne 0 ]; then
    echo ""
    echo "======================================================="
    echo " MIGRATE FAILED."
    echo "======================================================="
    echo "If the error is:  relation \"...\" does not exist"
    echo "  → the DB schema is out of sync with the migration graph."
    echo "    Usually means a migration file was rewritten after it"
    echo "    had already been applied to this database."
    echo ""
    echo "Diagnose:"
    echo "  cd ${PROJECT_DIR} && source venv/bin/activate"
    echo "  python manage.py showmigrations accounts"
    echo ""
    echo "If this DB has NO real data yet (safe):"
    echo "  re-run this script with:  $0 --reset-db"
    echo ""
    echo "If this DB HAS real data (do NOT drop):"
    echo "  1. Dump first:"
    echo "     sudo -u postgres pg_dump ${DB_NAME} > /root/${DB_NAME}-\$(date +%F).sql"
    echo "  2. Reconcile state manually — either:"
    echo "     python manage.py migrate accounts --fake   # mark missing app applied"
    echo "     then hand-write a data migration that backfills the missing table"
    echo "     OR restore the dump into a fresh DB built from the new migration set."
    echo ""
    echo "Aborting before static/systemd steps."
    exit 1
fi

# Seed data — all idempotent, all best-effort.
python manage.py seed_demo_data            || true
python manage.py seed_maneb_syllabus       || true
python manage.py assign_role_permissions   || true
python manage.py collectstatic --noinput

# Superuser only if none exists
python manage.py shell <<'PY' || true
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(is_superuser=True).exists():
    U.objects.create_superuser('admin', 'admin@example.com', 'ChangeMe123!')
    print("Created superuser admin / ChangeMe123!  -- CHANGE THIS PASSWORD")
PY

# ----------------------------------------------------------------------------
# 6. Systemd: Daphne (ASGI — serves HTTP + WebSockets)
# ----------------------------------------------------------------------------
sudo tee /etc/systemd/system/daphne-${PROJECT_NAME}.service > /dev/null <<EOF
[Unit]
Description=Daphne ASGI for Malawi School ERP
After=network.target redis-server.service postgresql.service

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/daphne -b 127.0.0.1 -p ${DAPHNE_PORT} config.asgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ----------------------------------------------------------------------------
# 7. Systemd: Celery worker + beat
# ----------------------------------------------------------------------------
sudo tee /etc/systemd/system/celery-worker-${PROJECT_NAME}.service > /dev/null <<EOF
[Unit]
Description=Celery Worker for Malawi School ERP
After=network.target redis-server.service

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/celery -A config worker -l info
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/celery-beat-${PROJECT_NAME}.service > /dev/null <<EOF
[Unit]
Description=Celery Beat for Malawi School ERP
After=network.target redis-server.service

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/celery -A config beat -l info
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now daphne-${PROJECT_NAME}
sudo systemctl enable --now celery-worker-${PROJECT_NAME}
sudo systemctl enable --now celery-beat-${PROJECT_NAME}

# ----------------------------------------------------------------------------
# 8. Nginx
# ----------------------------------------------------------------------------
sudo tee /etc/nginx/sites-available/${PROJECT_NAME} > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN} 204.168.251.91;

    client_max_body_size 25M;

    # Static files
    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
        expires 30d;
        access_log off;
    }

    # Media (uploads)
    location /media/ {
        alias ${PROJECT_DIR}/media/;
        expires 7d;
    }

    # WebSocket endpoint (Channels)
    location /ws/ {
        proxy_pass http://127.0.0.1:${DAPHNE_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Everything else → Daphne
    location / {
        proxy_pass http://127.0.0.1:${DAPHNE_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/${PROJECT_NAME}
sudo nginx -t
sudo systemctl reload nginx

# ----------------------------------------------------------------------------
# 9. SSL (only if DNS already points at this server)
# ----------------------------------------------------------------------------
if getent hosts "${DOMAIN}" > /dev/null; then
    echo ">>> DNS resolves — running certbot"
    sudo certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos \
        --register-unsafely-without-email --redirect || \
        echo "!! certbot failed — run manually: certbot --nginx -d ${DOMAIN}"
else
    echo ">>> DNS for ${DOMAIN} not yet pointing here — run certbot later:"
    echo "    sudo certbot --nginx -d ${DOMAIN}"
fi

# ----------------------------------------------------------------------------
# 10. Status
# ----------------------------------------------------------------------------
echo "======================================================="
echo " Deployment complete."
echo " Services:"
for s in daphne-${PROJECT_NAME} celery-worker-${PROJECT_NAME} celery-beat-${PROJECT_NAME}; do
    systemctl is-active --quiet $s && echo "   ✔ $s" || echo "   ✘ $s  (see: journalctl -u $s -n 50)"
done
echo ""
echo " Login:  https://${DOMAIN}/   (or http://204.168.251.91/)"
echo " Admin:  https://${DOMAIN}/admin/"
echo " Superuser: admin / ChangeMe123!  <-- CHANGE IT"
echo "======================================================="

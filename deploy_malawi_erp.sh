#!/bin/bash
# ============================================================================
# Deploy Malawi School ERP to production
# Stack: Django + Channels (Daphne) + Celery + PostgreSQL + Redis + Nginx
# ============================================================================
set -euo pipefail

PROJECT_NAME="malawi-erp"                # systemd prefix, e.g. daphne-malawi-erp
PROJECT_DIR="/home/project/malawi_school_erp"
VENV_DIR="${PROJECT_DIR}/venv"
REPO_URL="https://github.com/Izk-123/malawi-school-erp.git"
BRANCH="main"

DOMAIN="school.pritechmw.com"               # <-- CHANGE ME
DB_NAME="malawi_erp_db"
DB_USER="malawi_erp_user"
DB_PASS="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"   # auto-generated
DJANGO_SECRET="$(openssl rand -base64 48 | tr -d '/+=' | cut -c1-50)"
DAPHNE_PORT=8010                         # pick a free port (J&N uses 8001)

echo "======================================================="
echo " Deploying Malawi School ERP"
echo "   Domain    : ${DOMAIN}"
echo "   Directory : ${PROJECT_DIR}"
echo "   DB        : ${DB_NAME} / ${DB_USER}"
echo "   DB pass   : ${DB_PASS}   (save this!)"
echo "======================================================="
sleep 2

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
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip wheel
pip install -r requirements.txt
pip install gunicorn psycopg2-binary   # gunicorn kept for utility (Daphne serves HTTP)

# ----------------------------------------------------------------------------
# 3. Production .env  (only created once — never overwritten)
# ----------------------------------------------------------------------------
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo ">>> Writing .env (first-time only)"
    cat > "${PROJECT_DIR}/.env" <<EOF
SECRET_KEY=${DJANGO_SECRET}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},204.168.251.91

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

# --- App toggles ----------------------------------------------------------
ENABLE_SELF_REGISTRATION=True
EOF
    chmod 600 "${PROJECT_DIR}/.env"
else
    echo ">>> .env already exists — leaving it alone"
fi

# ----------------------------------------------------------------------------
# 4. PostgreSQL database + role
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

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" \
    | grep -q 1 || sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

# ----------------------------------------------------------------------------
# 5. Migrate, seed, static
# ----------------------------------------------------------------------------
python manage.py migrate --noinput
python manage.py seed_demo_data            || true
python manage.py seed_maneb_syllabus       || true
python manage.py assign_role_permissions   || true
python manage.py collectstatic --noinput

# create superuser non-interactively if none exists
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
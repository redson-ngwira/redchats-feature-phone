#!/bin/bash
# RedChats — PythonAnywhere Deployment Script
# Run this in a PythonAnywhere Bash console after cloning the repo.
#
# Usage:
#   git clone https://github.com/redson-ngwira/redchats-feature-phone.git
#   cd redchats-feature-phone
#   bash deploy.sh

set -e

PROJECT_DIR="$HOME/redchats-feature-phone"
VENV_NAME="redchats"

echo "=== RedChats Deployment ==="

# 1. Create virtualenv
echo "[1/5] Creating virtualenv..."
mkvirtualenv --python=/usr/bin/python3.10 $VENV_NAME 2>/dev/null || workon $VENV_NAME

# 2. Install dependencies
echo "[2/5] Installing dependencies..."
cd $PROJECT_DIR
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 3. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "[3/5] Creating .env file..."
    SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > .env << EOF
SECRET_KEY=$SECRET
CEREBRAS_API_KEY=your-cerebras-api-key-here
DEBUG=False
ALLOWED_HOSTS=redchats.pythonanywhere.com
EOF
    echo ""
    echo "  >>> IMPORTANT: Edit .env and add your Cerebras API key:"
    echo "      nano $PROJECT_DIR/.env"
    echo ""
else
    echo "[3/5] .env already exists, skipping."
fi

# 4. Run migrations
echo "[4/5] Running migrations..."
python manage.py migrate --noinput

# 5. Collect static files
echo "[5/5] Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "NEXT STEPS on PythonAnywhere:"
echo ""
echo "1. Edit .env with your Cerebras API key:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Go to the Web tab:"
echo "   - Click 'Add a new web app'"
echo "   - Choose 'Manual configuration'"
echo "   - Python version: 3.10"
echo ""
echo "3. In the Web tab, set:"
echo "   - Source code: $PROJECT_DIR"
echo "   - Virtualenv: $HOME/.virtualenvs/$VENV_NAME"
echo ""
echo "4. Edit the WSGI file (link in Web tab):"
echo "   - Delete everything, paste the WSGI config below"
echo ""
echo "5. In the Web tab, set Static files:"
echo "   - URL: /static/"
echo "   - Directory: $PROJECT_DIR/staticfiles"
echo ""
echo "6. Click 'Reload redchats.pythonanywhere.com'"
echo ""
echo "=== WSGI FILE CONTENTS ==="
echo "Copy this into your WSGI config file:"
echo ""
cat << 'WSGI'
import os
import sys

path = '/home/redchats/redchats-feature-phone'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'featurechat.settings'

from dotenv import load_dotenv
load_dotenv(path + '/.env')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
WSGI

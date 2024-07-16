#!/bin/bash
set -e

cd /home/ec2-user/app

echo "Step 1: Setting up Python environment"
sudo amazon-linux-extras enable python3.8
sudo yum install -y python3.8
/usr/bin/python3.8 -m venv venv
source venv/bin/activate

echo "Step 2: Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "Step 3: Setting up environment variables"
# The .env file will be created by the GitHub Actions workflow

echo "Step 4: Setting PYTHONPATH"
export PYTHONPATH=$PYTHONPATH:/home/ec2-user/app

echo "Step 5: Checking PostgreSQL client"
which psql
psql --version

echo "Step 6: Testing database connection"
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_ENDPOINT" -U "$DB_USERNAME" -d "$DB_NAME" -c "SELECT 1;"; then
  echo "Database connection failed"
  exit 1
fi

echo "Step 7: Ensuring database exists"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_ENDPOINT" -U "$DB_USERNAME" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || PGPASSWORD="$DB_PASSWORD" psql -h "$DB_ENDPOINT" -U "$DB_USERNAME" -d postgres -c "CREATE DATABASE $DB_NAME"

echo "Step 8: Running Django commands"
cd api_project
python manage.py collectstatic --noinput
python manage.py migrate

echo "Step 9: Restarting uvicorn service"
sudo systemctl restart uvicorn.service

echo "Deployment completed successfully"
#!/usr/bin/env bash
# exit on error
set -o errexit

cd backend
pip install -r requirements.txt

# Run migrations and seed data
python manage.py migrate
python manage.py seed_demo

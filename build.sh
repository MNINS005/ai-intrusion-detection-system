#!/usr/bin/env bash
pip install -r requirements.txt
cd ids_project
python manage.py collectstatic --no-input
python manage.py migrate
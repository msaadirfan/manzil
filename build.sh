#!/bin/bash
python manage.py collectstatic --no-input --settings=manzilproject.settings_production

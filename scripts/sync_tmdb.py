#!/usr/bin/env python
"""Shortcut script — delegates to the Django management command."""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinefind.settings')
django.setup()

from django.core.management import call_command
call_command('sync_tmdb', *sys.argv[1:])

import os

from nova.settings.base import *  # noqa: F401, F403

env = os.environ.get('DJANGO_SETTINGS_MODULE', 'nova.settings.development')

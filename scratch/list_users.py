import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PlaceSync.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.all():
    print(f"Username: {u.username} | Role: {getattr(u, 'role', 'N/A')}")

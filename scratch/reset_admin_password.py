import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PlaceSync.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
try:
    u = User.objects.get(username='mitadmin')
    u.set_password('Admin@123')
    u.save()
    print("mitadmin password set to Admin@123 successfully!")
except User.DoesNotExist:
    print("mitadmin user not found!")

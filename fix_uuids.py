import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presentation_project.settings')
django.setup()

from generator.models import Presentation

print("Fixing UUIDs...")
count = 0
for p in Presentation.objects.all():
    p.unique_id = uuid.uuid4()
    p.save()
    count += 1
print(f"Updated {count} presentations with new UUIDs.")

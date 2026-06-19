
import os
import django
import sys
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presentation_project.settings')
django.setup()

from generator.models import Presentation
import urllib.parse

def debug():
    # UUID from metadata
    uuid = '114f9c18-47f8-4c16-94e2-9df4eada1af5'
    
    print(f"DEBUG: Checking presentation {uuid}")
    print(f"BASE_DIR: {settings.BASE_DIR}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    try:
        p = Presentation.objects.get(unique_id=uuid)
    except Presentation.DoesNotExist:
        print("Presentation not found!")
        return

    print(f"Topic: {p.topic}")
    sections = p.article_data.get('sections', [])
    
    for i, s in enumerate(sections):
        print(f"\n--- Section {i} ---")
        img_url = s.get('image')
        print(f"Stored Image URL: '{img_url}'")
        
        if not img_url:
            print("No image assigned.")
            continue
            
        if img_url.startswith('/media/'):
            rel = img_url.replace('/media/', '', 1)
            rel = urllib.parse.unquote(rel)
            abs_path = os.path.join(settings.MEDIA_ROOT, rel)
            
            print(f"Resolved Relative: {rel}")
            print(f"Resolved Absolute: {abs_path}")
            print(f"Exists: {os.path.exists(abs_path)}")
        else:
            print("URL does not start with /media/")

if __name__ == '__main__':
    debug()

import os
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Presentation

@receiver(post_delete, sender=Presentation)
def cleanup_presentation_files(sender, instance, **kwargs):
    """
    Clean up the entire folder associated with the presentation when it is deleted.
    """
    # Construct the folder path
    # Pattern: MEDIA_ROOT/presentations/user_<id>/<uuid>/
    
    if instance.unique_id:
        user_id = instance.user.id if instance.user else 'anonymous'
        presentation_folder = f"presentations/user_{user_id}/{instance.unique_id}"
        full_folder_path = os.path.join(settings.MEDIA_ROOT, presentation_folder)
        
        if os.path.exists(full_folder_path):
            try:
                shutil.rmtree(full_folder_path)
                print(f"Details: Deleted presentation folder: {full_folder_path}")
            except Exception as e:
                print(f"Error deleting presentation folder {full_folder_path}: {e}")
    
    # Legacy cleanup (optional, checks for loose files if they were saved that way)
    # The new structure puts everything in the folder, so rmtree covers it.

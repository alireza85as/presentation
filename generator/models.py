from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
import os

def presentation_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/presentations/user_<id>/<uuid>/<filename>
    user_id = instance.user.id if instance.user else 'anonymous'
    return f'presentations/user_{user_id}/{instance.unique_id}/{filename}'



class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Code valid for 10 minutes
        return timezone.now() <= self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.email} - {self.code}"
class Presentation(models.Model):
    """Model to store presentation generation requests and results"""
    
    topic = models.CharField(max_length=500, verbose_name="Topic")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presentations', null=True, blank=True)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    pdf_file = models.FileField(upload_to=presentation_directory_path, blank=True, null=True, verbose_name="PDF File")
    pptx_file = models.FileField(upload_to=presentation_directory_path, blank=True, null=True, verbose_name="PowerPoint File")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        verbose_name="Status"
    )
    error_message = models.TextField(blank=True, null=True, verbose_name="Error Message")
    article_data = models.JSONField(null=True, blank=True, verbose_name="Article Data")  # Stores editable article content
    presentation_type = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF Only'), ('pptx', 'PowerPoint Only'), ('both', 'Both')],
        default='both',
        verbose_name="Presentation Type"
    )
    template_name = models.CharField(
        max_length=20,
        choices=[
            ('classic', 'Classic'),
            ('modern', 'Modern'),
            ('creative', 'Creative/Professional'),
        ],
        default='classic',
        verbose_name="Template Style"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
    
    def __str__(self):
        return f"{self.topic} - {self.status}"

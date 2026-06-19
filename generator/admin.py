from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Presentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    """Admin interface for Presentation model"""
    actions = ['delete_selected_presentations']
    list_display = ('topic', 'user', 'status', 'created_at', 'presentation_type', 'has_pdf', 'has_pptx', 'delete_button')
    list_filter = ('status', 'created_at', 'user', 'presentation_type', 'template_name')
    search_fields = ('topic', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'unique_id')
    ordering = ('-created_at',)
    
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True
    
    def has_pptx(self, obj):
        return bool(obj.pptx_file)
    has_pptx.boolean = True

    def delete_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Delete</a>',
            reverse('admin:generator_presentation_delete', args=[obj.pk])
        )
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True

    @admin.action(description='Delete selected presentations (Full Cleanup)')
    def delete_selected_presentations(self, request, queryset):
        count = queryset.count()
        for obj in queryset:
            obj.delete() # Triggers signals
        self.message_user(request, f"{count} presentations were successfully deleted.")


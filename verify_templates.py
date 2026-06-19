import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presentation_project.settings')
django.setup()

from generator.services.pdf_service import PDFService

def verify_templates():
    print("Starting Template Verification...")
    service = PDFService()
    
    article = {
        'title': 'Template Test Presentation',
        'topic': 'Demonstrating PDF Styles',
        'introduction': 'This is a test to verify the visual styles of different PDF templates. Each template should look distinct.',
        'sections': [
            {
                'title': 'Section 1',
                'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
            },
            {
                'title': 'Section 2 (Persian Test)',
                'content': 'این یک متن فارسی برای تست نمایش صحیح فونت و راست‌چین بودن در قالب‌های مختلف است.'
            }
        ],
        'conclusion': 'End of test presentation.'
    }
    
    # Create output directory
    output_dir = 'test_outputs'
    os.makedirs(output_dir, exist_ok=True)
    
    templates = ['classic', 'modern', 'creative']
    
    for template in templates:
        try:
            print(f"Generating {template} template...", end=" ")
            output_path = os.path.join(output_dir, f'test_{template}.pdf')
            # Pass empty list for images for now
            service.generate_pdf(article, [], output_path, template_name=template)
            print(f"Success! Saved to {output_path}")
        except Exception as e:
            print(f"FAILED! Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    verify_templates()

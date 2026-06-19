import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'presentation_project.settings')
django.setup()

from generator.services.pdf_service import PDFService

def test_pdf_generation():
    service = PDFService()
    
    article = {
        'title': 'The Future of AI',
        'topic': 'Artificial Intelligence Trends 2025',
        'introduction': 'Artificial Intelligence is rapidly evolving, reshaping industries and daily life. This presentation explores the key trends defining the future of AI.',
        'sections': [
            {
                'title': 'Generative AI Revolution',
                'content': 'Generative AI models are becoming more sophisticated, capable of creating realistic images, videos, and text. This technology is transforming creative industries.'
            },
            {
                'title': 'AI in Healthcare',
                'content': 'AI is revolutionizing healthcare with predictive analytics, personalized medicine, and robotic surgery assistance.'
            },
            {
                'title': 'Ethical Considerations',
                'content': 'As AI becomes more powerful, ethical concerns regarding bias, privacy, and job displacement must be addressed.'
            }
        ],
        'conclusion': 'The future of AI holds immense promise but requires responsible development and regulation to ensure it benefits humanity.'
    }
    
    # Dummy image paths (assuming some exist or we handle missing ones gracefully)
    # I'll use a placeholder if possible, or just empty list to test text layout first.
    # The service code handles missing images gracefully?
    # It checks `if image_paths`.
    
    output_path = 'test_presentation.pdf'
    
    try:
        print("Generating PDF...")
        path = service.generate_pdf(article, [], output_path)
        print(f"PDF generated successfully at: {path}")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pdf_generation()

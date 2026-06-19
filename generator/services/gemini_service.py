import google.generativeai as genai
from django.conf import settings


class GeminiService:
    """Service class for interacting with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini API with API key from settings"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in settings")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use gemini-2.5-flash (latest fast model)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_article(self, topic: str) -> dict:
        """
        Generate a well-structured article about the given topic
        
        Args:
            topic: The topic to write about
            
        Returns:
            dict: Article structure with title, introduction, sections, and conclusion
        """
        prompt = f"""
Write a professional, presentation-ready article about: {topic}

The article should be structured as follows:
1. A compelling title
2. An engaging introduction (2-3 paragraphs)
3. Main content divided into 4-6 sections, each with:
   - A clear section header
   - 2-3 paragraphs of informative content
4. A strong conclusion

Use a professional, informative tone suitable for a business presentation.
Make the content engaging and easy to understand.

Please format your response as follows:
TITLE: [Your title here]

INTRODUCTION:
[Introduction paragraphs]

SECTION: [Section 1 Title]
[Section 1 content]

SECTION: [Section 2 Title]
[Section 2 content]

[Continue for all sections...]


CONCLUSION:
[Conclusion paragraphs]

PAY ATTENTION:
If the text is Persian, be sure to write in Persian. If the text is English or any other language, be sure to write in the same language.
"""
        
        try:
            response = self.model.generate_content(prompt)
            article_text = response.text
            
            # Parse the response into structured data
            article = self._parse_article(article_text)
            return article
            
        except Exception as e:
            raise Exception(f"Failed to generate article: {str(e)}")

    def translate_text(self, text: str, target_language: str = 'English') -> str:
        """
        Translate text to the target language
        
        Args:
            text: Text to translate
            target_language: Target language (default: English)
            
        Returns:
            str: Translated text
        """
        prompt = f"Translate the following text to {target_language}. Only return the translated text, no explanations or other text:\n\n{text}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return text  # Return original text if translation fails

    def generate_image_search_query(self, topic: str) -> str:
        """
        Generate an optimized English search query for finding images
        
        Args:
            topic: The topic to find images for
            
        Returns:
            str: Optimized search query
        """
        prompt = f"""
        Generate a short, effective English search query to find high-quality, relevant images for the topic: '{topic}'. 
        The query should be suitable for Google Images. 
        Focus on the main subject. 
        Do not include words like "high quality", "hd", "image of", etc. just the subject keywords.
        Return ONLY the query text, nothing else.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Query generation failed: {str(e)}")
            # Fallback to simple translation
            return self.translate_text(topic, 'English')
    
    def _parse_article(self, text: str) -> dict:
        """
        Parse the generated article text into structured format
        
        Args:
            text: Raw article text from Gemini
            
        Returns:
            dict: Structured article data
        """
        lines = text.strip().split('\n')
        article = {
            'title': '',
            'introduction': '',
            'sections': [],
            'conclusion': ''
        }
        
        current_section = None
        current_content = []
        section_title = ''  # Initialize to prevent NameError
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TITLE:'):
                article['title'] = line.replace('TITLE:', '').strip()
            
            elif line.startswith('INTRODUCTION:'):
                current_section = 'introduction'
                current_content = []
            
            elif line.startswith('SECTION:'):
                # Save previous section if exists
                if current_section == 'section' and current_content:
                    article['sections'].append({
                        'title': section_title,
                        'content': '\n\n'.join(current_content)
                    })
                
                section_title = line.replace('SECTION:', '').strip()
                current_section = 'section'
                current_content = []
            
            elif line.startswith('CONCLUSION:'):
                # Save previous section if exists
                if current_section == 'section' and current_content:
                    article['sections'].append({
                        'title': section_title,
                        'content': '\n\n'.join(current_content)
                    })
                
                current_section = 'conclusion'
                current_content = []
            
            elif line:  # Non-empty line
                current_content.append(line)
        
        # Save the last section
        if current_section == 'introduction':
            article['introduction'] = '\n\n'.join(current_content)
        elif current_section == 'section' and current_content:
            article['sections'].append({
                'title': section_title,
                'content': '\n\n'.join(current_content)
            })
        elif current_section == 'conclusion':
            article['conclusion'] = '\n\n'.join(current_content)
        
        return article

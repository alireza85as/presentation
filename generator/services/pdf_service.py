from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from PIL import Image as PILImage
import os
import urllib.request
import datetime
from django.conf import settings

# --- Template Strategies ---

class BasePDFTemplate:
    """Base class for PDF templates"""
    def __init__(self, service):
        self.service = service
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        
    def setup_styles(self):
        """Setup paragraph styles"""
        pass
        
    def draw_cover(self, canvas, doc):
        """Draw cover page background/elements"""
        pass
        
    def draw_page(self, canvas, doc):
        """Draw content page margins/headers/footers"""
        pass
        
    def get_frame_margin(self):
        return 2.5 * cm

    def get_cover_title_style(self):
        return self.styles['CoverTitle']
    
    def get_cover_subtitle_style(self):
        return self.styles['CoverSubtitle']

class ClassicTemplate(BasePDFTemplate):
    """The original professional design"""
    def setup_styles(self):
        self.primary_color = HexColor('#1A237E')  # Deep Indigo
        self.secondary_color = HexColor('#283593')
        self.accent_color = HexColor('#FFD700')    # Gold
        self.text_color = HexColor('#212121')
        
        # Cover Title
        self.styles.add(ParagraphStyle(
            name='CoverTitle', parent=self.styles['Heading1'],
            fontSize=36, textColor=HexColor('#FFFFFF'), alignment=TA_CENTER,
            fontName=self.service.persian_font, leading=45, spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle', parent=self.styles['Heading2'],
            fontSize=18, textColor=HexColor('#E0E0E0'), alignment=TA_CENTER,
            fontName=self.service.persian_font, leading=24
        ))
        
        # Headers & Body
        self._add_common_styles(self.primary_color, self.text_color)
        
        # Intro Box
        self._add_intro_style(HexColor('#000000'), HexColor('#E8EAF6')) # Light Indigo bg

    def _add_common_styles(self, header_color, body_color):
        self.styles.add(ParagraphStyle(
            name='SectionHeader_RTL', parent=self.styles['Heading2'],
            fontSize=24, textColor=header_color, spaceAfter=20, spaceBefore=30,
            fontName=self.service.persian_font, leading=32, alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader_LTR', parent=self.styles['Heading2'],
            fontSize=24, textColor=header_color, spaceAfter=20, spaceBefore=30,
            fontName=self.service.persian_font, leading=32, alignment=TA_LEFT
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBody_RTL', parent=self.styles['BodyText'],
            fontSize=13, textColor=body_color, alignment=TA_RIGHT, spaceAfter=15,
            leading=24, fontName=self.service.persian_font
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBody_LTR', parent=self.styles['BodyText'],
            fontSize=14, textColor=body_color, alignment=TA_LEFT, spaceAfter=15,
            leading=25, fontName=self.service.persian_font
        ))

    def _add_intro_style(self, text_color, bg_color):
         self.styles.add(ParagraphStyle(
            name='Introduction_RTL', parent=self.styles['BodyText'],
            fontSize=14, textColor=text_color, alignment=TA_RIGHT, spaceAfter=25,
            leading=26, fontName=self.service.persian_font, backColor=bg_color,
            borderPadding=20, borderRadius=8
        ))
         self.styles.add(ParagraphStyle(
            name='Introduction_LTR', parent=self.styles['BodyText'],
            fontSize=15, textColor=text_color, alignment=TA_LEFT, spaceAfter=25,
            leading=28, fontName=self.service.persian_font, backColor=bg_color,
            borderPadding=20, borderRadius=8
        ))

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        
        canvas.setStrokeColor(self.accent_color)
        canvas.setLineWidth(3)
        canvas.line(30, A4[1] - 30, A4[0] - 30, A4[1] - 30)
        canvas.line(30, 30, A4[0] - 30, 30)
        
        canvas.setFillColor(HexColor('#283593'))
        canvas.circle(A4[0], 0, 150, fill=True, stroke=False)
        canvas.circle(0, A4[1], 100, fill=True, stroke=False)
        canvas.restoreState()

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(1)
        canvas.line(40, A4[1] - 50, A4[0] - 40, A4[1] - 50)
        canvas.line(40, 50, A4[0] - 40, 50)
        
        text = f"Page {canvas.getPageNumber()}"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 40, 35, text)
        canvas.drawString(40, 35, datetime.datetime.now().strftime("%Y-%m-%d"))
        canvas.restoreState()

class ModernTemplate(ClassicTemplate):
    """Sleek, high contrast, dark headers on white"""
    def setup_styles(self):
        self.primary_color = HexColor('#212121') # Almost Black
        self.accent_color = HexColor('#00BFA5')  # Teal Accent
        self.text_color = HexColor('#424242')
        
        # Cover Title (Dark bg with teal accent)
        self.styles.add(ParagraphStyle(
            name='CoverTitle', parent=self.styles['Heading1'],
            fontSize=40, textColor=HexColor('#FFFFFF'), alignment=TA_LEFT,
            fontName=self.service.persian_font, leading=50, spaceAfter=20,
            leftIndent=50
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle', parent=self.styles['Heading2'],
            fontSize=20, textColor=self.accent_color, alignment=TA_LEFT,
            fontName=self.service.persian_font, leading=28,
            leftIndent=50
        ))
        
        self._add_common_styles(self.primary_color, self.text_color)
        self._add_intro_style(HexColor('#333333'), HexColor('#E0F2F1')) # Light Teal bg

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        # Dark Background for cover
        canvas.setFillColor(HexColor('#212121'))
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        
        # Teal Geometric Accent on side
        canvas.setFillColor(self.accent_color)
        canvas.rect(0, 0, 30, A4[1], fill=True, stroke=False)
        
        canvas.restoreState()

    def draw_page(self, canvas, doc):
        canvas.saveState()
        # Minimalist page number
        canvas.setFillColor(HexColor('#9E9E9E'))
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(A4[0] - 30, 30, str(canvas.getPageNumber()))
        
        # Small accent block top right
        canvas.setFillColor(self.accent_color)
        canvas.rect(A4[0]-20, A4[1]-40, 20, 40, fill=True, stroke=False)
        canvas.restoreState()

class CreativeTemplate(ClassicTemplate):
    """Colorful and artistic"""
    def setup_styles(self):
        self.primary_color = HexColor('#6A1B9A') # Purple
        self.secondary_color = HexColor('#AB47BC')
        self.accent_color = HexColor('#FF6F00')  # Orange
        self.text_color = HexColor('#3E2723')
        
        self.styles.add(ParagraphStyle(
            name='CoverTitle', parent=self.styles['Heading1'],
            fontSize=42, textColor=self.primary_color, alignment=TA_CENTER,
            fontName=self.service.persian_font, leading=50, spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle', parent=self.styles['Heading2'],
            fontSize=20, textColor=self.accent_color, alignment=TA_CENTER,
            fontName=self.service.persian_font, leading=26
        ))
        
        self._add_common_styles(self.primary_color, self.text_color)
        self._add_intro_style(HexColor('#212121'), HexColor('#F3E5F5')) # Light Purple bg

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        # White background
        canvas.setFillColor(HexColor('#FFFFFF'))
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        
        # Colorful blobs
        canvas.setFillColor(HexColor('#F3E5F5')) # Very light purple
        canvas.circle(A4[0]/2, A4[1]/2, 300, fill=True, stroke=False)
        
        canvas.setFillColor(self.primary_color)
        p = canvas.beginPath()
        p.moveTo(0, A4[1])
        p.lineTo(A4[0], A4[1])
        p.lineTo(A4[0], A4[1]-150)
        p.curveTo(A4[0]-100, A4[1]-250, 100, A4[1]-50, 0, A4[1]-200)
        p.close()
        canvas.drawPath(p, fill=True, stroke=False)
        
        canvas.setFillColor(self.accent_color)
        canvas.circle(A4[0]-50, 100, 40, fill=True, stroke=False)
        canvas.restoreState()

    def draw_page(self, canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, A4[1]-20, A4[0], 20, fill=True, stroke=False)
        
        # Footer decoration
        canvas.setStrokeColor(self.accent_color)
        canvas.setLineWidth(2)
        canvas.line(0, 0, A4[0], 0)
        
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(self.primary_color)
        canvas.drawCentredString(A4[0]/2, 15, str(canvas.getPageNumber()))
        canvas.restoreState()


class PDFService:
    """Service class for generating beautiful PDF presentations with Persian support"""
    
    def __init__(self):
        """Initialize PDF service"""
        self._setup_persian_font()
    
    def _setup_persian_font(self):
        """Download and register Persian font (Vazirmatn)"""
        try:
            from django.conf import settings
            fonts_dir = os.path.join(settings.MEDIA_ROOT, 'fonts')
            os.makedirs(fonts_dir, exist_ok=True)
            font_path = os.path.join(fonts_dir, 'Vazirmatn-Regular.ttf')
            
            if not os.path.exists(font_path):
                print("Downloading Persian font (Vazirmatn)...")
                urls = [
                    'https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/fonts/ttf/Vazirmatn-Regular.ttf',
                    'https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/Vazirmatn-Regular.ttf',
                    'https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf'
                ]
                success = False
                for url in urls:
                    try:
                        print(f"Trying to download from: {url}")
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=30) as response:
                            with open(font_path, 'wb') as out_file:
                                out_file.write(response.read())
                        print(f"Successfully downloaded font from {url}")
                        success = True
                        break
                    except Exception as e:
                        print(f"Failed to download from {url}: {str(e)}")
                
                if not success:
                    raise Exception("Failed to download font from all mirrors")
            
            pdfmetrics.registerFont(TTFont('Vazirmatn', font_path))
            self.persian_font = 'Vazirmatn'
            
        except Exception as e:
            print(f"Warning: Could not load Persian font: {str(e)}")
            self.persian_font = 'Helvetica'
    
    def _has_persian(self, text):
        if not text: return False
        persian_ranges = [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]
        for char in text:
            code = ord(char)
            for start, end in persian_ranges:
                if start <= code <= end: return True
        return False
    
    def _clean_markdown(self, text):
        if not text: return ""
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'^#+\s*', '', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        return text.strip()

    def _wrap_text(self, text, max_width, font_name, font_size):
        if not text: return []
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        space_width = pdfmetrics.stringWidth(' ', font_name, font_size)
        
        for word in words:
            word_width = pdfmetrics.stringWidth(word, font_name, font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width + space_width
                else:
                    lines.append(word)
                    current_line = []
                    current_width = 0
        if current_line: lines.append(' '.join(current_line))
        return lines

    def _prepare_text(self, text, max_width=None, font_name=None, font_size=None):
        """Prepare text for body paragraphs - simple reshaping without manual wrapping"""
        if not text: return ""
        text = self._clean_markdown(text)
        if self._has_persian(text):
            try:
                from arabic_reshaper import reshape
                from bidi.algorithm import get_display
                # Simple reshape and bidi - let ReportLab handle wrapping
                reshaped_text = reshape(text)
                return get_display(reshaped_text, base_dir='R')
            except ImportError:
                return text
        return text
    
    def _prepare_title(self, text, max_width=None, font_name=None, font_size=None):
        """Prepare title text - preserves word boundaries for proper Persian wrapping"""
        if not text: return ""
        text = self._clean_markdown(text)
        if self._has_persian(text):
            try:
                from arabic_reshaper import reshape
                from bidi.algorithm import get_display
                
                # For titles, preserve word boundaries
                if max_width and font_name and font_size:
                    words = text.split(' ')
                    lines = []
                    current_line = []
                    
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        test_width = pdfmetrics.stringWidth(test_line, font_name, font_size)
                        
                        if test_width <= max_width or not current_line:
                            current_line.append(word)
                        else:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Reshape and apply bidi to each line
                    processed_lines = []
                    for line in lines:
                        reshaped = reshape(line)
                        bidi_line = get_display(reshaped, base_dir='R')
                        processed_lines.append(bidi_line)
                    
                    return "<br/>".join(processed_lines)
                else:
                    # No width constraint
                    reshaped_text = reshape(text)
                    return get_display(reshaped_text, base_dir='R')
            except ImportError:
                return text
        return text
    
    def _resize_image(self, image_path: str, max_width: float, max_height: float) -> tuple:
        try:
            img = PILImage.open(image_path)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            if img_width > max_width:
                width = max_width
                height = width * aspect
            else:
                width = img_width
                height = img_height
            if height > max_height:
                height = max_height
                width = height / aspect
            return (width, height)
        except Exception as e:
            print(f"Error resizing image {image_path}: {str(e)}")
            return (max_width * 0.8, max_height * 0.8)

    def generate_pdf(self, article: dict, image_paths: list, output_path: str, template_name: str = 'classic') -> str:
        """Generate PDF using the selected template strategy"""
        
        # Select Template
        if template_name == 'modern':
            template = ModernTemplate(self)
        elif template_name == 'creative':
            template = CreativeTemplate(self)
        else:
            template = ClassicTemplate(self)
            
        dirname = os.path.dirname(output_path)
        if dirname: os.makedirs(dirname, exist_ok=True)
        
        cover_frame = Frame(0, 0, A4[0], A4[1], id='cover', showBoundary=0)
        margin = template.get_frame_margin()
        content_frame = Frame(margin, margin, A4[0] - 2*margin, A4[1] - 2*margin, id='content', showBoundary=0)
        
        cover_template = PageTemplate(id='Cover', frames=[cover_frame], onPage=template.draw_cover)
        content_template = PageTemplate(id='Content', frames=[content_frame], onPage=template.draw_page)
        
        doc = BaseDocTemplate(output_path, pagesize=A4, pageTemplates=[cover_template, content_template])
        
        story = []
        
        # --- COVER ---
        story.append(Spacer(1, 4 * inch if template_name == 'creative' else 3 * inch))
        
        title_text = article.get('title', 'Presentation')
        title_prepared = self._prepare_text(title_text)
        story.append(Paragraph(title_prepared, template.get_cover_title_style()))
        
        story.append(Spacer(1, 0.5 * inch))
        
        if article.get('topic'):
             topic_text = self._prepare_text(article.get('topic'))
             story.append(Paragraph(topic_text, template.get_cover_subtitle_style()))
        
        story.append(NextPageTemplate('Content'))
        story.append(PageBreak())
        
        # --- INTRODUCTION ---
        if article.get('introduction'):
            intro_text = article['introduction']
            is_persian = self._has_persian(intro_text)
            
            header_text = "مقدمه" if is_persian else "Introduction"
            header_style = template.styles['SectionHeader_RTL'] if is_persian else template.styles['SectionHeader_LTR']
            story.append(Paragraph(self._prepare_text(header_text), header_style))
            
            content_style = template.styles['Introduction_RTL'] if is_persian else template.styles['Introduction_LTR']
            available_width = (A4[0] - 2*margin) - 40 # Approx padding
            
            prepared_intro = self._prepare_text(intro_text, max_width=available_width, font_name=content_style.fontName, font_size=content_style.fontSize)
            story.append(Paragraph(prepared_intro, content_style))
            story.append(Spacer(1, 0.4 * inch))
        
        # --- SECTIONS ---
        sections = article.get('sections', [])
        # --- SECTIONS ---
        sections = article.get('sections', [])
        
        for idx, section in enumerate(sections):
            image_url = section.get('image')
            image_path_to_use = None
            
            if image_url:
                # Robust Path Resolution: Convert URL to filesystem path directly
                if image_url.startswith('/media/'):
                     # Remove '/media/' and join with MEDIA_ROOT
                     relative_path = image_url.replace('/media/', '', 1)
                     # Handle URL decoding (spaces to %20 etc)
                     import urllib.parse
                     relative_path = urllib.parse.unquote(relative_path)
                     
                     possible_path = os.path.join(str(settings.MEDIA_ROOT), relative_path)
                     print(f"DEBUG: Resolving Image\n URL: {image_url}\n Relative: {relative_path}\n Absolute: {possible_path}\n Exists: {os.path.exists(possible_path)}")
                     
                     if os.path.exists(possible_path):
                         image_path_to_use = str(possible_path)
                     else:
                         print(f"Warning: Image file not found at {possible_path}")
                else:
                    # Fallback for old round-robin or other URLs? 
                    print(f"Warning: Image URL {image_url} does not start with /media/")

            # FALLBACK: If explicit selection failed or wasn't provided, use Auto-Assign (Round Robin)
            if not image_path_to_use and image_paths:
                image_path_to_use = str(image_paths[idx % len(image_paths)])
                print(f"DEBUG: Using Fallback Image for section {idx}: {image_path_to_use}")

            if image_path_to_use:
                try:
                    img_width, img_height = self._resize_image(image_path_to_use, A4[0] - 2*margin, 3.5 * inch)
                    img = Image(image_path_to_use, width=img_width, height=img_height)
                    img.hAlign = 'CENTER'
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(img)
                    story.append(Spacer(1, 0.2 * inch))
                except Exception as e:
                     print(f"Error adding image: {e}")
            
            section_title = section.get('title', f'Section {idx + 1}')
            section_content = section.get('content', '')
            is_persian = self._has_persian(section_content)
            
            header_style = template.styles['SectionHeader_RTL'] if is_persian else template.styles['SectionHeader_LTR']
            # Use _prepare_title for headers to preserve word boundaries
            prepared_title = self._prepare_title(section_title, max_width=A4[0]-2*margin, font_name=header_style.fontName, font_size=header_style.fontSize)
            story.append(Paragraph(prepared_title, header_style))
            
            content_style = template.styles['CustomBody_RTL'] if is_persian else template.styles['CustomBody_LTR']
            available_width = (A4[0] - 2*margin) - 10
            prepared_content = self._prepare_text(section_content, max_width=available_width, font_name=content_style.fontName, font_size=content_style.fontSize)
            story.append(Paragraph(prepared_content, content_style))
            story.append(Spacer(1, 0.3 * inch))
            
        # --- CONCLUSION ---
        if article.get('conclusion'):
            story.append(Spacer(1, 0.5 * inch))
            conclusion_text = article['conclusion']
            is_persian = self._has_persian(conclusion_text)
            
            header_text = "نتیجه‌گیری" if is_persian else "Conclusion"
            header_style = template.styles['SectionHeader_RTL'] if is_persian else template.styles['SectionHeader_LTR']
            story.append(Paragraph(self._prepare_text(header_text), header_style))
            
            content_style = template.styles['CustomBody_RTL'] if is_persian else template.styles['CustomBody_LTR']
            available_width = (A4[0] - 2*margin) - 10
            prepared_conclusion = self._prepare_text(conclusion_text, max_width=available_width, font_name=content_style.fontName, font_size=content_style.fontSize)
            story.append(Paragraph(prepared_conclusion, content_style))
            
        doc.build(story)
        return output_path

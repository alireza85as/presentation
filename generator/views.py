from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import string

from .forms import TopicForm
from .models import Presentation, EmailVerification
from .services.gemini_service import GeminiService
from .services.image_service import ImageService
from .services.pdf_service import PDFService
from .services.pptx_service import PPTXService
import os


# --- Auth Views ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'رمز عبور و تکرار آن مطابقت ندارند')
            return render(request, 'generator/register.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده است')
            return render(request, 'generator/register.html')
            
        # Create user
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        user.is_active = False # Inactive until verified
        user.save()
        
        # Generate verification code
        code = ''.join(random.choices(string.digits, k=6))
        EmailVerification.objects.create(user=user, code=code)
        
        # Send email
        print(f"Verification Code for {email}: {code}")
        send_mail(
            'کد تایید ایمیل',
            f'کد تایید شما: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        request.session['verification_email'] = email
        return redirect('verify_email')
        
    return render(request, 'generator/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if not user.is_active:
                # Check if verification exists
                if hasattr(user, 'email_verification') and not user.email_verification.is_verified:
                    request.session['verification_email'] = email
                    return redirect('verify_email')
                else:
                    messages.error(request, 'حساب کاربری شما غیرفعال است')
            else:
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, 'ایمیل یا رمز عبور اشتباه است')
            
    return render(request, 'generator/login.html')

def verify_email_view(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('login')
        
    if request.method == 'POST':
        code = request.POST.get('code')
        # Combine 6 inputs if sent separately, or just one
        if not code:
            code = "".join([request.POST.get(f'code_{i}') for i in range(1, 7)])
            
        try:
            user = User.objects.get(email=email)
            verification = user.email_verification
            
            if verification.code == code and verification.is_valid():
                user.is_active = True
                user.save()
                verification.is_verified = True
                verification.save()
                
                # Auto login
                login(request, user)
                return redirect('email_verified')
            else:
                messages.error(request, 'کد وارد شده نامعتبر یا منقضی شده است')
        except User.DoesNotExist:
            messages.error(request, 'کاربر یافت نشد')
            
    return render(request, 'generator/verify_email.html', {'email': email})

@login_required
def email_verified_view(request):
    return render(request, 'generator/email_verified.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# --- Dashboard Views ---

def cleanup_user_presentations(user):
    """Keep only the 10 most recent presentations for the user."""
    presentations = Presentation.objects.filter(user=user).order_by('-created_at')
    if presentations.count() > 10:
        # Get the IDs of the top 10 to keep
        keep_ids = list(presentations.values_list('id', flat=True)[:10])
        
        # Get the ones to delete
        to_delete = Presentation.objects.filter(user=user).exclude(id__in=keep_ids)
        
        for presentation in to_delete:
            # Delete files from filesystem
            if presentation.pdf_file:
                if os.path.isfile(presentation.pdf_file.path):
                    os.remove(presentation.pdf_file.path)
            if presentation.pptx_file:
                if os.path.isfile(presentation.pptx_file.path):
                    os.remove(presentation.pptx_file.path)
            # Delete record
            presentation.delete()

@login_required
def dashboard_view(request):
    # Filter by user
    recent_docs = Presentation.objects.filter(user=request.user, status='completed').order_by('-created_at')[:5]
    all_docs = Presentation.objects.filter(user=request.user, status='completed').order_by('-created_at')
    
    return render(request, 'generator/dashboard.html', {
        'user': request.user,
        'recent_docs': recent_docs,
        'all_docs': all_docs
    })

@login_required
def create_pdf_view(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        template = request.POST.get('template', 'classic')
        if topic:
            # Create with user
            presentation = Presentation.objects.create(
                topic=topic, 
                status='pending', 
                presentation_type='pdf',
                user=request.user,
                template_name=template
            )
            cleanup_user_presentations(request.user)
            return redirect('generate', pk=presentation.pk)
    # Redirect GET to dashboard
    return redirect('/dashboard/?section=create-pdf')

@login_required
def create_ppt_view(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        if topic:
            # Create with user
            presentation = Presentation.objects.create(
                topic=topic, 
                status='pending', 
                presentation_type='pptx',
                user=request.user
            )
            cleanup_user_presentations(request.user)
            return redirect('generate', pk=presentation.pk)
    # Redirect GET to dashboard
    return redirect('/dashboard/?section=create-ppt')

@login_required
def saved_documents_view(request):
    # Redirect to dashboard
    return redirect('/dashboard/?section=saved-documents')

@login_required
def settings_view(request):
    return render(request, 'generator/settings.html', {'user': request.user})


# --- Existing Generation Logic (Preserved but adapted) ---

def index(request):
    # Show landing page for everyone
    return render(request, 'generator/index.html')

def generate_presentation(request, pk):
    """Generate presentation PDF for the given topic"""
    # Ensure user is logged in
    if not request.user.is_authenticated:
        return redirect('login')

    presentation = get_object_or_404(Presentation, pk=pk)
    
    # If already completed, redirect to success page (or dashboard)
    if presentation.status == 'completed':
        return redirect('dashboard') # Changed to dashboard for better flow
    
    # If pending, show generating page and start processing
    if presentation.status == 'pending':
        presentation.status = 'processing'
        presentation.save()
        return render(request, 'generator/generating.html', {'presentation': presentation})
    
    # If processing, try to generate
    if presentation.status == 'processing':
        try:
            print(f"[DEBUG] Starting generation for topic: {presentation.topic}")
            
            gemini_service = GeminiService()
            article = gemini_service.generate_article(presentation.topic)
            
            search_query = gemini_service.generate_image_search_query(presentation.topic)
            image_service = ImageService()
            # Define presentation directory relative to MEDIA_ROOT
            user_id = presentation.user.id if presentation.user else 'anonymous'
            unique_id = getattr(presentation, 'unique_id', 'legacy') # Handle cases where unique_id might not be set yet if migration hasn't run fully or for old objects
            
            presentation_folder = f"presentations/user_{user_id}/{unique_id}"
            full_presentation_folder = os.path.join(settings.MEDIA_ROOT, presentation_folder)
            
            # Create folder if not exists
            os.makedirs(full_presentation_folder, exist_ok=True)
            
            # Images will be saved in presentation_folder/images
            # ImageService appends 'images' if we don't handle it, but wait.
            # get_images_for_topic joins MEDIA_ROOT + sub_folder.
            # So if sub_folder is 'presentations/...', images go there.
            # But ImageService logic allows any sub_folder.
            # Let's verify ImageService again. 
            # It just joins settings.MEDIA_ROOT, sub_folder.
            # So if I pass presentation_folder + "/images", it works.
            
            images_sub_folder = os.path.join(presentation_folder, "images")
            image_paths = image_service.get_images_for_topic(search_query, num_images=5, sub_folder=images_sub_folder)
            
            pdf_service = PDFService()
            safe_topic = "".join(c for c in presentation.topic if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_topic = safe_topic.replace(' ', '_')[:50]
            
            # Generate PDF if requested
            if presentation.presentation_type in ['pdf', 'both']:
                pdf_filename = f"{safe_topic}_presentation.pdf"
                pdf_path = os.path.join(full_presentation_folder, pdf_filename)
                
                # Note: pdf_service.generate_pdf expects full absolute path for output
                pdf_service.generate_pdf(article, image_paths, pdf_path, template_name=presentation.template_name)
                
                # Save relative path to model (so .url works correctly)
                presentation.pdf_file.name = f"{presentation_folder}/{pdf_filename}" # Assigning string to FileField works as relative path

            # Generate PPTX if requested
            if presentation.presentation_type in ['pptx', 'both']:
                pptx_service = PPTXService()
                pptx_filename = f"{safe_topic}_presentation.pptx"
                pptx_path = os.path.join(full_presentation_folder, pptx_filename)
                
                pptx_service.generate_presentation(article, image_paths, pptx_path)
                presentation.pptx_file.name = f"{presentation_folder}/{pptx_filename}"
            
            # Auto-assign images to sections for editor (round-robin)
            if image_paths and article.get('sections'):
                for i, section in enumerate(article['sections']):
                    # Convert absolute path to /media/ URL
                    img_path = str(image_paths[i % len(image_paths)])
                    # Extract relative path from MEDIA_ROOT
                    relative = img_path.replace(str(settings.MEDIA_ROOT), '').replace('\\', '/').lstrip('/')
                    section['image'] = f'/media/{relative}'
            
            # Save article data for editing later
            presentation.article_data = article
            presentation.status = 'completed'
            presentation.save()
            
            return redirect('dashboard') # Redirect to dashboard after success
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Generation failed: {error_msg}")
            
            # Smart Error Handling
            if "429" in error_msg or "quota" in error_msg.lower():
                readable_error = "سقف مجاز استفاده از هوش مصنوعی (Google Gemini) پر شده است. لطفاً حدود ۱ دقیقه صبر کنید و مجدداً تلاش نمایید."
            else:
                readable_error = f"خطا در تولید ارائه: {error_msg}"
                
            presentation.status = 'failed'
            presentation.error_message = readable_error
            presentation.save()
            messages.error(request, readable_error)
            return redirect('dashboard')
    
    if presentation.status == 'failed':
        messages.error(request, f'Generation failed: {presentation.error_message}')
        return redirect('dashboard')
    
    return render(request, 'generator/generating.html', {'presentation': presentation})

def success(request, pk):
    # Deprecated in favor of dashboard, but kept for compatibility if needed
    return redirect('dashboard')

def download_pdf(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    if presentation.status != 'completed' or not presentation.pdf_file:
        raise Http404("PDF not found")
    pdf_path = presentation.pdf_file.path
    if not os.path.exists(pdf_path):
        raise Http404("PDF file not found")
    response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
    return response

def download_pptx(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    if presentation.status != 'completed' or not presentation.pptx_file:
        raise Http404("PowerPoint not found")
    pptx_path = presentation.pptx_file.path
    if not os.path.exists(pptx_path):
        raise Http404("PowerPoint file not found")
    response = FileResponse(open(pptx_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(pptx_path)}"'
    return response


# --- Editor Views ---

@login_required
def edit_presentation(request, pk):
    """Editor page for presentation"""
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    if presentation.status != 'completed':
        messages.error(request, 'فقط ارائه‌های تکمیل شده قابل ویرایش هستند.')
        return redirect('dashboard')
    return render(request, 'generator/editor.html', {'presentation': presentation})


@login_required
def api_get_content(request, pk):
    """API: Get article content for editing"""
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    # Get image paths for this presentation
    image_paths = []
    if presentation.unique_id:
        user_id = presentation.user.id if presentation.user else 'anonymous'
        images_folder = os.path.join(settings.MEDIA_ROOT, f'presentations/user_{user_id}/{presentation.unique_id}/images')
        if os.path.exists(images_folder):
            for f in os.listdir(images_folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    image_paths.append(f'/media/presentations/user_{user_id}/{presentation.unique_id}/images/{f}')
    
    return JsonResponse({
        'article': presentation.article_data,
        'template': presentation.template_name,
        'topic': presentation.topic,
        'images': image_paths,
        'pdf_url': presentation.pdf_file.url if presentation.pdf_file else None
    })


@login_required
def api_save_content(request, pk):
    """API: Save article content without regenerating PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    import json
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        presentation.article_data = data.get('article')
        if data.get('template'):
            presentation.template_name = data.get('template')
        presentation.save()
        return JsonResponse({'status': 'saved', 'message': 'ذخیره شد'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_regenerate_pdf(request, pk):
    """API: Save content and regenerate PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    import json
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        article = data.get('article')
        template_name = data.get('template', presentation.template_name)
        
        # Save article data
        presentation.article_data = article
        presentation.template_name = template_name
        
        # Get existing image paths
        image_paths = []
        if presentation.unique_id:
            user_id = presentation.user.id if presentation.user else 'anonymous'
            images_folder = os.path.join(settings.MEDIA_ROOT, f'presentations/user_{user_id}/{presentation.unique_id}/images')
            if os.path.exists(images_folder):
                for f in sorted(os.listdir(images_folder)):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        image_paths.append(os.path.join(images_folder, f))
        
        # Regenerate PDF only
        pdf_service = PDFService()
        
        safe_topic = "".join(c for c in presentation.topic if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_topic = safe_topic.replace(' ', '_')[:50]
        
        user_id = presentation.user.id if presentation.user else 'anonymous'
        presentation_folder = f"presentations/user_{user_id}/{presentation.unique_id}"
        full_folder = os.path.join(settings.MEDIA_ROOT, presentation_folder)
        os.makedirs(full_folder, exist_ok=True)
        
        # PDF file only
        pdf_filename = f"{safe_topic}_presentation.pdf"
        pdf_path = os.path.join(full_folder, pdf_filename)
        
        # Generate new PDF
        pdf_service.generate_pdf(article, image_paths, pdf_path, template_name=template_name)

        # Update model
        presentation.pdf_file.name = f"{presentation_folder}/{pdf_filename}"
        presentation.save()
        
        return JsonResponse({
            'status': 'regenerated',
            'message': 'PDF با موفقیت بازسازی شد',
            'pdf_url': presentation.pdf_file.url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_upload_image(request, pk):
    """API: Upload new image for presentation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image file provided'}, status=400)
    
    try:
        uploaded_file = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'error': 'نوع فایل مجاز نیست'}, status=400)
        
        # Save to presentation folder
        user_id = presentation.user.id if presentation.user else 'anonymous'
        images_folder = os.path.join(settings.MEDIA_ROOT, f'presentations/user_{user_id}/{presentation.unique_id}/images')
        os.makedirs(images_folder, exist_ok=True)
        
        # Generate unique filename
        import uuid
        ext = uploaded_file.name.split('.')[-1]
        filename = f"uploaded_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(images_folder, filename)
        
        # Save file
        with open(filepath, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        image_url = f'/media/presentations/user_{user_id}/{presentation.unique_id}/images/{filename}'
        
        return JsonResponse({
            'status': 'uploaded',
            'message': 'تصویر آپلود شد',
            'image_url': image_url,
            'filename': filename
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_search_images(request, pk):
    """API: Search for new images"""
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    query = request.GET.get('q', presentation.topic)
    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)
    
    try:
        print(f"[DEBUG] Searching images for: {query}")
        image_service = ImageService()
        image_urls = image_service.search_images(query, num_images=10)
        print(f"[DEBUG] Found {len(image_urls)} images")
        return JsonResponse({'images': image_urls})
    except Exception as e:
        print(f"[ERROR] Image search failed: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_download_image(request, pk):
    """API: Download image from URL and add to presentation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    import json
    import requests
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        image_url = data.get('url')
        
        if not image_url:
            return JsonResponse({'error': 'URL required'}, status=400)
        
        # Download image
        response = requests.get(image_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Determine extension
        content_type = response.headers.get('content-type', '')
        if 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            ext = 'jpg'
        
        # Save to presentation folder
        user_id = presentation.user.id if presentation.user else 'anonymous'
        images_folder = os.path.join(settings.MEDIA_ROOT, f'presentations/user_{user_id}/{presentation.unique_id}/images')
        os.makedirs(images_folder, exist_ok=True)
        
        import uuid
        filename = f"downloaded_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(images_folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        local_url = f'/media/presentations/user_{user_id}/{presentation.unique_id}/images/{filename}'
        
        return JsonResponse({
            'status': 'downloaded',
            'message': 'تصویر اضافه شد',
            'image_url': local_url,
            'filename': filename
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_delete_image(request, pk):
    """API: Delete an image from presentation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    import json
    presentation = get_object_or_404(Presentation, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        
        if not filename:
            return JsonResponse({'error': 'Filename required'}, status=400)
        
        # Security: only allow deleting from this presentation's folder
        user_id = presentation.user.id if presentation.user else 'anonymous'
        images_folder = os.path.join(settings.MEDIA_ROOT, f'presentations/user_{user_id}/{presentation.unique_id}/images')
        filepath = os.path.join(images_folder, os.path.basename(filename))
        
        if os.path.exists(filepath) and filepath.startswith(images_folder):
            os.remove(filepath)
            return JsonResponse({'status': 'deleted', 'message': 'تصویر حذف شد'})
        else:
            return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

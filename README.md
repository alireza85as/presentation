# Django Presentation Generator

A powerful Django web application that generates beautiful presentation PDFs using AI. Simply enter a topic, and the system will:

1. Generate a professional article using Google Gemini AI
2. Find relevant high-quality images using Google Custom Search
3. Create a beautifully formatted PDF with embedded images

## Features

- 🤖 **AI-Powered Content**: Uses Google Gemini to generate presentation-ready articles
- 🖼️ **Smart Image Search**: Automatically finds and downloads relevant images
- 📄 **Beautiful PDFs**: Creates professionally styled PDFs with custom layout
- 🎨 **Modern UI**: Minimalistic and attractive frontend with smooth animations
- 📱 **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## Setup Instructions

### 1. Install Dependencies

Make sure you have Python 3.8+ installed, then create a virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

- **GEMINI_API_KEY**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **GOOGLE_SEARCH_API_KEY**: Get from [Google Cloud Console](https://console.cloud.google.com/)
- **GOOGLE_SEARCH_ENGINE_ID**: Create a custom search engine at [Google CSE](https://programmablesearchengine.google.com/)

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Usage

1. Enter a topic in the input field (e.g., "Artificial Intelligence", "Climate Change")
2. Click "Generate Presentation"
3. Wait while the system generates your presentation
4. Download the PDF when ready

## Project Structure

```
presentation/
├── generator/                  # Main Django app
│   ├── services/              # Service classes
│   │   ├── gemini_service.py  # Gemini API integration
│   │   ├── image_service.py   # Image search & download
│   │   └── pdf_service.py     # PDF generation
│   ├── templates/             # HTML templates
│   ├── static/                # CSS, JS, images
│   ├── models.py              # Database models
│   ├── views.py               # View functions
│   └── forms.py               # Form definitions
├── presentation_project/       # Django project settings
├── media/                     # Generated files
│   ├── images/                # Downloaded images
│   └── pdfs/                  # Generated PDFs
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## Technologies Used

- **Backend**: Django 5.0
- **AI**: Google Gemini API
- **Image Search**: Google Custom Search API
- **PDF Generation**: ReportLab
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Image Processing**: Pillow

## API Limitations

- **Gemini API**: Free tier has rate limits
- **Google Custom Search**: Free tier limited to 100 queries/day

## License

This project is open source and available for educational purposes.

## Support

For issues or questions, please create an issue in the repository.

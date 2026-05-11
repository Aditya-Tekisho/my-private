# WhatsApp Automation App

A simple WhatsApp automation application built with Python FastAPI.

## Features

- **WhatsApp Web Connection** - Connect using QR code scan
- **Session Management** - Save and restore login sessions
- **Instant Messaging** - Send messages instantly to any contact
- **Scheduled Messages** - Schedule messages to send later
- **Contact Management** - Search and manage contacts
- **Message History** - View sent/pending/failed messages
- **Status Tracking** - Track message delivery status

## Tech Stack

- **Backend**: FastAPI + Python
- **Database**: SQLite
- **WhatsApp**: Selenium with WhatsApp Web
- **Scheduler**: APScheduler
- **UI**: Vanilla HTML/CSS/JS

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Chrome/Chromium

For WhatsApp Web automation, you need Chrome or Chromium browser:

```bash
# Ubuntu/Debian
sudo apt-get install chromium chromium-driver

# Or use Chrome
# Download from: https://www.google.com/chrome/
```

### 3. Run the Application

```bash
cd /workspace/project
python -m app.main
```

### 4. Access the App

Open your browser and navigate to:
- **http://localhost:8000** - Main application
- **http://localhost:8000/docs** - API documentation

## Usage Guide

### Connecting to WhatsApp

1. Click "Connect to WhatsApp" button
2. Scan the QR code with your WhatsApp mobile app
3. Session is automatically saved

### Sending Messages

1. Enter a message in the text box
2. Search and select a contact
3. Click "Send Now" for instant delivery
4. Or select a date/time and click "Schedule" for later

### Viewing History

- All messages are stored with their status
- Filter by: All, Sent, Pending, or Failed
- Search message history

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/qr | Get QR code for login |
| POST | /api/auth/check | Check login status |
| GET | /api/contacts | List contacts |
| GET | /api/contacts/search | Search contacts |
| POST | /api/messages/send | Send message now |
| POST | /api/messages/schedule | Schedule message |
| GET | /api/messages/history | Get message history |
| DELETE | /api/messages/{id} | Delete message |

## Project Structure

```
app/
├── main.py           # FastAPI application
├── config.py         # Configuration settings
├── models.py        # Pydantic models
├── database.py      # SQLite database
├── whatsapp.py      # WhatsApp Web automation
├── scheduler.py    # Message scheduler
└── routers/
    ├── auth.py     # Authentication routes
    ├── contacts.py # Contact routes
    ├── messages.py# Message routes
    └── history.py # History routes
static/
├── index.html      # Main UI
├── style.css      # Styles
└── app.js        # Frontend JavaScript
```

## Troubleshooting

### Chrome Driver Issues

If you encounter Chrome driver issues:
```bash
# Check Chrome version
google-chrome --version

# Download matching chromedriver
# https://chromedriver.chromium.org/downloads
```

### Session Expiry

WhatsApp sessions expire. Re-scan QR code if:
- Session shows as disconnected
- Messages fail to send

### Scheduling Issues

Make sure the application is running when scheduled messages are due.
The scheduler checks pending messages every minute.

## License

MIT
# Emotional Diary with Analytics

A web-based diary application with emotion tracking, calendar, and advanced analytics using Flask and MongoDB.

## Features

- **User Authentication:** Register and login securely.
- **Diary Entries:** Add, edit, delete, and view diary entries with date, content, and emotions.
- **Calendar View:** Visualize and filter entries by date.
- **Emotion Analytics:** Visualize emotion frequency over time (bar/line chart).
- **Negative Insights:** Automatic detection and visualization of negative words/emotions (pie chart, wordcloud).
- **Wordcloud:** See most frequent words in negative entries.
- **Responsive UI:** Modern, mobile-friendly interface.

## Tech Stack

- **Backend:** Python, Flask, Flask-PyMongo, MongoDB
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Authentication:** JWT-based (see `utils.py`)
- **Visualization:** Chart.js (bar, pie, wordcloud)

## Project Structure

```
/MongoDB
├── backend/
│   ├── main.py              # Main Flask application
│   ├── requirements.txt     # Python dependencies
│   ├── Setup/
│   │   ├── MongoDB_Setup.js # Database initialization
│   │   ├── backup_db.py     # Database backup script
│   │   ├── restore_db.py    # Database restore script
│   │   └── setup_dev.ps1    # Development environment setup
│   ├── Docker/
│   │   ├── Dockerfile       # Container configuration
│   │   └── docker-compose.dev.yml
│   ├── static/             # Frontend static assets
│   │   ├── css/
│   │   └── js/
│   └── .env.example        # Environment variables template
├── templates/              # HTML templates
│   ├── login.html
│   ├── index.html
│   └── charts.html
└── README.md
```

## Setup & Installation

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NguyenTien204/Emotional-Dinary.git
   cd MongoDB
   ```

2. **Set up environment:**
   ```bash
   # Copy environment template
   cp backend/.env.example backend/.env
   # Edit .env with your settings
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Initialize MongoDB:**
   - Ensure MongoDB is running locally on `mongodb://localhost:27017`
   - Run the setup script:
     ```bash
     mongosh < backend/Setup/MongoDB_Setup.js
     ```

5. **Run the application:**
   ```bash
   python backend/main.py
   ```

### Docker Setup

1. **Build and start containers:**
   ```bash
   cd backend/Docker
   docker-compose -f docker-compose.dev.yml up --build
   ```

### Ngrok Setup for Remote Access

1. **Install ngrok** from https://ngrok.com/download

2. **Start ngrok tunnel:**
   ```bash
   ngrok http 5000
   ```

3. **Update your application URL** in `.env`:
   ```
   APP_URL=https://your-ngrok-url.ngrok.io
   ```

## Environment Variables

Required variables in `.env`:
- `MONGO_URI`: MongoDB connection string
- `SECRET_KEY`: Application secret key
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)

## Database Management

### Backup
```bash
python backend/Setup/backup_db.py
```

### Restore
```bash
python backend/Setup/restore_db.py path/to/backup.json
```

## API Documentation

### Authentication Endpoints
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /logout` - User logout

### Diary Endpoints
- `GET /entries` - Get all entries for current user
- `POST /entries` - Create new diary entry
- `GET /entries/<id>` - Get specific entry
- `PUT /entries/<id>` - Update entry
- `DELETE /entries/<id>` - Delete entry

### Analytics Endpoints
- `GET /emotions/stats` - Get emotion statistics
- `GET /entries/wordcloud` - Get wordcloud data
- `GET /entries/negative` - Get negative sentiment analysis

## Security Notes

- All API endpoints require authentication except `/login` and `/register`
- User data is isolated - users can only access their own entries
- Passwords are hashed using bcrypt
- CORS is configured for secure cross-origin requests
- Environment variables are used for sensitive configuration

## Production Deployment

For production deployment:
1. Use HTTPS only
2. Set secure values for all environment variables
3. Configure proper CORS settings
4. Set up MongoDB authentication
5. Use a production-grade web server (e.g., Gunicorn)
6. Enable logging and monitoring
7. Set up regular database backups

## License

MIT License

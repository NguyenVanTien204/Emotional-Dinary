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

## Setup

1. **Clone the repository:**
   ```
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Install Python dependencies:**
   ```
   To start develop: cd backend\Setup.\setup_dev.ps1
   ```

3. **Start MongoDB:**  
   Ensure MongoDB is running locally on `mongodb://localhost:27017`.

4. **Create text index for search/insights:**
   ```
   use emotional_diary_db
   db.entries.createIndex({content: "text"})
   ```

5. **Run the Flask app:**
   ```
   python backend/main.py
   ```

6. **Open the app:**  
   Open `templates/index.html` or `templates/charts.html` in your browser.

## Folder Structure

```
backend/
  main.py
  utils.py
  analysis_static.py
templates/
  login.html
  index.html
  charts.html
static/
  css/
   charts.css
   style.css
  js/
   charts.js
   script.js
README.md


## Notes

- The app is for demo/educational purposes. For production, add HTTPS, environment variables, and security hardening.
- You can customize the list of negative keywords in `main.py` for your language/context.

## License

MIT License

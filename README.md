# FantasyRosterSubmission_db
# Fantasy Football Roster Submission App

A Flask-based web application that allows users to select and submit fantasy football rosters, save their selections in a SQLite database, and review or edit submissions. Built for a fantasy playoff challenge and deployed via AWS EC2 with Gunicorn and Nginx.

---

## 🚀 Features

- **User Input:** Collects user names, emails, and full roster submissions via web forms
- **Data Loading:** Reads cached NFL roster data from JSON files
- **Position Filtering:** Organizes players by QB, RB, WR/TE, and K
- **Form Handling:** Pre-fills forms for returning users
- **Database:** Stores submissions in SQLite, supports updates and exports
- **API Endpoint:** Exposes `/get-players` for JSON retrieval of player data
- **Excel Export:** Downloads all submissions as `.xlsx` for easy analysis
- **Logging:** Uses Python `logging` to track activity and debug issues
- **Deployment:** Runs continuously on AWS EC2 with Gunicorn + Nginx

---

## 🧱 Tech Stack

- **Backend:** Flask, Python 3
- **Frontend:** HTML + Jinja templates
- **Database:** SQLite3
- **Data Handling:** Pandas, JSON
- **Deployment:** AWS EC2, Gunicorn, Nginx

---

## 📂 File Structure (Partial)

```bash
.
├── app.py
├── submissions.db
├── templates/
│   ├── FFindex.html
│   ├── FFroster.html
│   └── show_submission.html
├── rosters_cache/
│   └── rosters*.json
├── submissions.xlsx
```

---

## 🔧 Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/fantasy-roster-app.git
   cd fantasy-roster-app
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Add cached roster files**
   Place JSON files into a `rosters_cache/` directory. Each should match a team like `rostersBUF_cache.json`.

4. **Run locally**
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000` to test locally.

5. **Deploy to EC2** (Linux)
   - Use `scp` or Git to transfer files to your EC2 instance
   - Run with Gunicorn:  
     ```bash
     gunicorn --bind 0.0.0.0:8000 app:app
     ```
   - Configure Nginx as a reverse proxy (map port 80 to 8000)
   - Use `systemd` to keep app running after logout

---

## 📦 Sample Commands

```bash
# Export to Excel
curl http://your-ec2-ip/export -o submissions.xlsx

# View all submissions
http://your-ec2-ip/submissions
```

---

## 📸 Screenshots
_Add screenshots of your app running, including form pages and roster tables._

---

## ✍ Author

**Jake Dick**  
[LinkedIn](https://www.linkedin.com/in/your-profile)  
[GitHub](https://github.com/your-username)

---

## 🏈 Notes
This was built as a custom web tool to streamline and store playoff fantasy football submissions. Feel free to fork and adapt for other fantasy formats.

---

## 📃 License
MIT

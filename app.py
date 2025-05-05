from flask import Flask, request, render_template, redirect, session, send_file, url_for, jsonify
from datetime import datetime
import pytz
import requests
import sqlite3
import pandas as pd
import json
import logging


# Set up logging to console at INFO level
logging.basicConfig(level=logging.INFO)


app = Flask(__name__)
app.secret_key = 'your_secret_key' # Required for session management

# Path to the cached file
cache_files = [
    "rosters_cache/rostersBUF_cache.json",
    "rosters_cache/rostersBAL_cache.json",
    "rosters_cache/rostersDET_cache.json",
    "rosters_cache/rostersGB_cache.json",
    "rosters_cache/rostersKC_cache.json",
    "rosters_cache/rostersLAC_cache.json",
    "rosters_cache/rostersLAR_cache.json",
    "rosters_cache/rostersMIN_cache.json",
    "rosters_cache/rostersPHI_cache.json",
    "rosters_cache/rostersDEN_cache.json",
    "rosters_cache/rostersHOU_cache.json",
    "rosters_cache/rostersPIT_cache.json",
    "rosters_cache/rostersTB_cache.json",
    "rosters_cache/rostersWSH_cache.json"
]

# Function to load cached data
def load_cached_data(cache_file):
    with open(cache_file, 'r') as f:
        return json.load(f)


@app.route('/get-players', methods=['GET'])
def get_players():
    players = {
        'qb': [],
        'rb': [],
        'wr': [],
        'te': [],
        'k': []
    }

    # Loop through each cache file and extract player data
    for cache_file in cache_files:
        data = load_cached_data(cache_file)
        body = data.get("body", {})
        team = body.get("team", "Unknown Team")
        team_logo = body.get("espnLogo1", "")  # Assuming this is the logo URL
        roster = body.get("roster", [])

        # Categorize players by position
        for player in roster:
            player_name = player.get("espnName", "Unknown Player")
            position = player.get("pos", "Unknown Position")

            # Categorize player based on position
            position = position.lower()
            player_data = {'Name': player_name, 'Team': team, 'Logo': team_logo}

            if 'qb' in position:
                players['qb'].append(player_data)
            elif 'rb' in position:
                players['rb'].append(player_data)
            elif 'wr' in position or 'te' in position:
                if not any(p['Name'] == player_name for p in players['wr']):
                    players['wr'].append(player_data)
            elif 'k' in position:
                players['k'].append(player_data)

    # Sort players alphabetically by last name
    for position in players:
        players[position] = sorted(players[position], key=lambda x: x['Name'].split()[-1])

    return jsonify(players)

from datetime import datetime
import pytz

# Define your local timezone (example: US Eastern Time)
local_tz = pytz.timezone('US/Central')  # Change this to your timezone

# Get the current time in UTC and convert it to local time
utc_now = datetime.now(pytz.utc)  # Get current UTC time
local_time = utc_now.astimezone(local_tz)  # Convert to local time
submission_time = local_time.strftime('%Y-%m-%d %H:%M:%S')  # Format as a string


# Now use `submission_time` when inserting data
# Database setup
def init_db():
    conn = sqlite3.connect('submissions.db')  # Create or open the database
    c = conn.cursor()

    # Check if the table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='submissions_2025';")
    table_exists = c.fetchone()

    if not table_exists:
        c.execute('''
            CREATE TABLE submissions_2025 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                qb TEXT NOT NULL,
                rb1 TEXT NOT NULL,
                rb2 TEXT NOT NULL,
                wr1 TEXT NOT NULL,
                wr2 TEXT NOT NULL,
                wr3 TEXT NOT NULL,
                flex TEXT NOT NULL,
                captain TEXT NOT NULL,
                k TEXT NOT NULL,
                submission_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logging.info("Created table submissions_2025")
    else:
        logging.info("Table submissions_2025 already exists")

    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Route for the name and email form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']

        # Check if the email already exists in the database
        conn = sqlite3.connect('submissions.db')
        c = conn.cursor()
        c.execute('SELECT * FROM submissions WHERE email = ?', (email,))
        existing_submission = c.fetchone()
        conn.close()

        if existing_submission:
            # Redirect to show_submission route
            app.logger.info(f"Existing submission found for email: {email}")
            return redirect(url_for('show_submission', submission_id=existing_submission[0]))
        else:
            # Store data in session and redirect to roster page
            session['first_name'] = request.form['firstName']
            session['last_name'] = request.form['lastName']
            session['email'] = request.form['email']
            app.logger.info(f"Session data: {session}")  # Log session data
            return redirect(url_for('roster'))

    return render_template('FFindex.html')


@app.route('/submission/<int:submission_id>', methods=['GET'])
def show_submission(submission_id):
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()

    # Fetch the submission with the specific ID
    c.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    submission = c.fetchone()

    conn.close()

    if submission:
        # Set session variables for use in the roster page
        session['first_name'] = submission[1]
        session['last_name'] = submission[2]
        session['email'] = submission[3]
        session['qb'] = submission[4]
        session['rb1'] = submission[5]
        session['rb2'] = submission[6]
        session['wr1'] = submission[7]
        session['wr2'] = submission[8]
        session['wr3'] = submission[9]
        session['flex'] = submission[10]
        session['captain'] = submission[11]
        session['k'] = submission[12]
        return render_template('show_submission.html', submission=submission)
    else:
        return "Submission not found", 404

# Route for the roster form
@app.route('/roster', methods=['GET', 'POST'])
def roster():
    # Get players data for all positions
    qb_players = get_players_by_position('qb')
    rb_players = get_players_by_position('rb')
    wr_players = get_players_by_position('wr')
    k_players = get_players_by_position('k')

    # Log the fetched player data with logos
    logging.info("Fetched QB Players with Logos:")
    for player in qb_players:
        logging.info(f"Player: {player['Name']}, Team: {player['Team']}, Logo: {player.get('Logo', 'No logo available')}")

    if request.method == 'POST':
        # Get the form data from the user
        qb = request.form['qb']
        rb1 = request.form['rb1']
        rb2 = request.form['rb2']
        wr1 = request.form['wr1']
        wr2 = request.form['wr2']
        wr3 = request.form['wr3']
        flex = request.form['flx']
        captain = request.form['cpt']
        k = request.form['k']

        # Get the email from the session
        email = session.get('email')

        # Check if the user is editing an existing submission (based on email)
        if email:
            # Log the update process
            logging.info(f"Updating submission for email: {email}")
            logging.info(f"New submission: QB: {qb}, RB1: {rb1}, RB2: {rb2}, WR1: {wr1}, WR2: {wr2}, WR3: {wr3}, FLX: {flx}, CPT: {cpt}, K: {k}")

            # Update the submission in the database with new data
            conn = sqlite3.connect('submissions.db')
            c = conn.cursor()
            c.execute('''
                UPDATE submissions
                SET qb = ?, rb1 = ?, rb2 = ?, wr1 = ?, wr2 = ?, wr3 = ?, flx = ?, cpt = ?, k = ?, submission_time = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k, email))
            conn.commit()
            conn.close()

            # Log the data after the update
            logging.info("Data after insertion:")
            c.execute('SELECT * FROM submissions WHERE email = ?', (email,))
            updated_submission = c.fetchone()
            logging.info(f"Updated submission: {updated_submission}")

            # Redirect to a thank-you page after updating
            return redirect('/thankyou')
        else:
            # If email is not found in the session, handle as a new submission
            return redirect(url_for('index'))

    # Check if the user is editing an existing submission
    email = session.get('email')
    if email:
        # Fetch the existing submission from the database
        conn = sqlite3.connect('submissions.db')
        c = conn.cursor()
        c.execute('''
            SELECT
              id,
              first_name,
              last_name,
              email,
              qb,
              rb1,
              rb2,
              wr1,
              wr2,
              wr3,
              flex,
              captain,
              k,
              submission_time
            FROM submissions
            WHERE email = ?
        ''', (email,))
        existing_submission = c.fetchone()
        conn.close()

        if existing_submission:
            # Log the existing submission details
            logging.info(f"Existing submission found for {email}: {existing_submission}")
            # Pre-fill the form with the existing submission data
            return render_template('FFroster.html',
                                   first_name=session.get('first_name'),
                                   last_name=session.get('last_name'),
                                   email=email,
                                   qb_players=qb_players,
                                   rb_players=rb_players,
                                   wr_players=wr_players,
                                   k_players=k_players,
                                   selected_qb=existing_submission[4],
                                   selected_rb1=existing_submission[5],
                                   selected_rb2=existing_submission[6],
                                   selected_wr1=existing_submission[7],
                                   selected_wr2=existing_submission[8],
                                   selected_wr3=existing_submission[9],
                                   selected_flx=existing_submission[10],
                                   selected_cpt=existing_submission[11],
                                   selected_k=existing_submission[12])

    return render_template('FFroster.html',
                           first_name=session.get('first_name'),
                           last_name=session.get('last_name'),
                           email=session.get('email'),
                           qb_players=qb_players,
                           rb_players=rb_players,
                           wr_players=wr_players,
                           k_players=k_players)


def get_players_by_position(position):
    players = []
    for cache_file in cache_files:
        data = load_cached_data(cache_file)
        body = data.get("body", {})
        roster = body.get("roster", [])

        for player in roster:
            player_name = player.get("espnName", "Unknown Player")
            player_position = player.get("pos", "Unknown Position")
            team = body.get("team", "Unknown Team")
            logo = player.get("Logo", "")  # Assuming the logo is part of the player data

            if position == 'qb' and 'qb' in player_position.lower():
                players.append({'Name': player_name, 'Team': team, 'Logo': logo})
            elif position == 'rb' and 'rb' in player_position.lower():
                players.append({'Name': player_name, 'Team': team, 'Logo': logo})
            elif position == 'wr' and ('wr' in player_position.lower() or 'te' in player_position.lower()):
                players.append({'Name': player_name, 'Team': team, 'Logo': logo})
            elif position == 'k' and 'k' in player_position.lower():
                players.append({'Name': player_name, 'Team': team, 'Logo': logo})

    # Log the player data to check if Logo is available
    for player in players:
        print(f"Player: {player['Name']}, Logo: {player.get('Logo', 'No logo available')}")

    # Sort players alphabetically by last name
    players = sorted(players, key=lambda x: x['Name'].split()[-1])
    return players

def add_submission_time_column():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()

    # Check if the submission_time column exists
    c.execute("PRAGMA table_info(submissions)")
    columns = [column[1] for column in c.fetchall()]

    if "submission_time" not in columns:
        # If the column doesn't exist, add it
        c.execute('''
            ALTER TABLE submissions ADD COLUMN submission_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ''')
        conn.commit()

    conn.close()



# Route to handle roster submission
# @app.route('/submit', methods=['POST'])
# def submit_roster():
#     # Get session data
#     first_name = session.get('first_name')
#     last_name = session.get('last_name')
#     email = session.get('email')
#
#     # Get form data from FFroster.html
#     qb = request.form['qb']
#     rb1 = request.form['rb1']
#     rb2 = request.form['rb2']
#     wr1 = request.form['wr1']
#     wr2 = request.form['wr2']
#     wr3 = request.form['wr3']
#     flex = request.form['flx']
#     captain = request.form['cpt']
#     k = request.form['k']
#
#     # Log the data that will be inserted into the database
#     logging.info(f"Inserting data: QB={qb}, RB1={rb1}, RB2={rb2}, WR1={wr1}, WR2={wr2}, WR3={wr3}, FLX={flex}, CPT={captain}, K={k}")
#
#     # Store data in the database
#     conn = sqlite3.connect('submissions.db')
#     c = conn.cursor()
#
#     # Debugging: Log the data before inserting
#     logging.info(f"Inserting data into database: first_name={first_name}, last_name={last_name}, email={email}, qb={qb}, rb1={rb1}, rb2={rb2}, wr1={wr1}, wr2={wr2}, wr3={wr3}, flex={flex}, captain={captain}, k={k}, submission_time={submission_time}")
#
#     # 2) Check if that email is already in the table
#     c.execute("SELECT id FROM submissions WHERE email = ?", (email,))
#     row = c.fetchone()
#
#     if row:
#         # 3) If row exists, do an UPDATE
#         c.execute('''
#               UPDATE submissions
#                  SET qb=?,
#                      rb1=?,
#                      rb2=?,
#                      wr1=?,
#                      wr2=?,
#                      wr3=?,
#                      flex=?,
#                      captain=?,
#                      k=?,
#                      submission_time=CURRENT_TIMESTAMP
#                WHERE email=?
#             ''', (qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k, email))
#         logging.info(f"Updated existing submission for {email}")
#     else:
#         # 4) If no row, do an INSERT
#         logging.info("Columns to insert: first_name, last_name, email, qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k")
#         logging.info(f"Values: {first_name}, {last_name}, {email}, {qb}, {rb1}, {rb2}, {wr1}, {wr2}, {wr3}, {flex}, {captain}, {k}")
#         c.execute('''
#                 INSERT INTO submissions
#                   (first_name, last_name, email, qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k)
#                 VALUES (?,?,?,?,?,?,?,?,?,?,?, ?)
#             ''', (first_name, last_name, email, qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k))
#         logging.info(f"Inserted new submission for {email}")
#
#     conn.commit()
#     conn.close()
#
#     return redirect('/thankyou')

@app.route('/submit', methods=['POST'])
def submit_roster():
    # Get session data
    first_name = session.get('first_name')
    last_name = session.get('last_name')
    email = session.get('email')

    # Validate session data
    if not first_name or not last_name or not email:
        logging.error("Missing session data: first_name, last_name, or email.")
        return redirect('/roster?error=missing_session_data')

    # Get form data from FFroster.html
    try:
        qb = request.form['qb']
        rb1 = request.form['rb1']
        rb2 = request.form['rb2']
        wr1 = request.form['wr1']
        wr2 = request.form['wr2']
        wr3 = request.form['wr3']
        flex = request.form['flx']
        captain = request.form['cpt']
        k = request.form['k']
    except KeyError as e:
        logging.error(f"Missing form field: {e}")
        return redirect('/roster?error=missing_form_field')

    # Log the data that will be inserted into the database
    logging.info(f"Inserting data: QB={qb}, RB1={rb1}, RB2={rb2}, WR1={wr1}, WR2={wr2}, WR3={wr3}, FLX={flex}, CPT={captain}, K={k}")

    # Store data in the database with retries to handle potential locks
    for attempt in range(3):  # Retry up to 3 times
        try:
            with sqlite3.connect('submissions.db') as conn:
                c = conn.cursor()

                # Check if the email already exists
                c.execute("SELECT id FROM submissions WHERE email = ?", (email,))
                row = c.fetchone()

                if row:
                    # Update existing record
                    c.execute('''
                        UPDATE submissions
                        SET qb=?, rb1=?, rb2=?, wr1=?, wr2=?, wr3=?, flex=?, captain=?, k=?, submission_time=CURRENT_TIMESTAMP
                        WHERE email=?
                    ''', (qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k, email))
                    logging.info(f"Updated existing submission for {email}")
                else:
                    # Insert new record
                    c.execute('''
                        INSERT INTO submissions
                        (first_name, last_name, email, qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k, submission_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (first_name, last_name, email, qb, rb1, rb2, wr1, wr2, wr3, flex, captain, k))
                    logging.info(f"Inserted new submission for {email}")

                conn.commit()
                break  # Break loop if successful

        except sqlite3.OperationalError as e:
            logging.warning(f"Database locked on attempt {attempt + 1}: {e}")
            time.sleep(1)  # Wait for 1 second before retrying
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return redirect('/roster?error=unexpected_error')
    else:
        logging.error("Failed to insert/update after multiple attempts due to database lock.")
        return redirect('/roster?error=database_locked')

    return redirect('/thankyou')

# Route to display a "thank you" page
@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')


# Route to display all submissions
@app.route('/submissions')
def show_submissions():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()

    # Fetch the data and order by submission_time (or any other field)
    c.execute('''
        SELECT
          id,
          first_name,
          last_name,
          email,
          qb,
          rb1,
          rb2,
          wr1,
          wr2,
          wr3,
          flex,
          captain,
          k,
          submission_time
        FROM submissions
        ORDER BY submission_time DESC
    ''')
    data = c.fetchall()
    conn.close()

    # Log the fetched data to ensure it's correct
    logging.info(f"Fetched submissions: {data}")

    return render_template('submissions.html', data=data)

@app.route('/clear_submissions', methods=['POST'])
def clear_submissions():
    # Clear all data from the submissions table
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()
    c.execute('DELETE FROM submissions')
    conn.commit()
    conn.close()
    return redirect('/submissions')  # Redirect to the submissions page after clearing



# Route to export data to Excel
@app.route('/export')
def export_data():
    conn = sqlite3.connect('submissions.db')
    query = "SELECT * FROM submissions"
    df = pd.read_sql_query(query, conn)
    conn.close()

    file_path = 'submissions.xlsx'
    df.to_excel(file_path, index=False, engine='openpyxl')
    return send_file(file_path, as_attachment=True)



@app.route("/debug_table")
def debug_table():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(submissions)")
    columns = c.fetchall()
    conn.close()
    logging.info(f"Table info for 'submissions': {columns}")
    return "Table schema logged successfully."

def drop_old_table():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()

    # Drop the old table
    c.execute('DROP TABLE IF EXISTS submissions')

    conn.commit()
    conn.close()
    print("Old table dropped successfully!")


def rename_new_table():
    conn = sqlite3.connect('submissions.db')
    c = conn.cursor()

    # Rename the new table
    c.execute('ALTER TABLE submissions_2025 RENAME TO submissions')

    conn.commit()
    conn.close()
    print("New table renamed successfully!")


@app.route('/migrate_tables')
def migrate_tables():
    drop_old_table()
    rename_new_table()
    return "Migration completed!"

if __name__ == '__main__':
    app.run(debug=True)
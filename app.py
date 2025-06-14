from flask import Flask, render_template, jsonify, request, send_from_directory, session

# from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
import string
import random
from countries import countries_by_continent
import os
import smtplib
from email.message import EmailMessage
import json
import threading
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, static_url_path="/static", static_folder="static")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
DATABASE_URL = "postgres://u5ls1quo381tm2:pf1e21f427f2706abdb37863a5382156f9f08bbb6cd676a61434b75e0890b61a0@c8lj070d5ubs83.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d5ngml0f45qdjh"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace(
    "postgres://", "postgresql://"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = os.environ.get("SECRET_KEY")

app.config["SESSION_TYPE"] = "filesystem"  # Use filesystem for session storage
Session(app)

# flags with errors: nepal, switzerland, israel, solomon islands

# solo, learn, race


def get_random_country(continent):

    # Initialize 'recent_countries' in session if not present
    if "recent_countries" not in session:
        session["recent_countries"] = []

    recent_countries = session["recent_countries"]

    countries = countries_by_continent.get(continent, countries_by_continent["all"])

    # Reset 'recent_countries' if all countries have been used
    if len(recent_countries) >= len(countries):
        recent_countries = []

    # Filter out recently used countries
    eligible_countries = [c for c in countries if c["name"] not in recent_countries]

    # If no eligible countries are left, reset 'recent_countries'
    if not eligible_countries:
        recent_countries = []
        eligible_countries = countries

    # Select a random country from eligible countries
    country = random.choice(eligible_countries)
    recent_countries.append(country["name"])

    # Update the session with the new 'recent_countries' list
    session["recent_countries"] = recent_countries

    return country


@app.route("/")
def game_start():
    return render_template("gameStart.html")


@app.route("/flag_guesser")
def flag_guesser():
    mode = request.args.get("mode", "solo")
    return render_template("flagGuesser.html", mode=mode, show_selection=True)


@app.route("/get_flag")
def get_flag():
    subgroup = request.args.get("continent", "")

    # Mapping of expected subgroups to actual keys in the dictionary
    subgroup_mapping = {
        "all": "all",
        "africa": "africa",
        "asia": "asia",
        "europe": "europe",
        "north_america": "north_america",
        "south_america": "south_america",
        "oceania": "oceania",
        "test": "test",
        "30_most_recognized": "30_most_recognized",
        "10_most_recognized": "10_most_recognized",
        "50_most_recognized": "50_most_recognized",
        "us_states": "us_states",
        "landlocked_countries": "landlocked_countries",
        "island_nations": "island_nations",
        "opec_members": "opec_members",
        "newest_countries": "newest_countries",
        "oldest_national_flags": "oldest_national_flags",
        "flags_with_unique_shapes": "flags_with_unique_shapes",
        "flags_with_animals": "flags_with_animals",
        "flags_with_stars": "flags_with_stars",
        "monarchies": "monarchies",
        "olympic_host_nations": "olympic_host_nations",
        "g20_countries": "g20_countries",
        "commonwealth_nations": "commonwealth_nations",
        "brics_countries": "brics_countries",
        "european_union": "european_union",
        "asean_countries": "asean_countries",
        "nordic_countries": "nordic_countries",
        "caribbean_nations": "caribbean_nations",
        "pacific_island_nations": "pacific_island_nations",
        "arab_league": "arab_league",
        "former_soviet_republics": "former_soviet_republics",
        "countries_with_tricolor_flags": "countries_with_tricolor_flags",
        "countries_with_crosses_on_their_flags": "countries_with_crosses_on_their_flags",
        "countries_with_crescent_moon_on_their_flags": "countries_with_crescent_moon_on_their_flags",
        "countries_with_union_jack_in_their_flags": "countries_with_union_jack_in_their_flags",
        "countries_with_suns_on_their_flags": "countries_with_suns_on_their_flags",
        "countries_that_drive_on_the_left": "countries_that_drive_on_the_left",
        "microstates": "microstates",
        "countries_with_vertical_stripes_on_their_flags": "countries_with_vertical_stripes_on_their_flags",
        "countries_with_horizontal_stripes_on_their_flags": "countries_with_horizontal_stripes_on_their_flags",
        "countries_with_unique_currency_symbols": "countries_with_unique_currency_symbols",
        "countries_with_only_one_bordering_country": "countries_with_only_one_bordering_country",
        "countries_with_coastlines_on_multiple_oceans": "countries_with_coastlines_on_multiple_oceans",
        "countries_with_red_primary_color": "countries_with_red_primary_color",
        "countries_with_green_primary_color": "countries_with_green_primary_color",
        "countries_with_white_primary_color": "countries_with_white_primary_color",
        "countries_with_blue_primary_color": "countries_with_blue_primary_color",
        "countries_with_yellow_primary_color": "countries_with_yellow_primary_color",
    }

    # Use the mapping, or default to the original subgroup
    actual_key = subgroup_mapping.get(subgroup, subgroup)

    if actual_key in countries_by_continent:
        country = get_random_country(actual_key)
        total_countries = len(countries_by_continent[actual_key])

        # Replace 'facts' with 'facts' from the 'all' section
        for country_in_all in countries_by_continent["all"]:
            if country_in_all["name"] == country["name"]:
                country["facts"] = country_in_all.get("facts", [])
                break

        return jsonify({**country, "total_countries": total_countries})
    else:
        return jsonify({"error": f"Invalid subgroup: {subgroup}"}), 400


@app.route("/get_suggestions")
def get_suggestions():
    query = request.args.get("query", "").lower()
    subgroup = request.args.get("continent", "all")
    if subgroup == "us_states":
        countries = countries_by_continent.get(subgroup)
    else:
        countries = countries_by_continent.get("all")
    suggestions = [
        country["name"]
        for country in countries
        if country["name"].lower().startswith(query)
    ]
    suggestions += [
        alias
        for country in countries
        for alias in country["aliases"]
        if alias.lower().startswith(query)
    ]
    return jsonify(list(set(suggestions)))


@app.route("/final_screen")
def final_screen():
    elapsed_time = request.args.get("time")
    continent = request.args.get("continent")
    learn = request.args.get("learn", "false").lower() == "true"
    return render_template(
        "finalScreen.html", time=elapsed_time, continent=continent, learn=learn
    )


@app.route("/reset")
def reset():
    session.pop("recent_countries", None)
    return jsonify({"message": "Reset successful"})


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename, cache_timeout=0)


@app.route("/submit_suggestion", methods=["POST"])
def submit_suggestion():
    data = request.get_json()
    suggestion = data.get("suggestion", "").strip()
    if suggestion:
        try:
            send_email(suggestion)
            print(f"New suggestion received: {suggestion}")
            return jsonify({"message": "Suggestion submitted successfully"}), 200
        except Exception as e:
            print(f"Error sending email: {e}")
            return jsonify({"error": "Failed to send suggestion via email"}), 500
    else:
        return jsonify({"error": "No suggestion provided"}), 400


def send_email(suggestion):
    # Fetch environment variables
    EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")
    RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")  # Your email address

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not RECEIVER_EMAIL:
        raise Exception("Email credentials are not fully set")

    msg = EmailMessage()
    msg["Subject"] = "New Suggestion Received"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(f"Suggestion:\n\n{suggestion}")

    # Connect to the SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    time_str = db.Column(db.String(20), nullable=False)
    time_ms = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<LeaderboardEntry {self.name} - {self.time_str}>"


def get_leaderboard_entries(category):
    return (
        LeaderboardEntry.query.filter_by(category=category)
        .order_by(LeaderboardEntry.time_ms)
        .limit(5)
        .all()
    )


def is_top5_score(category, time_ms):
    entries = get_leaderboard_entries(category)
    if len(entries) < 5:
        return True
    return time_ms < entries[-1].time_ms


def parse_time_to_ms(time_str):
    try:
        minutes, seconds, hundredths = time_str.split(":")
        total_ms = (
            (int(minutes) * 60000) + (int(seconds) * 1000) + (int(hundredths) * 10)
        )
        return total_ms
    except ValueError:
        return None


@app.route("/check_score", methods=["POST"])
def check_score():
    data = request.get_json()
    category = data.get("category")
    time_str = data.get("time")

    if not category or not time_str:
        return jsonify({"error": "Invalid data"}), 400

    time_ms = parse_time_to_ms(time_str)
    if time_ms is None:
        return jsonify({"error": "Invalid time format"}), 400

    is_top5 = is_top5_score(category, time_ms)

    return jsonify({"is_top5": is_top5})


@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.get_json()
    category = data.get("category")
    time_str = data.get("time")
    name = data.get("name")

    if not category or not time_str or not name:
        return jsonify({"error": "Invalid data"}), 400

    time_ms = parse_time_to_ms(time_str)
    if time_ms is None:
        return jsonify({"error": "Invalid time format"}), 400

    # Check if the score is a top 5 score
    if not is_top5_score(category, time_ms):
        return jsonify({"error": "Score is not in the top 5"}), 400

    # Add the new score
    new_entry = LeaderboardEntry(
        category=category, name=name, time_str=time_str, time_ms=time_ms
    )
    db.session.add(new_entry)
    db.session.commit()

    # Keep only the top 5 scores
    entries = get_leaderboard_entries(category)
    excess_entries = (
        LeaderboardEntry.query.filter_by(category=category)
        .order_by(LeaderboardEntry.time_ms.desc())
        .offset(5)
        .all()
    )
    for entry in excess_entries:
        db.session.delete(entry)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/get_leaderboard", methods=["GET"])
def get_leaderboard():
    category = request.args.get("category")
    if not category:
        return jsonify({"error": "Category not specified"}), 400

    entries = get_leaderboard_entries(category)
    leaderboard = [{"name": entry.name, "time": entry.time_str} for entry in entries]

    return jsonify({"leaderboard": leaderboard})


@app.route("/remove_duplicates", methods=["POST"])
def remove_duplicates():
    from sqlalchemy import func

    subquery = (
        db.session.query(
            LeaderboardEntry.category,
            LeaderboardEntry.name,
            LeaderboardEntry.time_str,
            func.min(LeaderboardEntry.id).label("min_id"),
        )
        .group_by(
            LeaderboardEntry.category, LeaderboardEntry.name, LeaderboardEntry.time_str
        )
        .subquery()
    )

    duplicates = LeaderboardEntry.query.join(
        subquery,
        (LeaderboardEntry.category == subquery.c.category)
        & (LeaderboardEntry.name == subquery.c.name)
        & (LeaderboardEntry.time_str == subquery.c.time_str)
        & (LeaderboardEntry.id != subquery.c.min_id),
    ).all()

    for entry in duplicates:
        db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": True, "removed": len(duplicates)})


# def generate_room_code():
#     return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# @app.route('/create_race')
# def create_race():
#     room_code = generate_room_code()
#     # Initialize race session in database or in-memory
#     return jsonify({"room_code": room_code})

# @app.route('/join_race/<room_code>')
# def join_race(room_code):
#     # Validate room code and join race
#     return render_template('race.html', room_code=room_code)

# @socketio.on('join')
# def on_join(data):
#     room = data['room']
#     join_room(room)
#     emit('player_joined', {'message': f'Player joined the race'}, room=room)

# @socketio.on('start_race')
# def on_start_race(data):
#     room = data['room']
#     # Initialize game state for the room
#     emit('race_started', {'message': 'Race started'}, room=room)

# @socketio.on('flag_guessed')
# def on_flag_guessed(data):
#     room = data['room']
#     # Update game state and check for race completion
#     emit('opponent_progress', {'progress': data['progress']}, room=room)

# @socketio.on('race_completed')
# def on_race_completed(data):
#     room = data['room']
#     # Record race results and notify players
#     emit('race_results', {'winner': data['winner'], 'time': data['time']}, room=room)


if __name__ == "__main__":
    app.run(debug=False)

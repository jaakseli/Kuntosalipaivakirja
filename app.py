import secrets
import sqlite3
from flask import Flask
from flask import abort, flash, redirect, render_template, request, session
import config, users, workouts, comments

app = Flask(__name__)
app.secret_key = config.secret_key

WORKOUT_CATEGORIES = [
    ("legs", "Jalat"),
    ("chest", "Rinta"),
    ("back", "Selka"),
    ("shoulders", "Hartiat"),
    ("arms", "Kasivarret"),
    ("core", "Keskivartalo"),
    ("full_body", "Koko kroppa"),
]

EXERCISE_CATEGORIES = [
    ("bench_press", "Bench press"),
    ("bicep_curl", "Bicep curl"),
    ("squat", "Squat"),
    ("deadlift", "Deadlift"),
    ("row", "Row"),
    ("overhead_press", "Overhead press"),
    ("pull_up", "Pull-up"),
    ("lunge", "Lunge"),
    ("leg_press", "Leg press"),
    ("other", "Other"),
]

WORKOUT_CATEGORY_LABELS = dict(WORKOUT_CATEGORIES)
EXERCISE_CATEGORY_LABELS = dict(EXERCISE_CATEGORIES)

def _get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token

def _validate_csrf():
    session_token = session.get("csrf_token")
    form_token = request.form.get("csrf_token")
    return bool(session_token and form_token and session_token == form_token)

@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _get_csrf_token()}

@app.route("/")
def index():
    all_workouts = workouts.get_all_workouts()
    return render_template(
        "index.html",
        workouts=all_workouts,
        query=None,
        workout_category_labels=WORKOUT_CATEGORY_LABELS,
    )

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect("/")

    results = workouts.search_workouts(query)
    return render_template(
        "index.html",
        workouts=results,
        query=query,
        workout_category_labels=WORKOUT_CATEGORY_LABELS,
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        if not _validate_csrf():
            abort(400)
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            flash("Salasanat eivät täsmää.")
            return redirect("/register")

        try:
            users.create_user(username, password1)
            flash("Tunnus luotu onnistuneesti. Kirjaudu sisään.")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Käyttäjänimi on jo varattu.")
            return redirect("/register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        if not _validate_csrf():
            abort(400)
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            return redirect("/")
        else:
            flash("Kirjautuminen epäonnistui.")
            return redirect("/login")

@app.route("/logout")
def logout():
    del session["user_id"]
    return redirect("/")

@app.route("/add_workout", methods=["GET", "POST"])
def add_workout():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "GET":
        exercise_count = request.args.get("exercise_count", default=1, type=int)
        return _render_add_workout(exercise_count)
    
    if request.method == "POST":
        if not _validate_csrf():
            abort(400)
        workout_name = request.form["workout_name"]
        category = request.form["category"]
        description = request.form["description"]
        user_id = session["user_id"]
        exercise_count = request.form.get("exercise_count", type=int)

        exercise_category_list = request.form.getlist("exercise_category")
        sets_list = request.form.getlist("sets")
        reps_list = request.form.getlist("reps")
        weight_list = request.form.getlist("weight")
        
        if not workout_name or len(workout_name.strip()) == 0:
            return _render_add_workout()

        exercises = _parse_exercises(
            exercise_count,
            exercise_category_list,
            sets_list,
            reps_list,
            weight_list,
        )
        if exercises is None:
            return _render_add_workout()

        workouts.add_workout(user_id, workout_name, category, description, exercises)
        flash("Treeni lisätty onnistuneesti.")
        return redirect("/")

@app.route("/workouts/<int:workout_id>/edit", methods=["GET", "POST"])
def edit_workout(workout_id):
    if "user_id" not in session:
        return redirect("/login")

    workout = workouts.get_workout(workout_id)
    if workout is None or workout["user_id"] != session["user_id"]:
        return redirect("/")

    if request.method == "GET":
        exercises = workouts.get_workout_exercises(workout_id)
        exercise_count = request.args.get("exercise_count", default=len(exercises), type=int)
        return render_template(
            "edit_workout.html",
            workout=workout,
            exercises=exercises,
            exercise_count=exercise_count,
            workout_categories=WORKOUT_CATEGORIES,
            exercise_categories=EXERCISE_CATEGORIES,
        )

    workout_name = request.form["workout_name"]
    if not _validate_csrf():
        abort(400)
    category = request.form["category"]
    description = request.form["description"]
    exercise_count = request.form.get("exercise_count", type=int)

    exercise_category_list = request.form.getlist("exercise_category")
    sets_list = request.form.getlist("sets")
    reps_list = request.form.getlist("reps")
    weight_list = request.form.getlist("weight")

    if not workout_name or len(workout_name.strip()) == 0:
        return redirect(f"/workouts/{workout_id}/edit")

    exercises = _parse_exercises(
        exercise_count,
        exercise_category_list,
        sets_list,
        reps_list,
        weight_list,
    )
    if exercises is None:
        return redirect(f"/workouts/{workout_id}/edit")

    workouts.update_workout(workout_id, session["user_id"], workout_name, category, description, exercises)
    flash("Treeni päivitetty onnistuneesti.")
    return redirect(f"/users/{session['user_id']}")

@app.route("/workouts/<int:workout_id>")
def workout_stats(workout_id):
    workout = workouts.get_workout_with_user(workout_id)
    if workout is None:
        return redirect("/")

    exercises = workouts.get_workout_exercises(workout_id)
    workout_comments = comments.get_workout_comments(workout_id)
    return render_template(
        "workout_stats.html",
        workout=workout,
        exercises=exercises,
        workout_comments=workout_comments,
        workout_category_labels=WORKOUT_CATEGORY_LABELS,
        exercise_category_labels=EXERCISE_CATEGORY_LABELS,
    )

@app.route("/workouts/<int:workout_id>/delete", methods=["POST"])
def delete_workout_route(workout_id):
    if "user_id" not in session:
        return redirect("/login")

    workout = workouts.get_workout(workout_id)
    if workout is None or workout["user_id"] != session["user_id"]:
        return redirect("/")

    if not _validate_csrf():
        abort(400)

    workouts.delete_workout(workout_id, session["user_id"])
    flash("Treeni poistettu onnistuneesti.")
    return redirect("/")

@app.route("/workouts/<int:workout_id>/comment", methods=["POST"])
def add_comment_route(workout_id):
    if "user_id" not in session:
        return redirect("/login")

    if not _validate_csrf():
        abort(400)

    workout = workouts.get_workout(workout_id)
    if workout is None:
        return redirect("/")

    comment_text = request.form.get("comment_text", "").strip()
    if not comment_text or len(comment_text) == 0:
        flash("Kommentti ei voi olla tyhjä.")
        return redirect(f"/workouts/{workout_id}")

    if len(comment_text) > 5000:
        flash("Kommentti on liian pitkä.")
        return redirect(f"/workouts/{workout_id}")

    comments.add_comment(workout_id, session["user_id"], comment_text)
    flash("Kommentti lisätty onnistuneesti.")
    return redirect(f"/workouts/{workout_id}")

@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
def delete_comment_route(comment_id):
    if "user_id" not in session:
        return redirect("/login")

    if not _validate_csrf():
        abort(400)

    comment = comments.get_comment(comment_id)
    if comment is None:
        return redirect("/")

    workout_id = comment["workout_id"]
    if comment["user_id"] != session["user_id"]:
        return redirect(f"/workouts/{workout_id}")

    comments.delete_comment(comment_id, session["user_id"])
    flash("Kommentti poistettu onnistuneesti.")
    return redirect(f"/workouts/{workout_id}")

@app.route("/users/<int:user_id>")
def user_stats(user_id):
    user = users.get_user(user_id)
    if user is None:
        return redirect("/")

    user_workouts = workouts.get_user_workouts(user_id)
    workouts_with_exercises = []
    for workout in user_workouts:
        exercises = workouts.get_workout_exercises(workout["id"])
        workouts_with_exercises.append({"workout": workout, "exercises": exercises})

    return render_template(
        "user_stats.html",
        user=user,
        workouts=workouts_with_exercises,
        workout_category_labels=WORKOUT_CATEGORY_LABELS,
        exercise_category_labels=EXERCISE_CATEGORY_LABELS,
    )

def _parse_exercises(exercise_count, categories, sets_list, reps_list, weight_list):
    if exercise_count is None or exercise_count <= 0:
        return None

    max_len = max(len(categories), len(sets_list), len(reps_list), len(weight_list))
    
    # Pad lists to same length with empty strings
    categories = categories + [''] * (max_len - len(categories))
    sets_list = sets_list + [''] * (max_len - len(sets_list))
    reps_list = reps_list + [''] * (max_len - len(reps_list))
    weight_list = weight_list + [''] * (max_len - len(weight_list))

    exercises = []
    for category, sets, reps, weight in zip(categories, sets_list, reps_list, weight_list):
        # Skip empty exercises
        if not category or not sets or not reps or not weight:
            continue
            
        try:
            sets_value = int(sets)
            reps_value = int(reps)
            weight_value = float(weight)
        except ValueError:
            continue

        if sets_value <= 0 or reps_value <= 0 or weight_value < 0:
            continue

        exercises.append(
            {
                "category": category,
                "sets": sets_value,
                "reps": reps_value,
                "weight": weight_value,
            }
        )

    # Must have at least one valid exercise
    if len(exercises) == 0:
        return None

    return exercises

def _render_add_workout(exercise_count=1):
    return render_template(
        "add_workout.html",
        workout_categories=WORKOUT_CATEGORIES,
        exercise_categories=EXERCISE_CATEGORIES,
        exercise_count=exercise_count,
    )
import sqlite3
from flask import Flask
from flask import flash, redirect, render_template, request, session
import config, users, workouts

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
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            flash("Salasanat eivat tasmää.")
            return redirect("/register")

        try:
            users.create_user(username, password1)
            flash("Tunnus luotu onnistuneesti. Kirjaudu sisaan.")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Kayttajanimi on jo varattu.")
            return redirect("/register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            return redirect("/")
        else:
            flash("Kirjautuminen epaonnistui.")
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
        return _render_add_workout()
    
    if request.method == "POST":
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
        flash("Treeni lisatty onnistuneesti.")
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
        return render_template(
            "edit_workout.html",
            workout=workout,
            exercises=exercises,
            workout_categories=WORKOUT_CATEGORIES,
            exercise_categories=EXERCISE_CATEGORIES,
        )

    workout_name = request.form["workout_name"]
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
    return redirect(f"/users/{session['user_id']}")

@app.route("/workouts/<int:workout_id>")
def workout_stats(workout_id):
    workout = workouts.get_workout_with_user(workout_id)
    if workout is None:
        return redirect("/")

    exercises = workouts.get_workout_exercises(workout_id)
    return render_template(
        "workout_stats.html",
        workout=workout,
        exercises=exercises,
        workout_category_labels=WORKOUT_CATEGORY_LABELS,
        exercise_category_labels=EXERCISE_CATEGORY_LABELS,
    )

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

    if not (
        len(categories)
        == len(sets_list)
        == len(reps_list)
        == len(weight_list)
        == exercise_count
    ):
        return None

    exercises = []
    for category, sets, reps, weight in zip(categories, sets_list, reps_list, weight_list):
        try:
            sets_value = int(sets)
            reps_value = int(reps)
            weight_value = float(weight)
        except ValueError:
            return None

        if sets_value <= 0 or reps_value <= 0 or weight_value < 0:
            return None

        exercises.append(
            {
                "category": category,
                "sets": sets_value,
                "reps": reps_value,
                "weight": weight_value,
            }
        )

    return exercises

def _render_add_workout():
    return render_template(
        "add_workout.html",
        workout_categories=WORKOUT_CATEGORIES,
        exercise_categories=EXERCISE_CATEGORIES,
    )
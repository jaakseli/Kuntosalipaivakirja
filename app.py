import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
import config, users, workouts

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")


#sovellus



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            return render_template("register_unsuccesful.html", message="salasanat eivät täsmää")

        try:
            users.create_user(username, password1)
            return render_template("register_succesful.html")
        except sqlite3.IntegrityError:
            return render_template("register_unsuccesful.html", message="käyttäjänimi on jo varattu")

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
            return render_template("login_unsuccesful.html")

@app.route("/logout")
def logout():
    del session["user_id"]
    return redirect("/")

@app.route("/add_workout", methods=["GET", "POST"])
def add_workout():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "GET":
        return render_template("add_workout.html")
    
    if request.method == "POST":
        workout_name = request.form["workout_name"]
        description = request.form["description"]
        user_id = session["user_id"]
        
        if not workout_name or len(workout_name.strip()) == 0:
            return render_template("add_workout.html")
        
        workouts.add_workout(user_id, workout_name, description)
        return render_template("workout_added.html")
import requests
from flask import Flask, redirect, render_template, request, flash, session
from cs50 import SQL
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from misc import login_required

#initializes flask app and database
app = Flask(__name__)
db = SQL("sqlite:///movies.db")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")##dashboard route after login
@login_required
def index():
    result = db.execute("SELECT * FROM movies ORDER BY seat ASC")
    return render_template("index.html",stateList = result)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add" , methods = ["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name")
        date = request.form.get("date")
        time = request.form.get("time")
        duration = request.form.get("duration")
        if not name or not date or not time or not duration:
            flash("You must fill all the fields.")
            return redirect("/add")
        db.execute("INSERT INTO movies(name, date, time, duration, seat) VALUES (?, ?, ?, ?, ?)",name,date,time,duration,25)
    return render_template("add_movies.html")

@app.route("/reserve", methods = ["GET","POST"])
@login_required
def reserve():
    if request.method == "POST":
        try:
            numberSeat = int(request.form.get("number"))
            movieID = request.form.get("id")
            vaccantSeat = db.execute("SELECT seat FROM movies WHERE id = ?",movieID)[0]['seat']
            if (vaccantSeat-numberSeat) >= 0:
                db.execute("UPDATE movies SET seat = ? WHERE id = ?",vaccantSeat-numberSeat,movieID)
                db.execute("INSERT INTO reservations(uid, mid, reserved) VALUES (?, ?, ?)",session["user_id"],movieID,numberSeat)
            else: 
                flash(f"You cannot reserve more than {vaccantSeat} seats.")
                return redirect("/reserve")
        except (ValueError, TypeError):
            flash("You must fill all the fields.")
            return redirect("/reserve")
    result = db.execute("SELECT * FROM movies")
    return render_template("reserve.html", options = result)

@app.route("/reservation")
@login_required
def reservations():
    reservationList = db.execute("SELECT movies.name, movies.date, movies.time, reservations.reserved FROM movies INNER JOIN reservations ON movies.id = reservations.mid WHERE reservations.uid = ?",session["user_id"])
    return render_template("reservation.html", lists = reservationList)

@app.route("/login", methods = ["GET","POST"])
def login():
    session.clear()
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            if username and password:
                search = db.execute("SELECT * FROM users WHERE username = ?", username)
                if check_password_hash(search[0]["password_hashed"],password):
                    session["user_id"] = search[0]["id"]
                    print(session["user_id"])
                    return redirect("/")
                else:
                    ##apology wrong pw
                    return redirect("/login")
            else:
                #apology fill all the fields
                return redirect("/login")
        except (IndexError, ValueError, TypeError):
            return redirect("/login") #apology Invalid username and password
    return render_template("login.html")
   

@app.route("/register", methods = ["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        check = db.execute("SELECT id FROM users WHERE username = ?", username)

        if len(check) == 0:
            if username and (password == confirmation) and password and confirmation:
                db.execute("INSERT INTO users(username, password_hashed) VALUES (?, ?)",username,generate_password_hash(password))
                return redirect("/")
            elif username and not password and not confirmation:
                return redirect("/")#must provide password
            else: 
                return redirect("/login") #fill all the fields
        else:
            ##username taken
            return redirect("/register")
        
    return render_template("register.html")


if __name__ == "__main__":
    app.run()


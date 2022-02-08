from flask import Flask, render_template, session, request, redirect, abort, jsonify,url_for
import os
import requests
import sqlite3
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'r3cjo2j42omjezo327'

GOOGLE_CLIENT_ID = '1068262751633-voa0vthskm2casevshg0b7damdplp0r5.apps.googleusercontent.com'#os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET ='LMHBWMBN9hiokfLkRRkBCXRa' #os.getenv("GOOGLE_CLIENT_SECRET")

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
c = conn.cursor()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
	return render_template("login.html")

@app.route('/login')
def login():
    if request.args.get("next"):
        session["next"] = request.args.get("next")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/userinfo.profile&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri=https://codefreeauth.pythonanywhere.com/login/callback&client_id={GOOGLE_CLIENT_ID}")

@app.route("/login/callback")
def google_authorized():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": request.args.get("code"),
        "grant_type": "authorization_code",
        "redirect_uri": "https://codefreeauth.pythonanywhere.com/login/callback"
    })
    print(r.json())
    r = requests.get(f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={r.json()["access_token"]}').json()

    user = c.execute("SELECT * FROM users WHERE user_id=:user_id", {"user_id": r["id"]}).fetchall()
    if len(user) != 0:
        session["user_id"] = user[0][0]
        session["name"] = user[0][1]
        session["avatar"] = user[0][2]
    else:
        c.execute("INSERT INTO users (user_id, name, photo) VALUES (:id, :name, :photo)", {"id": r["id"], "name": r["name"], "photo": r["picture"]})
        conn.commit()
        session["user_id"] = r["id"]
        session["name"] = r["name"]
        session["avatar"] = r["picture"]

    return redirect("/api")


@app.route("/api", methods = ['POST','GET'])
@login_required
def api():
    return render_template("form.html")

@app.route("/addrec", methods = ['POST','GET'])
@login_required
def addrec():
    if request.method == 'POST':
        sepal_len = request.form['sepal_len']
        sepal_wid = request.form['sepal_wid']
        petal_len = request.form['petal_len']
        petal_wid = request.form['petal_wid']
        Class = request.form['Class']
        c.execute("INSERT INTO iris (sepal_len,sepal_wid,petal_len,petal_wid,class) VALUES (?,?,?,?,?)",(sepal_len,sepal_wid,petal_len,petal_wid,Class))
        conn.commit()
        return 'Record Successfully Added!'
    else:
        return "Service is up!"


if __name__ == '__main__':
	app.run(debug= True)
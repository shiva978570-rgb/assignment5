import os
import pickle
import pandas as pd
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "thyroiddetect_secret"

BASE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────
model = None
MODEL_LOADED = False

try:
    with open(os.path.join(BASE, "thyroid_model.pkl"), "rb") as f:
        model = pickle.load(f)
    MODEL_LOADED = True
    print("Model Loaded Successfully")

except:
    print("Model not found → Demo mode running")

# ─────────────────────────────────────────
# HISTORY STORAGE
# ─────────────────────────────────────────
history_store = {}

def get_history():
    return history_store.get(session.get("username",""), [])

def get_stats():
    h = get_history()
    return {
        "total": len(h),
        "positive": sum(1 for i in h if i["result"]=="P"),
        "negative": sum(1 for i in h if i["result"]=="N"),
    }

# ─────────────────────────────────────────
# LOGIN CHECK
# ─────────────────────────────────────────
def is_logged_in():
    return "username" in session


# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
@app.route("/")
def index():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            session["username"] = username
            return redirect(url_for("dashboard"))

    return render_template("login.html")


# ─────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if not is_logged_in():
        return redirect(url_for("login"))

    result = None
    error = None

    if request.method == "POST":

        try:

            age = request.form.get("age")
            sex = request.form.get("sex")
            tsh = float(request.form.get("tsh"))

            # Demo prediction rule
            if tsh < 0.4 or tsh > 4.0:
                prediction = "P"
                label = "Positive — Thyroid Disease"
                rclass = "positive"
            else:
                prediction = "N"
                label = "Negative — No Thyroid Disease"
                rclass = "negative"

            result = {
                "label": label,
                "class": rclass,
                "confidence": 85
            }

            # Save history
            u = session["username"]
            history_store.setdefault(u,[])

            history_store[u].append({
                "age": age,
                "sex": sex,
                "tsh": tsh,
                "result": prediction,
                "confidence": 85,
                "date": date.today().strftime("%d %b %Y")
            })

        except Exception as ex:
            error = str(ex)

    return render_template(
        "dashboard.html",
        result=result,
        error=error,
        stats=get_stats(),
        form_data={},
        model_loaded=MODEL_LOADED
    )


# ─────────────────────────────────────────
# HISTORY
# ─────────────────────────────────────────
@app.route("/history")
def history():

    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template(
        "history.html",
        records=get_history()
    )


# ─────────────────────────────────────────
# DELETE RECORD
# ─────────────────────────────────────────
@app.route("/delete_record/<int:index>", methods=["POST"])
def delete_record(index):

    h = history_store.get(session["username"], [])

    if 0 <= index < len(h):
        h.pop(index)

    return redirect(url_for("history"))


# ─────────────────────────────────────────
# CLEAR HISTORY
# ─────────────────────────────────────────
@app.route("/clear_history", methods=["POST"])
def clear_history():

    history_store[session["username"]] = []
    return redirect(url_for("history"))


# ─────────────────────────────────────────
# ABOUT
# ─────────────────────────────────────────
@app.route("/about")
def about():

    return render_template("about.html")


# ─────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────
if __name__ == "__main__":

    print("Server Running → http://localhost:5000")
    app.run(debug=True)
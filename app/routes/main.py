from flask import Blueprint, render_template
from datetime import datetime

main = Blueprint("main", __name__, template_folder="../templates")

@main.route("/")
def index():
    return render_template("index.html", year=datetime.utcnow().year)

@main.route("/terms")
def terms():
    return render_template("terms.html", year=datetime.utcnow().year)

@main.route("/how-to-use")
def how_to_use():
    return render_template("howto.html", year=datetime.utcnow().year)

@main.route("/about")
def about():
    return render_template("about.html", year=datetime.utcnow().year)

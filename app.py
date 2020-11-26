import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/browse_books")
def browse_books():
    books = list(mongo.db.books.find())
    return render_template("books.html", books=books)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    books = list(mongo.db.books.find({"$text": {"$search": query}}))
    return render_template("books.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if user already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()}
        )
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("login"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("my_lists", username=session["user"]))
        
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if user already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for("my_lists", username=session["user"]))
            else:
                # invalid Username and/or password
                flash("incorrect Username and/or password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def my_lists(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("my_lists.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book = {
            "list_name": request.form.get("list_name"),
            "book_name": request.form.get("book_name"),
            "author": request.form.get("author"),
            "keywords": request.form.get("keywords"),
            "description": request.form.get("description"),
            "book_image": request.form.get("book_image"),
            "created_by": session["user"]
        }
        mongo.db.books.insert_one(book)
        flash("Book successfully added!")
        return redirect(url_for("browse_books"))

    lists = mongo.db.lists.find().sort("list_name", 1)
    return render_template("add_book.html", lists=lists)


@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if request.method == "POST":
        submit = {
            "list_name": request.form.get("list_name"),
            "book_name": request.form.get("book_name"),
            "author": request.form.get("author"),
            "keywords": request.form.get("keywords"),
            "description": request.form.get("description"),
            "book_image": request.form.get("book_image"),
            "created_by": session["user"]
        }
        mongo.db.books.update({"_id": ObjectId(book_id)}, submit)
        flash("Book successfully updated!")
        return redirect(url_for("browse_books"))

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    lists = mongo.db.lists.find().sort("list_name", 1)
    return render_template("edit_book.html", book=book, lists=lists)


@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    mongo.db.books.remove({"_id": ObjectId(book_id)})
    flash("Book successfully deleted!")
    return redirect(url_for("browse_books"))


@app.route("/get_lists")
def get_lists():
    lists = list(mongo.db.lists.find().sort("list_name", 1))
    return render_template("lists.html", lists=lists)


@app.route("/add_list", methods=["GET", "POST"])
def add_list():
    if request.method == "POST":
        list = {
            "list_name": request.form.get("list_name")
        }
        mongo.db.lists.insert_one(list)
        flash("New list added")
        return redirect(url_for("get_lists"))
    
    return render_template("add_list.html")


@app.route("/edit_list/<list_id>", methods=["GET", "POST"])
def edit_list(list_id):
    if request.method == "POST":
        submit = {
            "list_name": request.form.get("list_name")
        }
        mongo.db.lists.update({"_id": ObjectId(list_id)}, submit)
        flash("List successfully updated")
        return redirect(url_for("get_lists"))
    
    list = mongo.db.lists.find_one({"_id": ObjectId(list_id)})
    return render_template("edit_list.html", list=list)


@app.route("/delete_list/<list_id>")
def delete_list(list_id):
    mongo.db.lists.remove({"_id": ObjectId(list_id)})
    flash("List successfully deleted")
    return redirect(url_for("get_lists"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
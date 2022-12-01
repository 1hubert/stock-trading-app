import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    db_data = db.execute(
        "SELECT stock_symbol, SUM(nr_of_shares) FROM transactions WHERE user_id = ? GROUP BY stock_symbol", session["user_id"])

    total = 0
    portfolio_data = []
    for row in db_data:
        shares = row["SUM(nr_of_shares)"]
        if shares > 0:
            price = lookup(row["stock_symbol"])["price"]
            value = shares * price
            portfolio_data.append({"stock": row["stock_symbol"], "shares": shares, "price": price, "value": value})
            total += value

    cash = int(db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"])
    total += cash

    return render_template("index.html", portfolio_data=portfolio_data, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide stock symbol", 400)

        stock_info = lookup(symbol)

        if not stock_info:
            return apology("stock with given symbol does not exist", 400)

        if not shares:
            return apology("must provide stock symbol", 400)

        try:
            shares = int(shares)
        except (TypeError, ValueError):
            return apology("invalid number of shares", 400)

        if not shares >= 1:
            return apology("invalid number of shares", 400)

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        if stock_info["price"] * shares > cash[0]["cash"]:
            return apology("you cannot afford this number of shares at the current price", 400)

        db.execute("INSERT INTO transactions (user_id, stock_symbol, price, nr_of_shares, transaction_type) VALUES ( ?, ?, ?, ?, ?)",
                   session["user_id"], stock_info["symbol"], stock_info["price"], shares, "BUY")

        new_cash = cash[0]["cash"] - (stock_info["price"] * shares)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    table_data = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])

    return render_template("history.html", table_data=table_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must provide a stock symbol", 400)

        print(request.form.get("quote"))

        stock_info = lookup(request.form.get("symbol"))

        if not stock_info:
            return apology("stock not found", 400)

        name = stock_info["name"]
        price = stock_info["price"]
        symbol = stock_info["symbol"]

        return render_template("quoted.html", name=name, price=price, symbol=symbol)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username is new
        if len(rows) != 0:
            return apology("username already exists", 400)

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        if not confirmation:
            return apology("must provide password confirmation", 400)

        # Ensure passwords do match
        if password != confirmation:
            return apology("both passwords must match", 400)

        password_hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), password_hash)

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        available = db.execute(
            "SELECT SUM(nr_of_shares) FROM transactions WHERE user_id = ? AND stock_symbol = ?", session["user_id"], symbol)

        if not available:
            apology("you don't have any shares of selected stock")

        available = int(available[0]["SUM(nr_of_shares)"])

        if available < shares:
            return apology("You don't have enough stocks to sell")

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        price = lookup(symbol)["price"]

        db.execute("INSERT INTO transactions (user_id, stock_symbol, price, nr_of_shares, transaction_type) VALUES ( ?, ?, ?, ?, ?)",
                   session["user_id"], symbol, price, -(shares), "SELL")

        new_cash = cash + (price * shares)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        return redirect("/")

    else:
        stocks = db.execute(
            "SELECT stock_symbol FROM transactions WHERE user_id = ? GROUP BY stock_symbol HAVING SUM(nr_of_shares) > 0;", session["user_id"])
        return render_template("sell.html", stocks=stocks)

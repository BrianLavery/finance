import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import re

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)

# Configure CS50 Library to use SQLite database
db = SQL(os.getenv("DATABASE_URL"))

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")






@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Extract portfolio info from SQL database for user
    portfolio_list = db.execute("SELECT symbol, name, shares from portfolios WHERE userid = :userid", userid=session['user_id'])

    # Create a list that will put data into
    data = []

    # Create totals list to capture totals of amounts
    totals = []

    # Run through each dictionary from the SQL extract (each dict is one row)
    for i in range(len(portfolio_list)):
        tdata = []

        # Extract symbol, assign to variable as use later; append into list after capitalise
        symbol = portfolio_list[i]['symbol']
        tdata.append(symbol.upper())

        # Append name and shares into list
        tdata.append(portfolio_list[i]['name'])
        tdata.append(portfolio_list[i]['shares'])

        # Look up current price and append
        result = lookup(symbol)
        price = result['price']
        tdata.append(usd(price))

        # Append shares into list
        shares = portfolio_list[i]['shares']

        # Append value into list
        total = shares * price
        totalusd = usd(total)
        tdata.append(totalusd)
        data.append(tdata)

        # Add total into totals list
        totals.append(total)

    # Extract cash holdings for user
    cash_list = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
    cash = cash_list[0]['cash']
    cashusd = usd(cash)

    # Add cash into totals list
    totals.append(cash)

    # Create cash sub-list
    tdata = []
    tdata.append("Cash")
    tdata.append('')
    tdata.append('')
    tdata.append('')
    tdata.append(usd(cash))

    # Append cash sub-list into data list of lists
    data.append(tdata)

    # Calculate total
    subtotal = sum(totals)

    # Create totals sub-list
    tdata = []
    tdata.append('')
    tdata.append('')
    tdata.append('')
    tdata.append('')
    tdata.append(usd(subtotal))

    # Append totals sub-list into data list of lists
    data.append(tdata)

    # Render template and pass in headings and data lists
    headings = ["Symbol", "Name", "Shares", "Price", "Total"]
    return render_template("index.html", headings=headings, data=data)






@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check that symbol field has an entered value
        if not request.form.get("symbol"):
            return apology("must enter symbol", 403)

        # Ensure shares field has an entered value
        if not request.form.get("shares"):
            return apology("must enter a number of shares to purchase", 403)

        # Check symbol exists
        if not lookup(request.form.get("symbol")):
            return apology("invalid symbol", 403)

        # Check shares input is positive integer
        shares = int(request.form.get("shares"))
        if shares%1 != 0 or shares<0:
            return apology("must enter a positive whole number of shares", 403)

        # Check current share price: Extract value from form, lookup via API,
        symbol = request.form.get("symbol").upper()
        result = lookup(symbol)
        price = result['price']
        name = result['name']

        # Check user's cash balances
        rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
        cash = rows[0]["cash"]

        if cash < price * shares:
            return apology("you do not have sufficient funds to make this transaction", 403)

        # INSERT row into transactions recording the transaction details
        db.execute("INSERT INTO transactions (userid, symbol, shares, price) VALUES (:userid, :symbol, :shares, :price)",
                    userid=session["user_id"], symbol=symbol, shares=shares, price=price)

        # Check if this stock already exists in this portfolio for this user
        shares_old_list = db.execute("SELECT shares FROM portfolios WHERE userid = :user_id AND symbol = :symbol",
                                user_id = session["user_id"], symbol=symbol)
        if len(shares_old_list) == 0:
            db.execute("INSERT INTO portfolios (userid, symbol, name, shares) VALUES (:userid, :symbol, :name, :shares)",
                    userid=session["user_id"], symbol=symbol, name=name, shares=shares)
        else:
            shares_old = int(shares_old_list[0]['shares'])
            shares_new = shares_old + shares
            db.execute("UPDATE portfolios SET shares = :shares WHERE userid = :userid AND symbol = :symbol",
                        shares=shares_new, userid=session["user_id"], symbol=symbol)

        # UPDATE cash in users table
        cash_old_list = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
        cash_old = int(cash_old_list[0]['cash'])
        cash_new = cash_old - (shares * price)
        db.execute("UPDATE users SET cash = :cash WHERE id = :userid", cash=cash_new, userid=session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")







@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Extract portfolio info from SQL database for user
    transactions = db.execute("SELECT symbol, shares, price, timestamp from transactions WHERE userid = :userid", userid=session['user_id'])

    # Create a list that will put data into
    data = []

    # Run through each dictionary from the SQL extract (each dict is one list item)
    for i in range(len(transactions)):

        # Create a sublist each time to append data into
        tdata = []

        # Append symbol, shares, price, timestamp into this sub-list
        tdata.append(transactions[i]['symbol'])
        tdata.append(transactions[i]['shares'])
        tdata.append(usd(transactions[i]['price']))
        tdata.append(transactions[i]['timestamp'])

        # Append value into list
        data.append(tdata)

    # Render template and pass in headings and data lists
    headings = ["Symbol", "Shares", "Price", "Transacted"]
    return render_template("history.html", headings=headings, data=data)






@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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

    # Redirect user to home page
    return redirect("/")






@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get symbol
        symbol = request.form.get("symbol").upper()

        # Lookup symbol (returns dictionary with name, symbol, price)
        result = lookup(symbol)

        # Redirect to quoted template and pass in name, symbol, price (in USD)
        return render_template("quoted.html", name=result['name'], symbol=result['symbol'], price=usd(result['price']))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)

        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Define pw as variable
        pw = request.form.get("password")

        # Check password has required characters (uppercase, lowercase, special character & numeric value)
        # (1) ReGex to check if a string contains uppercase, lowercase special character & numeric value
        regex = ("^(?=.*[a-z])(?=." + "*[A-Z])(?=.*\\d)" + "(?=.*[-+_!@#$%^&*., ?]).+$")

        # (2) Compile the ReGex
        p = re.compile(regex)

        # (3) Print Yes if string matches ReGex
        if not (re.search(p, pw)):
            return apology("passwords must contain an uppercase letter, lowercase letter, special character & numeric value", 403)

        # Check if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if len(rows) == 1:
            return apology("username already exists", 403)

        # Create password hash
        username = request.form.get("username")
        pwhash = generate_password_hash(pw)

        # Insert user's details into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :pwhash)", username=username, pwhash=pwhash)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":

        # Extract symbols for stocks in user's portfolo
        symbol_dicts = db.execute("SELECT symbol FROM portfolios WHERE userid = :userid", userid = session["user_id"])

        # Extract values into list
        symbols = []
        for i in range(len(symbol_dicts)):
            symbols.append(symbol_dicts[i]['symbol'].upper())

        # Pass list into sell template to render
        return render_template("sell.html", symbols=symbols)

    # User reached route via POST (as by submitting a form via POST)
    else:
        if not request.form.get("symbol"):
            return apology("must enter symbol", 403)

        if not request.form.get("shares"):
            return apology("must enter number of shares to sell", 403)

        # Define selected stock and selected number of shares as variables
        selected_sym = request.form.get("symbol")
        selected_shares = int(request.form.get("shares"))

        # Extract symbols for stocks in user's portfolo
        shares_dicts = db.execute("SELECT shares FROM portfolios WHERE userid = :userid AND symbol = :symbol",
                                    userid = session["user_id"], symbol=selected_sym)

        # Check if no result for symbol; if so return apology
        if len(shares_dicts) == 0:
            return apology("you do not own any of these shares", 403)

        # Check shares value entered is a positive integer
        print(type(selected_shares))
        if selected_shares % 1 != 0 or selected_shares < 0:
            return apology("must enter a positive whole number of shares", 403)

        # Check if own less shares than amount requested to be sold
        existing_shares = int(shares_dicts[0]['shares'])
        if existing_shares < selected_shares:
            return apology("you do not have a sufficient number of these shares to complete this transaction", 403)

        # Extract price of transaction
        result = lookup(selected_sym)
        price = result['price']

        # Record the transaction in transactions database
        db.execute("INSERT INTO transactions (userid, symbol, shares, price) VALUES (:userid, :symbol, :shares, :price)",
                    userid=session["user_id"], symbol=selected_sym, shares=-selected_shares, price=price)

        # Update the number of shares in the portfolio database
        new_shares = existing_shares - selected_shares
        db.execute("UPDATE portfolios SET shares = :shares WHERE userid = :userid AND symbol = :symbol",
                    shares=new_shares, userid=session["user_id"], symbol=selected_sym)

        # Update cash position in users database
        cash_list = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
        cash_old = int(cash_list[0]['cash'])
        cash_new = cash_old + (selected_shares * price)
        db.execute("UPDATE users SET cash = :cash WHERE id = :userid", cash=cash_new, userid=session["user_id"])

        # Redirect user to home page
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)




from flask import Flask, render_template, session, redirect, request, flash, url_for
import requests
import json
import sys
import os
import datetime
sys.path.append('../Alexa')
from helpers import getAccounts, getAccountAndBalance, getCheckingBalance, getTotalBalance, getPurchases,getTotalforDOW, calculateSuggestedToday, getAllocations, addAllocation, updateAllocations
# import ../AlexaSkill/helpers.py

app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = os.urandom(12)

API_KEY = "638e3a40768577cc14440e93f78f7085"
BASE_NESSIE_URL = "http://api.reimaginebanking.com/"
customerID = "58000d58360f81f104543d82" #TODO: change this because this is zuck

def getResult():
    if not session.get('logged_in'):
        flash("Not logged in!")
        return redirect(url_for("login"))
    result = getAccountAndBalance(customerID)
    return result

def checkAuth():
    if not session.get('logged_in'):
        return False
    return True

def getMerchantName(merchantID):
    merchantURL = "http://api.reimaginebanking.com/merchants/%s?key=%s" %(merchantID, API_KEY)
    merchantName = json.loads(requests.get(merchantURL).text)["name"]
    return merchantName

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    else:
        ab = []
        result = getResult()
        for key in result:
            account = result[key]
            ab.append({"type": account[0], "balance": "${:,.2f}".format(account[1])})
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        return render_template("index.html")#, checkingTotal = "${:,.2f}".format(getCheckingBalance(customerID)),
        #totalBalance = "${:,.2f}".format(getTotalBalance(customerID)),
        #targetToday = "${:,.2s}".format(calculateSuggestedToday(customerID, datetime.datetime.now().weekday())))

@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST" and request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
        return redirect(url_for("home"))
    else:
        flash("Try again")
        return render_template("login.html")

@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect("/")

@app.route("/accounts")
def listAccounts():
    if checkAuth() == False:
        return redirect(url_for("login"))
    ab = []
    result = getResult()
    for key in result:
        account = result[key]
        ab.append({"type": account[0], "balance": "${:,.2f}".format(account[1])})
    #li = [{"type": "hi", "balance": 20}, {"type": "bi", "balance": 200}]
    return render_template("listAccounts.html", customers=ab,
        checkingTotal = "${:,.2f}".format(getCheckingBalance(customerID)),
        totalBalance = "${:,.2f}".format(getTotalBalance(customerID)))

@app.route("/purchases")
def purchases():
    if checkAuth() == False:
        return redirect(url_for("login"))
    d = []
    result = getPurchases(customerID)
    for key in result:
        purchase = result[key]
        d.append({"merchantID": purchase[3], "purchaseDate": purchase[1], "amount": "${:,.2f}".format(purchase[2])})
    d = sorted(d, key=lambda k: datetime.datetime.strptime(k['purchaseDate'],"%Y-%m-%d"), reverse=True)
    return render_template("purchases.html", purchases=d)

@app.route("/allocations", methods=["GET", "POST"])
def allocations():
    if request.method == "POST":
        addAllocation(customerID, request.form["category"], request.form["amount"], request.form["date"])
    updateAllocations(customerID)
    data = getAllocations(customerID)
    print(str(data))
    l = []
    total = 0
    for dat in data:
        l.append({"cat": dat[0], "amount": "${:,.2f}".format(dat[1]), "date": dat[3]})
        total += dat[1]
    l = sorted(l, key=lambda k: datetime.datetime.strftime(k['date'],"%Y-%m-%d"), reverse=True)
    print(l)
    return render_template("allocations.html", allocations=l, total="${:,.2f}".format(total))

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')

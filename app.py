from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os, json

app = Flask(__name__)
app.secret_key = "yejeyje4h5trn41dty4mnj8dt"  # Change this to a secure random key

# JobAdder API credentials
CLIENT_ID = "vdcmxl3ipmyupaybeylbr2ojiy"
CLIENT_SECRET = "t3tl43dm573ufmtf3h3bnbdl4qtmpluiby26xehba4irdvdtjqnm"
REDIRECT_URI = "https://chatbot.rd1.co.uk/callback"  # Change this if deployed

# JobAdder endpoints
AUTH_URL = "https://id.jobadder.com/connect/authorize"
TOKEN_URL = "https://id.jobadder.com/connect/token"
API_BASE_URL = "https://api.jobadder.com/v2"

# Scopes needed (adjust based on needs)
SCOPES = "read write read_job offline_access"


@app.route("/")
def home():
    """Home page with login link"""
    return render_template("home.html")

@app.route("/privacy")
def privacy():
    """Home page with login link"""
    return render_template("privacy.html")

@app.route("/login")
def login():
    """Redirect user to JobAdder OAuth login"""
    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "random_state_string",
    }
    auth_redirect_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    return redirect(auth_redirect_url)


@app.route("/callback")
def callback():
    """Handle OAuth callback and exchange code for access token"""
    if "error" in request.args:
        return f"Error: {request.args['error']}"

    if "code" not in request.args:
        return "No code received from JobAdder"

    auth_code = request.args["code"]

    # Exchange authorization code for access token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f2d1f83ef979f2ef23b7b30cc53ed3c7"
    }
    # f2d1f83ef979f2ef23b7b30cc53ed3c7

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)

    if response.status_code == 200:
        tokens = response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens.get("refresh_token", "")

        return redirect(url_for("get_jobs"))
    else:
        return f"Failed to get access token: {response.json()}"

@app.route("/jobs")
def get_jobs():
    """Fetch live jobs from JobAdder API"""
    if "access_token" not in session:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(f"{API_BASE_URL}/jobs?Active=true", headers=headers)

    if response.status_code == 200:
        jobs = response.json()
        return render_template("jobs.html", jobs=jobs)
    else:
        return f"Failed to fetch jobs: {response.json()}"

@app.route("/logout")
def logout():
    """Clear session"""
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=8000)

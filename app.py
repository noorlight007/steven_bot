from flask import Flask, redirect, request, session, url_for, render_template
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()

import requests
import os, json
from db_users import create_new_contact, add_thread_id
from gpt_functions import *

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

account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
phone_number = os.getenv('PHONE_NUMBER')
messaging_sid = os.getenv('MESSAGING_SID')
twilio_client = Client(account_sid, auth_token)

openAI_key = os.getenv('OPENAI_API')

ASSISTANT_ID = "asst_jGpzZ6calAdRADZYePwBer89"

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

        headers = {"Authorization": f"Bearer {session['access_token']}"}
        live_jobs = requests.get(f"{API_BASE_URL}/jobads?status=current&offset=0&limit=50", headers=headers)
        items = live_jobs.json().get("items", [])
        if live_jobs.status_code == 200:
            with open("live_jobs.json", "w+") as file:
                json.dump(live_jobs.json(), file, indent=4)

            for item in items:
                try:
                    ad_id = item.get("adId")
                    state = item.get("state")
                    title = item.get("title")
                    job_details_req = requests.get(f"{API_BASE_URL}/jobads/{ad_id}", headers=headers)
                    print(job_details_req.status_code)
                    # job_details = job_details_req.json()
                    # with open(f"job_files/{title.replace("/", "")}_{ad_id}_{state}.json", "w") as file:
                    #     json.dump(job_details, file, indent=4)
                except Exception as e:
                    print(job_details_req.status_code)
                    print(str(e))
                    
                try:
                    applications_req = requests.get(f"{API_BASE_URL}/jobads/591198/applications", headers=headers)
                    application_items = applications_req.json().get("items", [])
                    applications = applications_req.json()
                    with open(f"applications.json", "w") as file:
                        json.dump(applications, file, indent=4)
                except Exception as e:
                    print(applications_req.status_code)
                    print(str(e))
                print(f"Working on , {title}")
            return {"status": "success"}
        else:
            return {"status": "failed"}
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


@app.route("/whatsapp", methods=["POST", "GET"])
def whatsapp():
    """Handle incoming WhatsApp messages"""
    message = request.form.get('Body')
    sender = request.form.get('From')
    profile_name = request.form.get('ProfileName')
    media_url = request.form.get('MediaUrl0')

    print(f"Message = {message}")
    print(f'Message sent by {profile_name}, phone: {sender[10:]}')

    # Managing user session
    if "user" not in session:
        user = create_new_contact(profile_name, sender[9:])
        session["user"] = {"id": user.id, "whatsapp": user.whatsapp, "profile_name": user.profile_name, "thread_id": user.thread_id}

    if media_url:
        twilio_client.messages.create(
            from_= phone_number,
            to= sender,
            body="Currently, we only support text messages. Please send text only."
        )
        return "Message sent successfully"
    from openai import OpenAI
    openai_client = OpenAI(api_key=openAI_key)

    if session["user"]["thread_id"]:  # If user has an existing thread
        sendNewMessage_to_existing_thread(session["user"]["thread_id"], message)

    else:   # If user does not have an existing thread
        my_thread_id = initiate_interaction(message)
        add_thread_id(session["user"]["thread_id"], my_thread_id)

    run = trigger_assistant(session["user"]["thread_id"], ASSISTANT_ID)
    
    while True:
        run_status = checkRunStatus(session["user"]["thread_id"] , run.id)
        print(f"Run status: {run_status.status}")
        queue_time = 1
        if run_status.status == "failed":
            final_response = "Sorry I am having issues generating responses for queries now. Please wait for me to fix it."
            run_status.status = "completed"
            continue
            
        elif run_status.status == "queued":
            if queue_time == 15:
                final_response = "Sorry I am having issues generating responses for queries now. Please wait for me to fix it."
                continue
            queue_time+= 1
            
        elif run_status.status == "requires_action":
            print("hello")
            # List to store all the call ids
            tools_outputs = []
            print(run_status.required_action.submit_tool_outputs)
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:  # Getting all the tool calls
                # The returned parameter value of gpt functions
                arguments = json.loads(tool_call.function.arguments)
                print(f"Function: {tool_call.function.name}\nArgument variables: {arguments}")

                arguments = json.loads(tool_call.function.arguments)

                if tool_call.function.name == "get_job_id":
                    from utils import get_job_details
                    try:
                        job_id = arguments['job_id']
                        application_id = arguments['application_id']

                        job_details_result = get_job_details(job_id, application_id)
                        if job_details_result["success"]:  # If job details are found
                            tool_output={
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"success":True,"job_details":job_details_result["job_details"]}),
                            }
                        else:  # If job details are not found
                            tool_output={
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"success":False,"reason":job_details_result["reason"]}),
                            }
                        tools_outputs.append(tool_output)
                    except Exception as e:
                        print(str(e))
                        tool_output={
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": True}),  # If there is an error
                        }

                        tools_outputs.append(tool_output)
                
                if tool_call.function.name == "review_applicant":
                    try:
                        application_id = arguments['application_id']
                        review_status = arguments['review_status']
                        from utils import update_application_status

                        update_status = update_application_status(application_id, review_status)
                        if update_status['success']:  # If the review status is updated
                            tool_output={
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"success":True}),
                            }
                        else:  # If the review status is not updated
                            tool_output={
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"success":False}),
                            }
                        tools_outputs.append(tool_output)
                    except Exception as e:
                        print(str(e))
                        tool_output={
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": True}),
                        }
                        tools_outputs.append(tool_output)
                
            run = openai_client.beta.threads.runs.submit_tool_outputs(
                thread_id=session["user"]["thread_id"],
                run_id=run.id,
                tool_outputs=tools_outputs
            )

            
        if run_status.status == "completed":
            # Extract the bot's response
            final_response = retrieveResponse(session["user"]["thread_id"])
            print(final_response)
            break

        time.sleep(1)

    print(final_response)


    

    



if __name__ == "__main__":
    app.run(debug=True, port=8000)

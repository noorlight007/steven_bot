from flask import Flask, redirect, request, session, url_for, render_template, jsonify
from flask_session import Session
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()
import time

import requests
import os, json
from db_users import create_new_contact, add_thread_id
from gpt_functions import *

app = Flask(__name__)
app.secret_key = "yejeyje4h5trn41dty4mnj8dt"  # Change this to a secure random key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# JobAdder API credentials
CLIENT_ID = "vdcmxl3ipmyupaybeylbr2ojiy"
CLIENT_SECRET = "t3tl43dm573ufmtf3h3bnbdl4qtmpluiby26xehba4irdvdtjqnm"
REDIRECT_URI = "https://chatbot.rd1.co.uk/callback"  # Change this if deployed

# JobAdder endpoints
AUTH_URL = "https://id.jobadder.com/connect/authorize"
TOKEN_URL = "https://id.jobadder.com/connect/token"
API_BASE_URL = "https://api.jobadder.com/v2"

# Scopes needed (adjust based on needs)
SCOPES ="read write read_company read_jobad write_jobad read_jobapplication write_jobapplication read_jobapplication_note write_jobapplication_note manage_jobapplication_custom read_job write_job read_job_note write_job_note manage_job_custom read_note write_note offline_access"

account_sid = os.getenv('ACCOUNT_SID')
auth_token = os.getenv('AUTH_TOKEN')
phone_number = os.getenv('PHONE_NUMBER')
messaging_sid = os.getenv('MESSAGING_SID')
twilio_client = Client(account_sid, auth_token)

openAI_key = os.getenv('OPENAI_API')
ASSISTANT_ID = "asst_T4S4FvYXXriP6rXiJNfoS32w"
# ASSISTANT_ID = "asst_9VCIfBw1dOKNVuP6fQFXunQA"

@app.route("/")
def home():
    # data = {
    #     "job_id": "591198",
    #     "application_id": "8762438"
    # }
    # response = requests.post("https://chatbot.rd1.co.uk/get_job_details", json=data)
    # print(response.json())
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

@app.route("/get_job_details", methods=["GET"])
def get_job_details_al():
    # Parse JSON request data
    # data = request.get_json()
    
    # if not data or "job_id" not in data or "application_id" not in data:
    #     return jsonify({"success": False, "reason": "Missing job_id or application_id"}), 400

    # job_ad_id = data["job_id"]
    # application_id = data["application_id"]
    """Handle OAuth callback and exchange code for access token"""

    job_id = request.args["job_id"]
    application_id = request.args["application_id"]

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f52fb704a18729131bc1e4aace77d73e",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    # Write JSON to a file with 4-space indentation
    
    if response.status_code == 200:
        tokens = response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens.get("refresh_token", "")

    # Exchange authorization code for access token
    # token_data = {
    #     "client_id": CLIENT_ID,
    #     "client_secret": CLIENT_SECRET,
    #     "grant_type": "refresh_token",
    #     "refresh_token": "f52fb704a18729131bc1e4aace77d73e"
    # }
    # f2d1f83ef979f2ef23b7b30cc53ed3c7

    # headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    # print(response.json())

    # if response.status_code == 200:
        headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
        try:
            # tokens = response.json()
            job_details_req = requests.get(f"{API_BASE_URL}/jobads/{job_id}", headers=headers)
            print(job_details_req.json())
            if job_details_req.status_code != 200:  # If job not found
                return jsonify({"success": False, "reason": "Job_not_found"})
        except Exception as e:
            return jsonify({"success": False, "reason": str(e)})
        
        try:
            application_details = requests.get(f"{API_BASE_URL}/applications/{application_id}", headers=headers)
            if application_details.status_code != 200:
                return jsonify({"success": False, "reason": "application_not_found"})
        except Exception as e:
            return jsonify({"success": False, "reason": str(e)})
        
        job_title = job_details_req.json()['title']
        summary = job_details_req.json()['summary']
        bulletPoints_list = job_details_req.json()['bulletPoints']
        bulletPoints = []
        for bulletPoint in bulletPoints_list:
            bulletPoint_ex = bulletPoint
            bulletPoints.append(bulletPoint_ex)
        description = job_details_req.json()['description']
        company_name = job_details_req.json()['company']['name']
        current_application_status = application_details.json()['status']['name']  # CHAT GPT Contacted - No Reply
        owner_name = job_details_req.json()['owner']['firstName'] + " " + job_details_req.json()['owner']['lastName']
        
        try:
            owner_position = job_details_req.json()['owner']['position']
        except:
            owner_position = "Unknown"
        job_location = job_details_req.json()['job']['location']['name']

        job_details = {
            "job title": job_title,
            "summary": summary,
            "bulletPoints": bulletPoints,
            "description": description,
            "company name": company_name,
            "job location name": job_location,
            "current application status": current_application_status,
            "owner name": owner_name,
            "owner position": owner_position
        }

        return jsonify({"success": True, "job_details": job_details})
    
    return jsonify({"success": False, "reason": "not doing shit"})

@app.route("/get_applications_jobID", methods=["GET"])
def get_applications_of_job_id():

    """Handle OAuth callback and exchange code for access token"""
    job_ad_id = request.args["job_id"]

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f52fb704a18729131bc1e4aace77d73e",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    # Write JSON to a file with 4-space indentation
    
    if response.status_code == 200:
        tokens = response.json()

    # if response.status_code == 200:
        headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
        try:
            applications = requests.get(f"{API_BASE_URL}/jobads/{job_ad_id}/applications/active", headers=headers)
            # tokens = response.json()
            # job_details_req = requests.get(f"{API_BASE_URL}/jobads/{job_id}", headers=headers)
            # print(job_details_req.json())
            if applications.status_code != 200:  # If job not found
                return jsonify({"success": False, "reason": "applications_not_found"})
            else:
                return jsonify ({"success": True, "applications": applications.json()})
        except Exception as e:
            return jsonify({"success": False, "reason": str(e)})
    
    return jsonify({"success": False, "reason": "not doing shit"})



@app.route("/update_application_status", methods=["GET"])
def update_apps():

    """Handle OAuth callback and exchange code for access token"""
    applicantion_id = request.args["application_id"]
    new_status = request.args["new_status"]
    status_dict = {"sent_waiting": 27789,"unsuccessful": 2107, "successful": 13251, "not interested": 13250}

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f52fb704a18729131bc1e4aace77d73e",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    # Write JSON to a file with 4-space indentation
    
    if response.status_code == 200:
        tokens = response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens.get("refresh_token", "")

    # if response.status_code == 200:
        headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
        try:
            data = {
                "statusId": status_dict[new_status],  # Replace with the new status ID
            }
            data_changes = requests.put(f"{API_BASE_URL}/applications/{applicantion_id}", json=data, headers=headers)

            if data_changes.status_code != 200:  # If job not found
                return jsonify({"success": False, "reason": "application_not_found"})
            else:
                return jsonify ({"success": True})
        except Exception as e:
            return jsonify({"success": False, "reason": str(e)})
    
    return jsonify({"success": False, "reason": "not doing shit"})


@app.route("/callback")
def callback():

    # job_id = request.args["job_id"]
    # auth_code = request.args["code"]

    """Handle OAuth callback and exchange code for access token"""

    # Exchange authorization code for access token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f52fb704a18729131bc1e4aace77d73e"
    }

    # token_data = {
    #     "client_id": CLIENT_ID,
    #     "client_secret": CLIENT_SECRET,
    #     "grant_type": "authorization_code",
    #     "code": auth_code,
    #     "redirect_uri": REDIRECT_URI
    # }
    # f2d1f83ef979f2ef23b7b30cc53ed3c7

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)

    if response.status_code == 200:
        tokens = response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens.get("refresh_token", "")
        # Save JSON response to a file
        # with open("token_response.json", "w") as json_file:
        #     json.dump(tokens, json_file, indent=4)
        # return jsonify({"success": "all okay"})
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(TOKEN_URL, data=token_data, headers=headers)
        print(response.json())

        if response.status_code == 200:
            
            headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
            try:
                job_details_req = requests.get(f"{API_BASE_URL}/jobads/591117/applications?offset=0&limit=50", headers=headers)
                print(job_details_req.json())
                
                if job_details_req.status_code != 200:  # If job not found
                    return jsonify({"success": False, "reason": "Job_not_found"})
                with open("new_job.json", "w") as json_file:
                    json.dump(job_details_req.json(), json_file, indent=4)
            except Exception as e:
                return jsonify({"success": False, "reason": str(e)})
    else:
        return jsonify({"success": False, "reason": "problem"})

@app.route("/get_live_jobs")
def get_live_jobs():
    """Handle OAuth callback and exchange code for access token"""

    # Exchange authorization code for access token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": "f52fb704a18729131bc1e4aace77d73e"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=token_data, headers=headers)

    if response.status_code == 200:
        tokens = response.json()

        headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
        ## First getting live job ads
        try:
            live_jobs = requests.get(f"{API_BASE_URL}/jobads?status=current&offset=0&limit=50", headers=headers)
            return jsonify({"success": True,"live_jobs": live_jobs.json()})
        except Exception as e:
            return jsonify({"success": False, "reason": str(e)})
    else:
        return jsonify({"success": False, "reason": "problem"})


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
        try:
            sendNewMessage_to_existing_thread(session["user"]["thread_id"], message)
        except Exception as e:
            deleteRun(session["user"]["thread_id"])
            sendNewMessage_to_existing_thread(session["user"]["thread_id"], message)

    else:   # If user does not have an existing thread
        my_thread_id = initiate_interaction(message)
        session["user"]["thread_id"] = my_thread_id
        add_thread_id(session["user"]["whatsapp"], my_thread_id)

    run = trigger_assistant(session["user"]["thread_id"], ASSISTANT_ID)
    # session['run_id'] = run.id
    flag_message = False
    queue_time = 1

    while True:
        run_status = checkRunStatus(session["user"]["thread_id"] , run.id)
        print(f"Run status: {run_status.status}")
        if run_status.status == "failed":
            final_response = "Sorry I am having issues generating responses for queries now. Please wait for me to fix it."
            # deleteRun(session["user"]["thread_id"])
            break
            
        elif run_status.status == "queued":
            if queue_time == 15:
                final_response = "Sorry I am having issues generating responses for queries now. Can you send the previous message again please."
                deleteRun(session["user"]["thread_id"])
                run = trigger_assistant(session["user"]["thread_id"], ASSISTANT_ID)
                queue_time = 1
                break
            queue_time+= 1

        elif run_status.status == "cancelled":
            queue_time = 1
            final_response = "Sorry I am having issues generating responses for queries now. Can you send the previous message again please."
            deleteRun(session["user"]["thread_id"])
            run = trigger_assistant(session["user"]["thread_id"], ASSISTANT_ID)
            # session['run_id'] = run.id
            break
        elif run_status.status == "requires_action":
            queue_time = 1
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

                            flag_message = True
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
            queue_time = 1
            # Extract the bot's response
            final_response = retrieveResponse(session["user"]["thread_id"])
            print(final_response)
            break

        time.sleep(1)
    
    print(final_response)
    twilio_client.messages.create(
        from_= phone_number,
        to= sender,
        body=final_response
    )
    return "Message sent successfully"


if __name__ == "__main__":
    app.run(debug=True, port=8000)

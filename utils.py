import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()
from gpt_functions import *
import time

# JobAdder API credentials
CLIENT_ID = os.getenv('JOBADDER_CLIENT_ID')
CLIENT_SECRET = os.getenv('JOBADDER_CLIENT_SECRET')

TOKEN_URL = "https://id.jobadder.com/connect/token"
API_BASE_URL = "https://api.jobadder.com/v2"

def get_job_details(job_ad_id, applicantion_id):
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
        try:
            job_details_req = requests.get(f"{API_BASE_URL}/jobads/{job_ad_id}", headers=headers)
            if job_details_req.status_code != 200:  # If job not found
                return {"success": False, "reason": "Job_not_found"}
        except:
            return {"success": False, "reason": "Job_not_found"}
        
        try:
            application_details = requests.get(f"{API_BASE_URL}/applications/{applicantion_id}", headers=headers)
            if application_details.status_code != 200:
                return {"success": False, "reason": "application_not_found"}
        except:
            return {"success": False, "reason": "application_not_found"}
        
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
        owner_position = job_details_req.json()['owner']['position']

        job_details = {
            "job title": job_title,
            "summary": summary,
            "bulletPoints": bulletPoints,
            "description": description,
            "company name": company_name,
            "current application status": current_application_status,
            "owner name": owner_name,
            "owner position": owner_position
        }

        return {"success": True, "job_details": job_details}
    
    return {"success": False, "reason": "system_error"}
    

def update_application_status(applicantion_id, new_status):
    ## Status dictionary
    status_dict = {"unsuccessful": 2107, "successful": 13251, "not interested": 13250}
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
        try:
            data = {
                "statusId": status_dict[new_status],  # Replace with the new status ID
            }
            data_changes = requests.put(f"{API_BASE_URL}/applications/{applicantion_id}/status", json=data, headers=headers)
            if data_changes.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "reason": "status_not_updated"}
        except:
            return {"success": False, "reason": "application_not_found"}  # If application not found
        
    return {"success": False, "reason": "system_error"}



def send_twilio_message():
    from twilio.rest import Client

    account_sid = os.getenv('ACCOUNT_SID')
    auth_token = os.getenv('AUTH_TOKEN')
    messaging_service_sid = os.getenv('MESSAGING_SID')
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        messaging_service_sid=messaging_service_sid,
        content_sid='HX447ca33fbd74315dcd4b377b98536aa1',
        content_variables= json.dumps({"1": "Joiner - £20ph - Stirling",
                                       "2": "591198",
                                       "3": "8762438"}),
        to='whatsapp:+8801301807991'
    )
    from db_users import create_new_contact, add_thread_id
    
    user = create_new_contact("Noor", "+8801301807991")

    marketing_msg = '''This is a message from Jobadder platform.
Recently you have applied to a job.
Job title: Joiner - £20ph - Stirling
Job ID: 591198
Your Application ID: 8762438
Now I would like to ask you some questions about this job requirements. Would you like to answer here?
If you want, confirm me now.'''
    if user.thread_id is None:
        thread_id = initiate_interaction_marketing(marketing_msg)
        user.thread_id = thread_id
        user.save()
    else:
        sendNewMessage_to_existing_thread_marketing(user.thread_id, marketing_msg)

    if message.error_code is None:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Error: {message.error_message}")
    return message.sid

# print(send_twilio_message())
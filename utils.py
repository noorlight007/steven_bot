import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()
from gpt_functions import *
import time

sample_job_id = "591198"
sample_application_id = "8762438"

# JobAdder API credentials
CLIENT_ID = os.getenv('JOBADDER_CLIENT_ID')
CLIENT_SECRET = os.getenv('JOBADDER_CLIENT_SECRET')

TOKEN_URL = "https://id.jobadder.com/connect/token"
API_BASE_URL = "https://api.jobadder.com/v2"

def get_job_details(job_ad_id, applicantion_id):
    """Handle OAuth callback and exchange code for access token"""
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"https://chatbot.rd1.co.uk/get_job_details?job_id={job_ad_id}&application_id={applicantion_id}", headers= headers)
    # if response.status_code == 200:
    #     job_details = response.json()
    #     return job_details
    # else:
    #     return None
    return response.json()


def update_application_status(applicantion_id, new_status):
    ## Status dictionary
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"https://chatbot.rd1.co.uk/update_application_status?applicantion_id={applicantion_id}&new_status={new_status}", headers= headers)

    if response.status_code == 200:
        return {"success": True}
    else:
        return {"success": False, "reason": "status_not_updated"}


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
        to='whatsapp:+8801571238110'
    )
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"https://chatbot.rd1.co.uk/update_application_status?applicantion_id={sample_application_id}&new_status=sent_waiting", headers= headers)
    from db_users import create_new_contact, add_thread_id
    
    user = create_new_contact("Noor", "+8801571238110")

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
# print(get_job_details(sample_job_id, sample_application_id))

print(send_twilio_message())
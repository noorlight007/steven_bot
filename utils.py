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
    response = requests.get(f"https://chatbot.rd1.co.uk/update_application_status?application_id={applicantion_id}&new_status={new_status}", headers= headers)

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
        content_sid='HX35d8ba28282733ee9a0561e6334e8f1f',
        content_variables= json.dumps({"1": "Maintenance Operative - £14 per hour - Edinburgh",
                                       "2": "592219",
                                       "3": "8808615"}),
        to='whatsapp:+447872603687'
    )
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"https://chatbot.rd1.co.uk/update_application_status?application_id=8808615&new_status=sent_waiting", headers= headers)
    print(response.status_code)
    from db_users import create_new_contact
    
    user = create_new_contact("Steven", "+447872603687")

    marketing_msg = '''This is a message from Recruitment Direct UK Ltd job application platform.
Recently you have applied to a job.
Job title: Maintenance Operative - £14 per hour - Edinburgh
Job ID: 592219
Your Application ID: 8808615
Now I would like to ask you some questions about the job requirements. 
Would you like to answer here?
Type Yes to continue?'''
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



def send_auto_twilio_message():
    from twilio.rest import Client

    account_sid = os.getenv('ACCOUNT_SID')
    auth_token = os.getenv('AUTH_TOKEN')
    messaging_service_sid = os.getenv('MESSAGING_SID')
    twilio_client = Client(account_sid, auth_token)
    headers = {"Content-Type": "application/json"}
    get_live_jobs = requests.get("https://chatbot.rd1.co.uk/get_live_jobs", headers= headers)
    if get_live_jobs.status_code == 200:
        if get_live_jobs.json()['success']:
            live_jobs = get_live_jobs.json()['live_jobs']
        else:
            return {"success": False}
    ## For each jobs
    for job in live_jobs['items']:
        # print(job)
        application_result = requests.get(f"https://chatbot.rd1.co.uk/get_applications_jobID?job_id={job['adId']}", headers= headers)
        if application_result.status_code == 200:
            if application_result.json()['success']:
                applications = application_result.json()['applications']
            else:
                return {"success": False}
        
        # Check if Steven has applied to any applications
        for application_item in applications['items']:
            if application_item['candidate']['candidateId'] == 13514425:
                print("Found steven!")
                if application_item['status']['statusId'] == 2097 or application_item['status']['statusId'] == 27789:   # If application status = "Applied"

                    job_title = job['title']
                    job_title = job_title.replace("/", "")
                    job_title = job_title.replace("  ", " ")
                    print(f"Job Title: {job_title}\nJob ID: {job['adId']}\nApplication ID: {application_item['applicationId']}")

                    message = twilio_client.messages.create(
                        messaging_service_sid=messaging_service_sid,
                        content_sid='HX35d8ba28282733ee9a0561e6334e8f1f',
                        content_variables= json.dumps({"1": f"{job_title}",
                                                    "2": str(job['adId']),
                                                    "3": str(application_item['applicationId'])}),
                        to='whatsapp:+447872603687'
                    )
                    headers = {"Content-Type": "application/json"}
                    response = requests.get(f"https://chatbot.rd1.co.uk/update_application_status?application_id={application_item['applicationId']}&new_status=sent_waiting", headers= headers)
                    print(response.status_code)
                    from db_users import create_new_contact
                    
                    user = create_new_contact("Steven", "+447872603687")

                    marketing_msg = f'''This is a message from Recruitment Direct UK Ltd job application platform.
Recently you have applied to a job.
Job title: {job_title}
Job ID: {job['adId']}
Your Application ID: {application_item['applicationId']}
Now I would like to ask you some questions about the job requirements. 
Would you like to answer here?
Type Yes to continue?'''
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


# send_twilio_message()
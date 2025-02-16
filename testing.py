import requests
# print(send_twilio_message())
job_details = requests.get(f"https://chatbot.rd1.co.uk/get_job_details/{sample_jon_id}/{sample_application_id}").json()
print(job_details)
import requests
# print(send_twilio_message())
sample_jon_id = "591198"
sample_application_id = "8762438"
job_details = requests.get(f"https://chatbot.rd1.co.uk/get_job_details/{sample_jon_id}/{sample_application_id}").json()
print(job_details)
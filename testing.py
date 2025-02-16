import requests
# print(send_twilio_message())
sample_jon_id = "591198"
sample_application_id = "8762438"

data = {
    "job_id": "591198",
    "application_id": "8762438"
}
headers = {"Content-Type": "application/json"}
response = requests.get("https://chatbot.rd1.co.uk/get_job_details", json=data ,headers= headers)
print(response)

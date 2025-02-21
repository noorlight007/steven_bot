import requests
# print(send_twilio_message())
sample_jon_id = "591198"
sample_application_id = "8774208"

data = {
    "application_id": "8774208"
}
headers = {"Content-Type": "application/json"}
response = requests.get("https://chatbot.rd1.co.uk/get_job_details?job_id=591198&application_id=8762438", headers= headers)
print(response)

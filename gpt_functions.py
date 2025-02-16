from openai import OpenAI
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv
load_dotenv()

openAI_key = os.getenv('OPENAI_API')

## Function to upload file into OpenAI
def saveFile_intoOpenAI(file_location):
    client = OpenAI(api_key=openAI_key)
    file = client.files.create(
        file=open(file_location, "rb"),
        purpose='assistants'
    )
    return file.id

# Delete file from openai
def deleteFile(file_id):
    client = OpenAI(api_key=openAI_key)
    file_deletion_status = client.files.delete(file_id = file_id)

    return file_deletion_status


# Creating assistant
def create_assistant(assistant_name, my_instruction):
    client = OpenAI(api_key=openAI_key)
    my_assistant = client.beta.assistants.create(
        name = assistant_name,
        description= "You are a virtual assistant who is very talented in generating questions for a job interview. You will generate questions for a job interview based on the job description. You will also validate the applicant's answers of the questions that you will generate.",
        instructions = my_instruction,
        model="gpt-4",
        temperature= 1.2,
        tools=[
               {
                "type": "function",
                "function": {
                    "name": "get_job_id",
                    "description": "Whenever a customer asks you about a job ad, you will execute this function to get the job details. You will ask the customer to provide the job ID. If the customer provides the job ID, you will return the job details to the customer.",
                    "parameters": {
                        "properties": {
                            "job_id": {
                                "description": "the job ID of the job ad",
                                "title": "Job ID",
                                "type": "string"
                            },
                            "application_id": {
                                "description": "the application ID of the applicant or the user",
                                "title": "Application ID",
                                "type": "string"
                            }
                        },
                        "required": [
                            "job_id",
                            "application_id"
                        ],
                        "type": "object"
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "review_applicant",
                    "description": "You will execute this function to review the applicant's answers of the questions that you will generate. If the applicant reply any of the 'basic questions' with no or negative answers, you will immediately execute this function with the job id and review_statue = 'unsuccessful'. If the applicant reply any of the generated questions with no or negative answers, you won't care, just ask the questions. And when you think no questions are needed, then you will execute this function with the job id and review_statue = 'successful'. If the applicant is not interested in answering the questions, you will execute this function with the job id and review_statue = 'not interested'.",
                    "parameters": {
                        "properties": {
                            "application_id": {
                                "description": "the application ID of the job ad",  ## 8762438
                                "title": "Application ID",
                                "type": "string"
                            },
                            "review_status": {
                                "description": "The review status of the applicant",
                                "title": "Review Status",
                                "type": "string"
                            }
                        },
                        "required": [
                            "application_id",
                            "review_status"
                        ],
                        "type": "object"
                    }
                }
            }
        ],
	)
    return my_assistant.id

def show_assistants():
    client = OpenAI(api_key=openAI_key)
    my_updated_assistant = client.beta.assistants.list()
    return my_updated_assistant

def updateAssistantInstruction(assistant_id,new_instruction):
    client = OpenAI(api_key=openAI_key)
    my_updated_assistant = client.beta.assistants.update(assistant_id,instructions=new_instruction)
    return my_updated_assistant

def updateAssistantVectorDB(assistant_id, vector_store_id):
    client = OpenAI(api_key=openAI_key)
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )


# Create a vector store 
def create_vector_store(store_name):
    client = OpenAI(api_key=openAI_key)
    vector_store = client.beta.vector_stores.create(name=store_name)
    return vector_store.id


# upload file into a vector store 
def upload_file_into_vector_store(vector_store_id ,file_ids):
    client = OpenAI(api_key=openAI_key)
 
    file_batch = client.beta.vector_stores.file_batches.create(
        vector_store_id=vector_store_id, file_ids=file_ids
    )
 
    # Print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)

    print("Done Uploading")
    return file_batch.status


def delete_vector_store_file(vector_store_id, file_id):
    client = OpenAI(api_key=openAI_key)

    deleted_vector_store_file = client.beta.vector_stores.files.delete(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
    print(deleted_vector_store_file)


## Create the Thread
def createThread(prompt):
    client = OpenAI(api_key=openAI_key)
    messages = [{"role":"user", "content": prompt}]
    thread = client.beta.threads.create(messages = messages)
    return thread.id


## Run the Assitance
def runAssistant(thread_id, asssitant_id):
    client = OpenAI(api_key=openAI_key)
    run = client.beta.threads.runs.create(thread_id = thread_id, assistant_id = asssitant_id)
    return run


def sendNewMessage(thread_id,prompt):
    client = OpenAI(api_key=openAI_key)
    thread_message = client.beta.threads.messages.create(thread_id, role= "user", content = prompt)


# Create thread
def initiate_interaction(user_message):
    client = OpenAI(api_key=openAI_key)
    my_thread = client.beta.threads.create(
        messages=[
            {
            "role": "user",
            "content": user_message
            }
        ]
    )
    return my_thread.id

def initiate_interaction_marketing(user_message):
    client = OpenAI(api_key=openAI_key)
    my_thread = client.beta.threads.create(
        messages=[
            {
            "role": "assistant",
            "content": user_message
            }
        ]
    )
    return my_thread.id


# sending message to existing thread
def sendNewMessage_to_existing_thread(thread_id,message):
    client = OpenAI(api_key=openAI_key)
    thread_message = client.beta.threads.messages.create(thread_id, role= "user", content = message)


def sendNewMessage_to_existing_thread_marketing(thread_id,message):
    client = OpenAI(api_key=openAI_key)
    thread_message = client.beta.threads.messages.create(thread_id, role= "assistant", content = message)


# starting a thread
def trigger_assistant(my_thread_id, my_assistant):
    client = OpenAI(api_key=openAI_key)
    run = client.beta.threads.runs.create(thread_id = my_thread_id, assistant_id = my_assistant)
    return run


## See run status
def checkRunStatus(thread_id, run_id):
    client = OpenAI(api_key=openAI_key)
    run = client.beta.threads.runs.retrieve(thread_id = thread_id, run_id = run_id)
    return run

## Retrieve Response from the thread
def retrieveResponse(thread_id):
    client = OpenAI(api_key=openAI_key)
    thread_messages = client.beta.threads.messages.list(thread_id)
    list_messages = thread_messages.data
    assistant_message = list_messages[0]
    message_text = assistant_message.content[0].text.value
    return message_text
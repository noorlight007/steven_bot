from mongoengine import *
from datetime import datetime

# Connection url with Mongodb database
connect(host = "mongodb://127.0.0.1:27017/steven?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.3.9") #This is a local database, that's why the string looks like this.

class Users(Document):
    id = SequenceField(primary_key = True)
    profile_name = StringField(required = True)  # Example: IM1 MARIA 
    whatsapp = StringField(required = True)
    thread_id = StringField()
    created_at = DateTimeField()
    updated_at = DateTimeField()

# Create a new contact
def create_new_contact(profile_name, whatsapp):
    # Check if contact is already available
    contact = Users.objects(whatsapp = whatsapp).first()
    if contact:
        return contact
    new_contact = Users(
        profile_name = profile_name,
        whatsapp = whatsapp,
        created_at = datetime.now(),
        updated_at = datetime.now()
    )
    new_contact.save()
    return new_contact

def add_thread_id(whatsapp, thread_id):
    contact = Users.objects(whatsapp = whatsapp).first()
    if contact:
        contact.thread_id = thread_id
        contact.updated_at = datetime.now()
        contact.save()
        return contact
    return None 
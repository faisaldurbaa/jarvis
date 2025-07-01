import os.path
import datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- IMPORTANT: NEW SCOPES ---
# These scopes grant read/write access. The old token.json will be invalid.
SCOPES = [
    "https://www.googleapis.com/auth/calendar", # Read/Write for Calendar
    "https://www.googleapis.com/auth/tasks",     # Read/Write for Tasks
    "https://www.googleapis.com/auth/gmail.readonly" # Read-Only for Gmail
]

def get_google_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

# --- Google Calendar Tools ---
def get_calendar_events(number_of_events: int = 5) -> str:
    try:
        creds = get_google_creds()
        service = build("calendar", "v3", credentials=creds)
        now = dt.datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(calendarId="primary", timeMin=now, maxResults=number_of_events, singleEvents=True, orderBy="startTime").execute()
        events = events_result.get("items", [])
        if not events: return "No upcoming events found, Sir."
        event_list = "Sir, here are your upcoming events:\n"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            event_list += f"- {start}: {event['summary']}\n"
        return event_list
    except Exception as e: return f"An error occurred: {e}"


def create_calendar_event(summary: str, start_time: str, end_time: str, location: str = "") -> str:
    if len(start_time) == 19:
        try:
            creds = get_google_creds()
            service = build("calendar", "v3", credentials=creds)
            event = {
                'summary': summary,
                'location': location,
                'start': {'dateTime': start_time }, 
                'end': {'dateTime': end_time }
            }
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created successfully, Sir. View it here: {created_event.get('htmlLink')}"
        except Exception as e:
            return f"An error occurred: {e}"
    elif len(start_time)==20:
        try:
            timezone = '+03:00'
            start_time = start_time[:-1]
            end_time = end_time[:-1]
            creds = get_google_creds()
            service = build("calendar", "v3", credentials=creds)
            event = {
                'summary': summary,
                'location': location,
                'start': {'dateTime': f'{start_time+timezone}'},
                'end': {'dateTime': f'{end_time+timezone}'} 
            }
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created successfully, Sir. View it here: {created_event.get('htmlLink')}"
        except Exception as e:
            return f"An error occurred: {e}"
    else:
        try:
            timezone = '+03:00'
            start_time = start_time[:-6]
            end_time = end_time[:-6]
            creds = get_google_creds()
            service = build("calendar", "v3", credentials=creds)
            event = {
                'summary': summary,
                'location': location,
                'start': {'dateTime': f'{start_time+timezone}'},
                'end': {'dateTime': f'{end_time+timezone}'} 
            }
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created successfully, Sir. View it here: {created_event.get('htmlLink')}"
        except Exception as e:
            return f"An error occurred: {e}"

# --- Google Tasks Tools ---
def list_google_tasks(max_tasks: int = 20) -> str:
    try:
        creds = get_google_creds()
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list().execute().get('items', [])
        if not tasklists: return "No Google Tasks lists found."
        primary_list_id = tasklists[0]['id']
        results = service.tasks().list(tasklist=primary_list_id, maxResults=max_tasks, showCompleted=False).execute()
        items = results.get('items', [])
        if not items: return "No active tasks found, Sir."
        task_list_str = "Sir, here are your current tasks:\n"
        for item in items:
            task_list_str += f"- {item['title']}\n"
        return task_list_str
    except Exception as e: return f"An error occurred: {e}"


def create_google_task(title: str, notes: str = "") -> str:
    try:
        creds = get_google_creds()
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list().execute().get('items', [])
        if not tasklists: return "No Google Tasks lists found."
        primary_list_id = tasklists[0]['id']
        task = {'title': title, 'notes': notes}
        result = service.tasks().insert(tasklist=primary_list_id, body=task).execute()
        return f"Task '{result['title']}' created successfully, Sir."
    except Exception as e: return f"An error occurred: {e}"

# --- Gmail Tools ---
def read_emails(number_of_emails: int = 5) -> str:
    try:
        creds = get_google_creds()
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=number_of_emails, labelIds=['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])
        if not messages: return "No new unread emails found, Sir."
        email_list = "Sir, here is a summary of your latest unread emails:\n"
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            email_list += f"- From: {sender}\n  Subject: {subject}\n"
        return email_list
    except Exception as e: return f"An error occurred: {e}"


#example usages:
#create_calendar_event(summary="Team sync-up", start_time="2025-06-23T10:00:00+03:00", end_time="2025-06-23T11:00:00+03:00",location="Zoom")
#create_google_task("Project Phase-1")
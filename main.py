

from __future__ import print_function

from datetime import datetime
from multiprocessing.util import DEFAULT_LOGGING_FORMAT
import os
import time
import sys

sys.path.append("lib")

from icalendar import Calendar
import wget

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
LOCAL_FILE = 'calendar.ics'
SERVICE_ACCOUNT_FILE = "service_account.json"

REMOTE_URL = os.getenv("REMOTE_URL")
CALENDAR = os.getenv("CALENDAR")
IDENTIFY_CHAR = os.getenv("IDENTIFY_CHAR")
COLORS = os.getenv("COLORS").split(",")

def main():
    inizio_semestre = datetime.now()
    fine_semestre = datetime.now()

    today = datetime.now()

    inizio = [1, 2]
    meta = [8, 9, 10, 11, 12]
    
    inizio_primo_semestre = datetime(today.year, 8, 15)
    fine_primo_semestre = datetime(today.year, 1, 30)

  
    if today.month in inizio:
        inizio_primo_semestre = datetime((today.year - 1), 8, 15)
    elif today.month in meta:
        fine_primo_semestre = datetime((today.year + 1), 1, 30)

    
    inizio_secondo_semestre = datetime(today.year, 2, 1)
    fine_secondo_semestre = datetime(today.year, 8, 14)

    if inizio_primo_semestre <= today <= fine_primo_semestre:
        inizio_semestre = inizio_primo_semestre
        fine_semestre = fine_primo_semestre
    elif inizio_secondo_semestre <= today <= fine_secondo_semestre:
        inizio_semestre = inizio_secondo_semestre
        fine_semestre = fine_secondo_semestre

    if os.path.exists(LOCAL_FILE):
        os.remove(LOCAL_FILE)
    
    wget.download(REMOTE_URL, LOCAL_FILE)

    g = open(LOCAL_FILE,'rb')
    gcal = Calendar.from_ical(g.read())
    g.close()

    corsi = []

    for component in gcal.walk():
        if component.name == "VEVENT":
            if not (component.get('summary') in corsi):
                corsi.append(component.get('summary'))

    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(calendarId=CALENDAR,
                                            timeMin=(inizio_semestre.isoformat() + "Z"),
                                            timeMax=(fine_semestre.isoformat() + "Z"),
                                            singleEvents=True,
                                            orderBy='startTime'
                                        ).execute()

        events = events_result.get('items', [])

        for event in events:
            if ("description" in event) and (event["description"][-1] == IDENTIFY_CHAR):
                print("Delete - " + event['summary'])
                service.events().delete(calendarId = CALENDAR, eventId = event['id']).execute()
                time.sleep(1/10)
    except HttpError as error:
        print('An error occurred: %s' % error)    

    for component in gcal.walk():
        if component.name == "VEVENT":
            if(inizio_semestre.isoformat() <= component.get('DTSTART').dt.isoformat() <= fine_semestre.isoformat()):
                location =  component.get('location')
                if "Aula A" in component.get('location'):
                    location = "Polo Ferrari - Povo 1"
                elif "Aula B" in component.get('location'):
                    location = "Polo Ferrari - Povo 2"
                stato = component.get("status") +  " - "
                if("CANCELLED" not in stato):
                    stato = ""
                    
                event = {
                    'summary': stato + component.get('summary'),
                    'location': location,
                    'description': component.get('description') + IDENTIFY_CHAR,
                    'colorId' : COLORS[corsi.index(component.get('summary'))],
                    'start': {
                        'dateTime': component.get('DTSTART').dt.isoformat(),
                        'timeZone': 'America/Los_Angeles',
                    },
                    'end': {
                        'dateTime': component.get('DTEND').dt.isoformat(),
                        'timeZone': 'America/Los_Angeles',
                    }
                }
                print("Creating - " + component.get('summary'))
                event = service.events().insert(calendarId = CALENDAR, body = event).execute()
                time.sleep(1/8)
 
if __name__ == '__main__':
    main()
"""
generate icalender (.ics) files from timetable data (classes.json & metadata.json)
and organize them into subdirectories.
files are genrated as - ./ical/{course_id}/{sem_id}/{phase_id}/{batch}.ics
"""

import json
import datetime
import os
from typing import Dict, List
from icalendar import Calendar, Event as CalEvent, Timezone, TimezoneStandard
import pytz



def get_next_weekday(start_date: datetime.date, weekday: int):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return start_date + datetime.timedelta(days_ahead)


def generate_icalendar_for_batch(events_data: dict, course_id: str, sem_id: str, phase_id: str, batch_id: str) -> Calendar:
    """Generate icalender for a specific batch"""
    cal = Calendar()
    cal.add('prodid', f'-//JIIT Planner//Timetable {course_id} {sem_id} {phase_id} {batch_id}//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', f'JIIT {course_id.upper()} {sem_id.upper()} {phase_id.upper()} {batch_id.upper()} Timetable')
    
    # Add timezone for correct timing
    tz = Timezone()
    tz.add('tzid', 'Asia/Kolkata')
    tz.add('x-lic-location', 'Asia/Kolkata')
    
    # Standard time component for Asia/Kolkata (IST is UTC+5:30 all year)
    tz_standard = TimezoneStandard()
    tz_standard.add('tzname', 'IST')
    tz_standard.add('dtstart', datetime.datetime.now())
    tz_standard.add('tzoffsetfrom', datetime.timedelta(hours=5, minutes=30))
    tz_standard.add('tzoffsetto', datetime.timedelta(hours=5, minutes=30))
    
    tz.add_component(tz_standard)
    cal.add_component(tz)
    
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # Use current date as start reference
    start_date = datetime.date.today()
    timezone = pytz.timezone('Asia/Kolkata')
    
    # Creation timestamp for all events
    creation_time = datetime.datetime.now(timezone)
    
    classes = events_data.get('classes', {})
    
    for day_name, day_events in classes.items():
        if not day_events:  # Skip empty days
            continue
            
        day_lower = day_name.lower()
        if day_lower not in weekdays:
            continue
            
        weekday = weekdays[day_lower]
        event_date = get_next_weekday(start_date, weekday)
        
        for event_info in day_events:
            # Create calendar event
            cal_event = CalEvent()
            
            start_time = datetime.datetime.strptime(event_info['start'], "%I:%M %p").time()
            end_time = datetime.datetime.strptime(event_info['end'], "%I:%M %p").time()

            
            start_datetime = timezone.localize(
                datetime.datetime.combine(event_date, start_time)
            )
            end_datetime = timezone.localize(
                datetime.datetime.combine(event_date, end_time)
            )
            
            # Set event properties
            cal_event.add('uid', f"{course_id}_{sem_id}_{phase_id}_{batch_id}_{day_name}_{event_info['start']}_{event_info['subjectcode']}")
            cal_event.add('dtstamp', creation_time)
            cal_event.add('dtstart', start_datetime)
            cal_event.add('dtend', end_datetime)
            cal_event.add('summary', f"{event_info['subject']} ({event_info['subjectcode']})")
            
            # description
            description = f"Subject: {event_info['subject']}\n"
            description += f"Subject Code: {event_info['subjectcode']}\n"
            description += f"Teacher: {event_info['teacher']}\n"
            description += f"Venue: {event_info['venue']}\n"
            description += f"Type: {event_info['type']}\n"
            description += f"Batches: {', '.join(event_info['batches'])}"
            
            cal_event.add('description', description)
            cal_event.add('location', event_info['venue'])
            
            # Add custom property to disable notifications (google calender)
            cal_event.add('x-google-default-reminders', 'false')
            
            # Set rule for weekly repetition
            cal_event.add('rrule', {
                'freq': 'weekly',
                'count': 16  # Assuming 16 weeks in a semester
            })
            
            cal.add_component(cal_event)
    
    return cal


def generate_icalendars(classes: dict) -> None:
    os.makedirs("ical", exist_ok=True)
    
    for class_batch_key, events_data in classes.items():
        parts = class_batch_key.split('_')
        if len(parts) >= 4:
            course_id = parts[0]
            sem_id = parts[1]
            phase_id = parts[2]
            batch_id = parts[3]
            
            ical_dir = f"ical/{course_id}/{sem_id}/{phase_id}"  #Access like (url)/ical/{course_id}/{sem_id}/{phase_id}/{batch}.ics"
            os.makedirs(ical_dir, exist_ok=True)
            
            cal = generate_icalendar_for_batch(events_data, course_id, sem_id, phase_id, batch_id)
            
            ical_filename = f"{ical_dir}/{batch_id}.ics"
            with open(ical_filename, 'wb') as f:
                f.write(cal.to_ical())
            
            print(f"Generated icalender: {ical_filename}")


def generate_icalendars_json(json_file_path: str = "classes.json"):
    """Genrate icalender files from json files"""
    try:
        # Load classes data
        with open(json_file_path, 'r') as f:
            classes = json.load(f)
        
        # Generate icalender files
        generate_icalendars(classes)
        
        print(f"icalender files generated from {json_file_path}")
        
    except FileNotFoundError as e:
        print(f"File not found {e}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format {e}")



if __name__ == "__main__":
    if os.path.exists("classes.json"):
        generate_icalendars_json("classes.json")
    else:
        print("classes.json not found --> Please run generate_cache.py first")

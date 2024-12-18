from jiit_tt_parser.parser import parse_events
from jiit_tt_parser.utils import load_worksheet
from jiit_tt_parser.utils.cache import get_cache_file
from typing import List
from jiit_tt_parser.parser.parse_events import Event, datetime
import json

def split_on_number(key: str):
    for i, k in enumerate(key):
        if k.isdigit():
            return key[:i], int(key[i:])

    return key, 0




def get_events(branch: str, sem: str) -> tuple[List[Event], List[str]]:
    xl_code = '-'.join((branch, sem))
    branches = {
        "btech-sem1": "sem1.xlsx",
        "bca-sem1": "bca_sem1_new.xlsx",
        "bca-sem3": "bca_sem1_new.xlsx",
    }
    branch_xl = branches.get(xl_code)

    if not branch_xl:
        return [],[]

    sheet, r, c = load_worksheet(get_cache_file(branch_xl))
    evs = parse_events(sheet, r, c)
    batches = set()
    for ev in evs:
        batches = batches.union(ev.batches)

    return evs, sorted(batches, key=split_on_number)


def filter_events(evs: List[Event], batch: str, day: str) -> List[dict]:
    filtered_evs = []

    for ev in evs:
        if (batch is None) or (batch not in ev.batches):
            continue

        if (day is not None) and (not ev.day.lower() == day.lower()):
            continue
        data = {}
        data["start"] = ev.period.start_time.strftime("%I:%M %p")
        data["end"] = ev.period.end_time.strftime("%I:%M %p")

        data["subject"] = ev.event or ev.eventcode
        data["subjectcode"] = ev.eventcode
        data["teacher"] = ', '.join(ev.lecturer)
        data["batches"] = ev.batches
        data["venue"] = ev.classroom



        filtered_evs.append(data)

    return filtered_evs


def generate_json():
    CACHE_VERSION = datetime.datetime.today().strftime("v%Y.%m.%d.%H.%M.%S")
    branches = {"btech": "B.Tech", "bca": "BCA"}
    semesters = {"btech": [1], "bca": [1]}

    metadata = {"courses": [], "semesters": {}, "batches": {}}
    classes = {}
    for course_id, course in branches.items():
        metadata["courses"].append({"id": course_id, "name": course})

        metadata["semesters"][course_id] = []
        metadata["batches"][course_id] = {}
        for sem in semesters[course_id]:
            sem_id = f"sem{sem}"
            metadata["semesters"][course_id].append({"id": sem_id, "name": str(sem)})

            metadata["batches"][course_id][sem_id] = []

            evs, batches = get_events(course_id, sem_id)
            for batch in batches:
                batch_id = batch.lower()
                metadata["batches"][course_id][sem_id].append({"id": batch_id, "name": batch})
                class_batch_key = "_".join((course_id, sem_id, batch_id))
                classes[class_batch_key] = {"cacheVersion": CACHE_VERSION, "classes":{}}
                for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:

                    classes[class_batch_key]["classes"][day] =  filter_events(evs, batch, "Wednesday")


    
    return metadata, classes

if __name__ == "__main__":
    metadata, classes = generate_json()
    with open("metadata.json", "w+") as f:
        json.dump(metadata, f)

    with open("classes.json", "w+") as f:
        json.dump(classes, f)

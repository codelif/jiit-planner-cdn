from jiit_tt_parser.parser import parse_events
from jiit_tt_parser.utils import load_worksheet
from jiit_tt_parser.utils.cache import get_cache_file
from jiit_tt_parser.parser.parse_events import Event
from jiit_tt_parser.parser.parse_faculty import search_bounds, generate_faculty_map, get_faculty_map_from_sem1, get_faculty_map_from_bca1
import json
import datetime
import os
import openpyxl
from typing import Dict, List

TIME_TABLE = os.path.join("raw", "time_tables")
FACULTY = os.path.join("raw", "faculty")


def maps():
    branches: Dict[str, str] = {}
    semesters: Dict[str, List[str]] = {}
    phases: Dict[str, Dict[str, List[str]]] = {}
    paths: Dict[str, str] = {}

    for branch in os.listdir(TIME_TABLE):
        if not os.path.isdir(os.path.join(TIME_TABLE, branch)):
            continue

        branch_name = branch[: branch.find("(")].strip()
        branch_code = branch[branch.find("(") :].strip(" ()")
        branches.update({branch_code: branch_name})
        semesters[branch_code] = []
        phases[branch_code] = {}

        for sem in os.listdir(os.path.join(TIME_TABLE, branch)):
            if not os.path.isdir(os.path.join(TIME_TABLE, branch, sem)):
                continue

            semesters[branch_code].append(sem)
            phases[branch_code][sem] = []
            
            for tt in os.listdir(os.path.join(TIME_TABLE, branch, sem)):
                path = os.path.abspath(os.path.join(TIME_TABLE, branch, sem, tt))
                if not os.path.isfile(path):
                    continue

                if not path.endswith((".xls", ".xlsx")):
                    continue
                phase = tt.split('.')[0]
                phases[branch_code][sem].append(phase)
                paths[f'{branch_code}_sem{sem}_phase{phase}'] = path
    
    return branches, semesters, phases, paths

def split_on_number(key: str):
    for i, k in enumerate(key):
        if k.isdigit():
            return key[:i], int(key[i:])

    return key, 0

def get_faculty_map():
    fac1_xl_path = './raw/faculty/10. Faculty Abbreviations_Even 2025.xlsx'
    sem1_xl_path = "./raw/faculty/1. BTech II Sem _Even 2025.xlsx"
    bca1_xl_path = './raw/faculty/6. BCA II Sem and IV Sem_Even 2025.xlsx'

    wb = openpyxl.load_workbook(fac1_xl_path)
    sheet = wb.active
    r, c = search_bounds(sheet)
    faculty_map = generate_faculty_map(sheet, r, c)
    faculty_map.update(get_faculty_map_from_sem1(sem1_xl_path))
    faculty_map.update(get_faculty_map_from_bca1(bca1_xl_path))
    
    with open("faculty.json", "w+") as f:
        json.dump(faculty_map, f)

def get_events(branch_xl: str | None) -> tuple[List[Event], List[str]]:
    if not branch_xl:
        return [],[]

    sheet, r, c = load_worksheet(branch_xl)
    evs = parse_events(sheet, r, c, "faculty.json")
    batches = set()
    for ev in evs:
        print(ev)
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
        data["teacher"] = ', '.join(ev.lecturer)+'T'
        data["batches"] = ev.batches
        data["venue"] = ev.classroom
        data["type"] = ev.event_type



        filtered_evs.append(data)

    return filtered_evs


def generate_json():
    CACHE_VERSION = datetime.datetime.today().strftime("v%Y.%m.%d.%H.%M.%S")
    branches, semesters, phases, excels = maps()

    metadata = {"cacheVersion": CACHE_VERSION, "courses": [], "semesters": {}, "phases": {}, "batches": {}}
    classes = {}
    for course_id, course in branches.items():
        metadata["courses"].append({"id": course_id, "name": course})
        metadata["semesters"][course_id] = []
        metadata["batches"][course_id] = {}
        metadata["phases"][course_id] = {}
        for sem in semesters[course_id]:
            sem_id = f"sem{sem}"
            metadata["semesters"][course_id].append({"id": sem_id, "name": str(sem)})
            metadata["phases"][course_id][sem_id] = []
            metadata["batches"][course_id][sem_id] = {}
            
            for phase in phases[course_id][sem]:
                phase_id = f"phase{phase}"
                metadata["phases"][course_id][sem_id].append({"id": phase_id, "name": str(phase)})
                metadata["batches"][course_id][sem_id][phase_id] = []
                excel_path = excels.get('_'.join((course_id, sem_id, phase_id)))
                evs, batches = get_events(excel_path)
                for batch in batches:
                    batch_id = batch.lower()
                    metadata["batches"][course_id][sem_id][phase_id].append({"id": batch_id, "name": batch})
                    class_batch_key = "_".join((course_id, sem_id, phase_id, batch_id))
                    classes[class_batch_key] = {"cacheVersion": CACHE_VERSION, "classes":{}}
                    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:

                        classes[class_batch_key]["classes"][day] =  filter_events(evs, batch, day)


    
    return metadata, classes

if __name__ == "__main__":
    get_faculty_map()
    metadata, classes = generate_json()
    # import sys
    # json.dump(metadata, sys.stdout)
    # json.dump(classes, sys.stdout)

    with open("classes.json", "w+") as f:
        json.dump(classes, f)
    with open("metadata.json", "w+") as f:
        json.dump(metadata, f)

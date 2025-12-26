from jiit_tt_parser.parser import parse_events
from jiit_tt_parser.utils import load_worksheet
from jiit_tt_parser.parser.parse_events import Elective, Event
from jiit_tt_parser.parser.parse_faculty import (
    generate_faculty_map,
    get_faculty_map_from_sem1,
    get_faculty_map_from_bca1_N_128,
)
import json
import datetime
import os
from typing import Dict, List
from generate_icalendar import generate_icalendars_json
from generate_curriculum import curriculum

TIME_TABLE = os.path.join("raw", "time_tables")
FACULTY = os.path.join("raw", "faculty")
electives_file = "./raw/electives/electives.xlsx"


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
                if tt.startswith("."):
                    continue

                phase = tt.split(".")[0]
                phases[branch_code][sem].append(phase)
                paths[f"{branch_code}_sem{sem}_phase{phase}"] = path

    return branches, semesters, phases, paths


def split_on_number(key: str):
    for i, k in enumerate(key):
        if k.isdigit():
            return key[:i], int(key[i:])

    return key, 0


def get_faculty_map():
    fac1_xl_path = "./raw/faculty/10. Faculty Abbreviations_Even 2025.xlsx"
    sem1_xl_path = "./raw/faculty/1. BTech II Sem _Even 2025.xlsx"
    bca1_xl_path = "./raw/faculty/6. BCA II Sem and IV Sem_Even 2025.xlsx"
    fac128_xl_path = "./raw/faculty/1.xlsx"

    faculty_map_62 = {}
    faculty_map_128 = {}
    faculty_map_62.update(generate_faculty_map(fac1_xl_path))
    faculty_map_62.update(get_faculty_map_from_sem1(sem1_xl_path))
    faculty_map_62.update(get_faculty_map_from_bca1_N_128(bca1_xl_path))
    faculty_map_128.update(get_faculty_map_from_bca1_N_128(fac128_xl_path))

    with open("faculty_62.json", "w+") as f:
        json.dump(faculty_map_62, f)
    with open("faculty_128.json", "w+") as f:
        json.dump(faculty_map_128, f)


def get_curriculum_map():
    e = curriculum()
    with open("curriculum.json", "w+") as f:
        json.dump(e, f)


def get_events(
    branch_xl: str | None, faculty_json: str
) -> tuple[List[Event | Elective], List[str]]:
    if not branch_xl:
        return [], []

    ws = load_worksheet(branch_xl)
    if ws is None:
        return [], []

    sheet, r, c = ws
    evs = parse_events(sheet, electives_file, r, c, faculty_json, "curriculum.json")
    batches = set()
    for ev in evs:
        if ev is not None:
            # print(ev)
            batches = batches.union(ev.batches)

    return evs, sorted(batches, key=split_on_number)


def filter_events(evs: List[Event | Elective], batch: str, day: str) -> List[dict]:
    filtered_evs = []

    for ev in evs:
        # print(ev)
        if ev is None:
            continue
        if isinstance(ev, Elective):
            continue
        if (batch is None) or (batch not in ev.batches):
            continue

        if (day is not None) and (not ev.day.lower() == day.lower()):
            continue
        data = {}
        data["is_elective"] = False
        data["start"] = ev.period.start_time.strftime("%I:%M %p")
        data["end"] = ev.period.end_time.strftime("%I:%M %p")

        data["day"] = ev.day.lower()
        data["subject"] = ev.event or ev.eventcode
        data["subjectcode"] = ev.eventcode
        data["teacher"] = ", ".join(ev.lecturer)
        data["batches"] = ev.batches
        data["venue"] = ev.classroom
        data["type"] = ev.event_type

        filtered_evs.append(data)

    return filtered_evs


def get_prefix_batches(batches: List[str], prefix: str):
    pbatches = []

    for batch in batches:
        if batch.startswith(prefix):
            pbatches.append(batch)

    return pbatches


def get_electives(evs: List[Event | Elective], batches: List[str]) -> List[dict]:
    filtered_evs = []

    for ev in evs:
        # print(ev)
        if ev is None:
            continue

        if not isinstance(ev, Elective):
            continue

        data = {}
        data["is_elective"] = True
        data["start"] = ev.period.start_time.strftime("%I:%M %p")
        data["end"] = ev.period.end_time.strftime("%I:%M %p")

        data["subject"] = ev.event or ev.eventcode
        data["subjectcode"] = ev.eventcode
        data["teacher"] = ", ".join(ev.lecturer)
        data["day"] = ev.day.lower()
        
        from pprint import pprint
        pprint(ev.batch_cats)
        pprint(batches)
        for bcat in ev.batch_cats:
            ev.batches = list(
                set(ev.batches).union(get_prefix_batches(batches, bcat))
            )

        if len(ev.batches) == 0:
            ev.batches = batches
        data["batches"] = ev.batches
        data["category"] = ev.category
        data["venue"] = ev.classroom
        data["type"] = ev.event_type

        filtered_evs.append(data)

    return filtered_evs


def filter_electives(evs: List[dict], batch: str, day: str) -> List[dict]:
    filtered_evs = []

    for ev in evs:
        if (day is not None) and (not ev["day"].lower() == day.lower()):
            continue

        if (batch is None) or (batch not in ev["batches"]):
            continue
        filtered_evs.append(ev)

    return filtered_evs


def generate_json():
    CACHE_VERSION = datetime.datetime.today().strftime("v%Y.%m.%d.%H.%M.%S")
    branches, semesters, phases, excels = maps()
    metadata = {
        "cacheVersion": CACHE_VERSION,
        "courses": [],
        "semesters": {},
        "phases": {},
        "batches": {},
    }
    classes = {}
    faculty_json = ""
    for course_id, course in branches.items():
        if course_id == "btech-128":
            faculty_json = "faculty_128.json"
        elif course_id == "btech-62" or course_id == "bca-62":
            faculty_json = "faculty_62.json"
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
                metadata["phases"][course_id][sem_id].append(
                    {"id": phase_id, "name": str(phase)}
                )
                metadata["batches"][course_id][sem_id][phase_id] = []
                excel_path = excels.get("_".join((course_id, sem_id, phase_id)))
                evs, batches = get_events(excel_path, faculty_json)
                print(batches)
                electives = get_electives(evs, batches)
                elective_key = "_".join((course_id, sem_id, phase_id))
                classes["electives"] = {}
                classes["electives"][elective_key] = electives

                for batch in batches:
                    batch_id = batch.lower()
                    metadata["batches"][course_id][sem_id][phase_id].append(
                        {"id": batch_id, "name": batch}
                    )
                    class_batch_key = "_".join((course_id, sem_id, phase_id, batch_id))
                    classes[class_batch_key] = {
                        "cacheVersion": CACHE_VERSION,
                        "classes": {},
                    }
                    for day in [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ]:
                        classes[class_batch_key]["classes"][day] = filter_events(
                            evs, batch, day
                        )
                        classes[class_batch_key]["classes"][day].extend(
                            filter_electives(electives, batch, day)
                        )

    return metadata, classes


if __name__ == "__main__":
    get_faculty_map()

    metadata, classes = generate_json()
    # import sys
    # json.dump(metadata, sys.stdout)
    # json.dump(classes, sys.stdout)

    # generate_icalendars(classes) use when classes data fixed

    with open("classes.json", "w+") as f:
        json.dump(classes, f)
    with open("metadata.json", "w+") as f:
        json.dump(metadata, f)

    # Generate iCalendar files
    generate_icalendars_json("classes.json")

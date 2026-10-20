import datetime
import gzip
import json
import os
from typing import Dict, List

import cbor2
from generate_curriculum import curriculum
from generate_icalendar import generate_icalendars_json
from jiit_tt_parser.parser import parse_events
from jiit_tt_parser.parser.parse_events import Elective, Event
from jiit_tt_parser.parser.parse_faculty import (
    generate_faculty_map, get_faculty_map_from_128_sem4,
    get_faculty_map_from_bca1_N_128, get_faculty_map_from_sem1)
from jiit_tt_parser.utils import load_worksheet

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
    fac2_xl_path = "./raw/faculty/Faculty Abbreviations EVEN 2026.xlsx"
    sem1_xl_path = "./raw/faculty/1. BTech II Sem _Even 2025.xlsx"
    bca1_xl_path = "./raw/faculty/6. BCA II Sem and IV Sem_Even 2025.xlsx"
    fac128_xl_path = "./raw/faculty/1.xlsx"
    fac128_xl_path_2 = "./raw/faculty/1 (copy 1).xlsx"

    faculty_map_62 = {}
    faculty_map_128 = {}
    faculty_map_62.update(generate_faculty_map(fac1_xl_path))
    faculty_map_62.update(generate_faculty_map(fac2_xl_path))
    faculty_map_62.update(get_faculty_map_from_sem1(sem1_xl_path))
    faculty_map_62.update(get_faculty_map_from_bca1_N_128(bca1_xl_path))
    faculty_map_128.update(get_faculty_map_from_bca1_N_128(fac128_xl_path))
    faculty_map_128.update(get_faculty_map_from_128_sem4(fac128_xl_path_2))

    with open("faculty_62.json", "w+") as f:
        json.dump(faculty_map_62, f)
    with open("faculty_128.json", "w+") as f:
        json.dump(faculty_map_128, f)


def get_curriculum_map():
    e = curriculum()
    with open("curriculum.json", "w+") as f:
        json.dump(e, f)


def get_events(
    branch_xl: str | None, faculty_json: str, course_context: str = ""
) -> tuple[List[Event | Elective], List[str]]:
    if not branch_xl:
        return [], []

    ws = load_worksheet(branch_xl)
    if ws is None:
        return [], []

    sheet, r, c = ws
    evs = parse_events(
        sheet,
        electives_file,
        r,
        c,
        faculty_json,
        "curriculum.json",
        course_context,
    )
    batches = set()
    for ev in evs:
        if ev is not None:
            # print(ev)
            batches = batches.union(ev.batches)

    batches.discard("ALL")
    sorted_batches = sorted(batches, key=split_on_number)
    for ev in evs:
        if ev is not None and "ALL" in ev.batches:
            ev.batches = sorted_batches

    return evs, sorted_batches


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
        data["batches"] = sorted(ev.batches, key=split_on_number)
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

        for bcat in ev.batch_cats:
            ev.batches = list(set(ev.batches).union(get_prefix_batches(batches, bcat)))

        if len(ev.batches) == 0:
            ev.batches = batches
        data["batches"] = sorted(ev.batches, key=split_on_number)
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
    classes = {
        "electives": {},
    }
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
                elective_key = "_".join((course_id, sem_id, phase_id))
                evs, batches = get_events(excel_path, faculty_json, elective_key)
                print(batches)
                electives = get_electives(evs, batches)
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


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def to_minutes(t: str) -> int:
    clock = datetime.datetime.strptime(t, "%I:%M %p")
    return clock.hour * 60 + clock.minute


def build_planner(metadata: dict, classes: dict) -> dict:
    """
    every batch in one deduplicated blob for apps: text lives once in strings,
    each class once in events, batches and electives point at event ids.
    event: [day 0=mon, start, end, subject, code, teacher, venue, type, category, elective, [batches]]
    times are minutes from midnight, a missing category is -1.
    """
    strings: Dict[str, int] = {}
    events: Dict[tuple, int] = {}

    def sid(s):
        if s is None:
            return -1
        if s not in strings:
            strings[s] = len(strings)
        return strings[s]

    def eid(e: dict) -> int:
        start, end = to_minutes(e["start"]), to_minutes(e["end"])
        # the parser writes 8 am classes as ending at 08:50 pm
        if end - start > 180 and end - 720 > start:
            end -= 720
        key = (
            DAYS.index(e["day"].lower()),
            start,
            end,
            sid(e["subject"]),
            sid(e["subjectcode"]),
            sid(e["teacher"]),
            sid(e["venue"]),
            sid(e["type"]),
            sid(e.get("category")),
            1 if e["is_elective"] else 0,
            tuple(sid(b) for b in e["batches"]),
        )
        if key not in events:
            events[key] = len(events)
        return events[key]

    courses = []
    for course in metadata["courses"]:
        c = course["id"]
        sems = []
        for sem in metadata["semesters"][c]:
            s = sem["id"]
            phases = []
            for phase in metadata["phases"][c][s]:
                p = phase["id"]
                batches = []
                for batch in metadata["batches"][c][s][p]:
                    week = classes["_".join((c, s, p, batch["id"]))]["classes"]
                    ids = [eid(e) for day in week.values() for e in day]
                    batches.append({"id": batch["id"], "name": batch["name"], "events": ids})
                electives = [eid(e) for e in classes["electives"].get("_".join((c, s, p)), [])]
                phases.append({"id": p, "name": phase["name"], "electives": electives, "batches": batches})
            sems.append({"id": s, "name": sem["name"], "phases": phases})
        courses.append({"id": c, "name": course["name"], "semesters": sems})

    return {
        "format": 1,
        "version": metadata["cacheVersion"],
        "strings": list(strings),
        "events": [list(k[:10]) + [list(k[10])] for k in events],
        "courses": courses,
    }


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
    # mtime=0 so the same data always gzips to the same bytes
    with open("planner.cbor.gz", "wb") as f:
        f.write(gzip.compress(cbor2.dumps(build_planner(metadata, classes)), 9, mtime=0))

    # Generate iCalendar files
    generate_icalendars_json("classes.json")

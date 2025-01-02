import os
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


if __name__ == "__main__":
    from pprint import pprint

    pprint(maps())

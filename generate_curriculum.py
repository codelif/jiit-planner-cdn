from typing import Dict, List, Callable, Optional
import camelot
from camelot.core import TableList
import json

PATH = "./raw/electives/curriculum{year}.pdf"
YEARS = [2018, 2024]
ParserFunction = Optional[Callable[[TableList], List[List[str]]]]


def parse_2018(tables: TableList) -> List[List[str]]:
    all_years_electives: List[List[str]] = []
    for table in tables:
        sem_electives: List[str] = []
        for r in range(1, len(table.rows) - 1):
            cell = table.cells[r][2]
            text = " ".join(cell.text.replace("\u2013", "-").strip(" \n").split())
            if text:
                sem_electives.append(text)
        all_years_electives.append(sem_electives)
    return all_years_electives


def parse_2024(tables: TableList) -> List[List[str]]:
    all_years_electives: List[List[str]] = []
    for table in tables:
        sem_electives: List[str] = []
        for r in range(1, len(table.rows)):
            cell1 = table.cells[r][2]
            cell2 = table.cells[r][2]
            text1 = " ".join(cell1.text.replace("\u2013", "-").strip(" \n").split())
            text2 = " ".join(cell2.text.replace("\u2013", "-").strip(" \n").split())
            text = text1 + " " + text2
            if text:
                sem_electives.append(text)
        all_years_electives.append(sem_electives)
    return all_years_electives


def parse_electives() -> Dict[str, List[List[str]]]:
    """
    All year-wise parse function should be defined above this
    The function name should be of the format parse_{year}
    with the function signature of:
    def parse_{year}(tables: TableList) -> List[List[str]]:

    in all seriousness, it doesn't work, it doesn't need to.
    for something that might change once in 5 years.  idc
    ask an llm to format it
    """
    electives: Dict[str, List[List[str]]] = {}
    for year in YEARS:
        path = PATH.format(year=year)
        tables: TableList = camelot.read_pdf(path, pages="all")[:8]
        parse_year: ParserFunction = globals().get(f"parse_{year}")
        if parse_year is not None:
            electives.update({str(year): parse_year(tables)})
        else:
            print(f"function 'parse_{year}' does not exist.")
    return electives


def generate_electives() -> Dict[int, Dict[int, List[str]]]:
    return {
        2018: {
            4: ["HSS-1"],
            5: ["HSS-2", "DE-1", "SE"],
            6: ["DE-2", "DE-3", "OE-1", "HSS-3"],
            7: ["DE-4", "DE-5", "DE-6", "OE-2"],
            8: ["DE-7", "DE-8", "OE-3"],
        },
        2024: {
            4: ["HSS-1", "DE-1"],
            5: ["DE-2", "DE-3", "SE"],
            6: ["DE-4", "DE-5", "OE-1"],
            7: ["DE-6", "OE-2"],
            8: ["DE-7", "OE-3"],
        },
    }


def generate_courses() -> Dict[str, str]:
    courses_years = [
        {
            "15B11MA111": "Mathematics-1",
            "15B11PH111": "Physics-1",
            "15B11CI111": "Software Development Fundamentals-I",
            "15B11HS112": "English",
            "15B17PH171": "Physics Lab-1",
            "15B17CI171": "Software Development Lab-I",
            "18B15GE111": "Engineering Drawing & Design",
            "15B11MA211": "Mathematics-2",
            "15B11PH211": "Physics-2",
            "15B11EC111": "Electrical Science-I",
            "15B11CI211": "Software Development Fundamentals-II",
            "15B17PH271": "Physics Lab-2",
            "15B17EC171": "Electrical Science Lab-I",
            "15B17CI271": "Software Development Lab-II",
            "18B15GE112": "Workshop",
            "15B11CI212": "Theoretical Foundations of Computer Science",
            "15B11CI312": "Database Systems and Web",
            "15B11CI311": "Data Structures",
            "15B17CI371": "Data Structures Lab",
            "15B17CI372": "Database Systems and Web Lab",
            "15B11EC211": "Electrical Science-II",
            "15B17EC271": "Electrical Science Lab-II",
            "15B11HS211": "Economics",
            "15B11MA301": "Probability and Random Processes",
            "18B11EC213": "Digital Systems",
            "15B11CI411": "Algorithms and Problem Solving",
            "15B11GE301": "Environmental Science",
            "18B15EC213": "Digital Systems Lab",
            "15B17CI471": "Algorithms and Problem Solving Lab",
            "15B11HS111": "Life Skills",
            "15B11CI313": "Computer Organisation and Architecture",
            "15B19CI591": "Minor Project – 1",
            "15B17CI373": "Computer Organisation and Architecture Lab",
            "15B17CI472": "Operating Systems and Systems Programming Lab",
            "15B17CI575": "Open Source Software lab",
            "15B11CI412": "Operating Systems and Systems Programming",
            "15B17CI576": "Information Security Lab",
            "18B12HS311": "Indian Constitution & Traditional Knowledge",
            "18B11CS311": "Computer Networks and Internet of Things",
            "18B15CS311": "Computer Networks and Internet of Things Lab",
            "15B19CI691": "Minor Project-2",
            "15B11CI513": "Software Engineering OR Artificial Intelligence",
            "15B11CI514": "Software Engineering OR Artificial Intelligence",
            "15B17CI573": "Software Engineering Lab OR Artificial Intelligence Lab",
            "15B17CI574": "Software Engineering Lab OR Artificial Intelligence Lab",
            "15B19CI791": "Major Project Part-1",
            "15B19CI793": "Summer Training Viva",
            "15B19CI891": "Major Project Part-2",
        },
        {
            "15B11MA111": "Mathematics-1",
            "15B11PH111": "Physics-1",
            "15B17PH171": "Physics Lab-1",
            "15B11CI111": "Software Development Fundamentals-I",
            "24B15CS111": "Software Development Fundamentals Lab-I",
            "24B11EC111": "Basic Electronics",
            "24B15EC111": "Basic Electronics Lab",
            "15B11HS112": "English",
            "18B15GE112": "Workshop",
            "15B11MA211": "Mathematics-2",
            "15B11PH211": "Physics-2",
            "15B17PH271": "Physics Lab-2",
            "15B11CI121": "Software Development Fundamentals-II",
            "24B15CS121": "Software Development Fundamentals Lab-II",
            "24B16HS111": "Life Skills & Professional Communication Lab",
            "18B15GE111": "Engineering Drawing & Design",
            "24B11HS111": "Universal Human Values (UHV)",
            "24B11CS212": "Theory of Computation",
            "15B11CI311": "Data Structures",
            "15B17CI371": "Data Structures Lab",
            "24B11CS213": "Database Management Systems",
            "24B15CS213": "Database Management Systems Lab",
            "24B15CS214": "Unix Programming Lab",
            "24B15CS215": "Object Oriented Programming using Java",
            "15B11HS211": "Economics",
            "24B17CS211": "Summer Training-I (4 weeks)",
            "24B11CS221": "Design and Analysis of Algorithms",
            "24B15CS221": "Design and Analysis of Algorithms Lab",
            "24B11CS222": "Artificial Intelligence and Machine Learning",
            "24B15CS222": "Artificial Intelligence and Machine Learning Lab",
            "24B11CS223": "Software Engineering",
            "19B13BT211": "Environmental Studies",
            "24B11CS312": "Operating Systems",
            "24B15CS312": "Operating Systems Lab",
            "24B11CS313": "Computer Networks",
            "24B15CS313": "Computer Networks Lab",
            "24B15CS314": "Full Stack Development Lab",
            "18B12HS311": "Indian Constitution & Traditional Knowledge",
            "24B17CS311": "Summer Training-II (6 weeks)",
            "24B11CS321": "Web Technology",
            "24B15CS321": "Web Technology Lab",
            "24B11CS322": "Advanced Data Structures and Algorithms",
            "24B15CS322": "Advanced Data Structures and Algorithms Lab",
            "24B11CS323": "Distributed and Cloud Computing OR Information Security and Cryptography",
            "24B11CS324": "Distributed and Cloud Computing OR Information Security and Cryptography",
            "24B15HS311": "Soft Skill For Employability",
            "24B17CS312": "Minor Project",
            "15B19CI791": "Major Project Part – 1",
            "24B17CS411": "Summer Training - III (6 weeks)",
            "15B19CI891": "Major Project Part – 2",
        },
    ]
    curr = {}
    for courses in courses_years:
        for k, v in courses.items():
            # 15B19CI891 B19CI891 19CI891 CI891
            curr.update({k: v, k[2:]: v, k[3:]: v, k[5:]: v})

    return curr


def curriculum():
    return {"electives": generate_electives(), "courses": generate_courses()}


if __name__ == "__main__":
    e = curriculum()
    with open("curriculum.json", "w+") as f:
        json.dump(e, f)

import json
import os
import sys

import color

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print(color.FAIL + "THIS IS NOT THE MAIN PY FILE" + color.ENDC)
    sys.exit()

lang = any
messages = any

color_replacements = {
    "(R)": f"{color.ENDC}",
    "(PINK)": f"{color.HEADER}",
    "(BLUE)": f"{color.OKBLUE}",
    "(GRAY)": f"{color.GRAY}",
    "(CYAN)": f"{color.OKCYAN}",
    "(GREEN)": f"{color.OKGREEN}",
    "(YELLOW)": f"{color.WARNING}",
    "(RED)": f"{color.FAIL}",
    "(B)": f"{color.BOLD}",
    "(U)": f"{color.UNDERLINE}",
}


def loadLangFile(code):
    global lang, messages
    try:
        with open(f"lang/logs_{code}.json", "r") as file:
            langFile = json.load(file)
    except FileNotFoundError:
        print(color.FAIL + f"File lang/logs_{code}.json not found" + color.ENDC)
        sys.exit()
    try:
        with open(f"lang/messages_{code}.json", "r") as file:
            MessageslangFile = json.load(file)
    except FileNotFoundError:
        print(color.FAIL + f"File lang/messages_{code}.json not found" + color.ENDC)
        sys.exit()
    messages = MessageslangFile
    lang = langFile


def parse(code, reference):
    global lang
    x = 0
    string = lang[code]
    replacements = {}
    for i in reference:
        replacements[f"[{x}]"] = i
        x += 1
    for old, new in replacements.items():
        string = string.replace(old, str(new))
    for old, new in color_replacements.items():
        string = string.replace(old, new)
    return string + color.ENDC


def message_parse(code):
    global messages
    string = messages[code]
    return string

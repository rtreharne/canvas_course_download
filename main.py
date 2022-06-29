#!bin/python3
import argparse
import os
import re

from pathvalidate import sanitize_filename
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist
from canvasapi.file import File
from canvasapi.module import Module, ModuleItem

def limit_string_length(string):
    if len(string) <= 128:
        return string
    else:
        return string[:128]

def extract_files(text):
    text_search = re.findall("/files/(\\d+)", text, re.IGNORECASE)
    groups = set(text_search)
    return groups


def get_course_files(course):
    modules = course.get_modules()

    files_downloaded = set()  # Track downloaded files for this course to avoid duplicates

    for module in modules:
        module: Module = module
        module_items = module.get_module_items()
        for item in module_items:
            item: ModuleItem = item

            try:
                path = f"{output}/" \
                       f"{sanitize_filename(course.name)}/" \
                       f"{sanitize_filename(module.name)}/"
            except Exception as e:
                print(e)
                continue
            if not os.path.exists(path):
                os.makedirs(path)

            item_type = item.type
            print(f"{course.name} - "
                  f"{module.name} - "
                  f"{item.title} ({item_type})")

            if item_type == "File":
                file = canvas.get_file(item.content_id)
                files_downloaded.add(item.content_id)
                file.download(path + sanitize_filename(file.filename))
            elif item_type == "Page":
                page = course.get_page(item.page_url)
                try:
                    with open(path + sanitize_filename(limit_string_length(item.title)).replace("/", "") + ".html", "w", encoding="utf-8") as f:
                        f.write(page.body or "")
                except:
                    continue
                files = extract_files(page.body or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename))
                    except ResourceDoesNotExist:
                        pass
            elif item_type == "ExternalUrl":
                url = item.external_url
                try:
                    with open(path + sanitize_filename(limit_string_length(item.title).replace("/", "")) + ".url", "w") as f:
                        f.write("[InternetShortcut]\n")
                        f.write("URL=" + url)
                except:
                    continue
            elif item_type == "Assignment":
                assignment = course.get_assignment(item.content_id)
                with open(path + sanitize_filename(limit_string_length(item.title)).replace("/", "") + ".html", "w", encoding="utf-8") as f:
                    f.write(assignment.description or "")
                files = extract_files(assignment.description or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename).replace("/", ""))
                    except ResourceDoesNotExist:
                        pass

    try:
        files = course.get_files()
        for file in files:
            file: File = file
            if not file.id in files_downloaded:
                print(f"{course.name} - {file.filename}")
                path = f"{output}/{sanitize_filename(course.name)}/" \
                       f"{sanitize_filename(file.filename)}"
                file.download(path)
    except Unauthorized:
        pass


if __name__ == "__main__":
    API_KEY = input("Enter your Canvas API token: ")
    output = input("Enter your save destination, e.g. 'output/': ")
    courses = input("Enter course ids as a comma separated list. E.g. 45263,98652. Or leave blank to default to courses listed in 'courses.py' file: ")
    #parser = argparse.ArgumentParser(description="Download all content from Canvas")
    #parser.add_argument("output")
    #parser.add_argument("courses", help="Comma-separated course IDs or 'all'", nargs="?", const="all")
    #parser.add_argument("api_key")
    #args = parser.parse_args()

    # Handle args
    #output = args.output.rstrip("/") + "/"

    if courses is None:
        courses = "file"
        courses = []  # courses to scrape
        print("No courses specified. Scraping all courses from courses.py")

    API_URL = "https://liverpool.beta.instructure.com"

    canvas = Canvas(API_URL, API_KEY)



    # Select courses to scrape, default to all
    if courses != "file":

        ids = courses.split(",")
        courses = []
        for id in ids:
            courses.append(canvas.get_course(int(id)))
    else:
        from courses import course_dict
        for key in course_dict:
            print([x for x in course_dict[key]])
            courses.extend([canvas.get_course(x) for x in course_dict[key]])

    # Perform scrape

    for course in courses:
        print(course)
        course: Course = course
        get_course_files(course)
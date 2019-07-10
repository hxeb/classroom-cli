#!/user/bin/env python3
"""
    - Read class registration info from db
    - Read classrooms from google
    - Create new and delete stale ones
"""

import config
from lib.database import Database
from lib.classroom import Classroom


def main():
    classes = fetch_classes_from_hxeb()
    course_payloads = build_course_payload(classes)
    classroom = Classroom()

    for payload in course_payloads:
        classroom.create_course(payload)


def fetch_classes_from_hxeb():

    db = Database(config)
    cursor = db.cursor()

    sql = """
    SELECT * FROM Classes
    WHERE Status = 'Active'
    AND CreateOn > '2019-01-01'
    """
    classes = db.read_sql(sql)
    return classes


def build_course_payload(classes):
    for class_ in classes:
        class_id = class_['ClassID']
        payload = {
            'name': class_['ClassNameCn'].strip(),
            'section': '2019',
            # 'room': '301',
            'ownerId': 'me',
            'courseState': 'PROVISIONED',
        }
        if class_['ClassNameEn']:
            payload['descriptionHeading'] = class_['ClassNameEn']
        if class_['Description']:
            payload['description'] = class_['Description']

        yield payload


if __name__ == '__main__':
    main()

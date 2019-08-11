"""
Python wrapper of google classroom API
https://developers.google.com/classroom/
https://developers.google.com/classroom/quickstart/python?authuser=3
"""

import pickle
import os.path
import json
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Classroom:

    def __init__(self):
        self._service = get_google_classroom_service()

    def create_course(self, payload):
        """
        payload = {
            'id': 'class id'
            'name': '10th Grade Biology',
            'descriptionHeading': 'english class name',
            'description': '''description''',
            'section': '2019',
            'room': '301',
            'ownerId': 'me',
            'courseState': 'PROVISIONED'
        }
        """
        course = self._service.courses().create(body=payload).execute()
        return course.get('id')

    def patch_course(self, id, payload):
        """
        :param id: either google course id or alias
        """
        course = self._service.courses().patch(
            id=id,
            updateMask='name,section,room,description',
            body=payload
        ).execute()
        return course

    def list_courses(self):
        results = self._service.courses().list().execute()
        return results.get('courses', [])

    def get_course(self, id):
        course = self._service.courses().get(id=id).execute()
        teachers = self._service.courses().teachers().list(courseId=id).execute()
        students = self._service.courses().students().list(courseId=id).execute()
        return Course(course, students=students, teachers=teachers)

    def delete_course(self, id):
        """Can only delete courseState=ARCHIVED courses"""
        self._service.courses().delete(id=id).execute()
        print(f'Course ID {id} deleted')

    def archive_course(self, id):
        course = self._service.courses().patch(
            id=id,
            updateMask='courseState',
            body={'courseState': 'ARCHIVED'}
        ).execute()
        print(f'Course {course["id"]} {course["name"]} ARCHIVED')
        return course

    def change_course_state(self, id, state):
        course = self._service.courses().patch(
            id=id,
            updateMask='courseState',
            body={'courseState': state}
        ).execute()
        print(f'Course {course["id"]} {course["name"]} {state}')
        return course

    def sync_course(self, payload):
        alias_id = payload['id']
        name = payload['name']
        try:
            course = self.get_course(alias_id)
        except Exception:
            course = None

        if not course:
            print(f'Course {alias_id} {name} not found. Creating...')
            self.create_course(payload)
        else:
            print(f'Course {alias_id} {name} exists, updating...')
            self.patch_course(alias_id, payload)

    def list_teachers(self, course_id):
        results = self._service.courses().teachers().list(courseId=course_id).execute()
        return results.get('teachers', [])

    def list_students(self, course_id):
        results = self._service.courses().students().list(courseId=course_id).execute()
        return results.get('students', [])

    def add_teacher(self, course_id, teacher):
        body = {
            'userId': teacher,
            'courseId': course_id,
            'role': 'TEACHER'
        }
        try:
            inv = self._service.invitations().create(body=body).execute()
            print(f'Teacher {teacher} was invited to the course with ID {course_id}')
        except errors.HttpError as e:
            error = json.loads(e.content).get('error')
            if(error.get('code') == 409):
                print(f'User "{teacher}" is already a member of this course.')
            else:
                print('ERROR: ', error['message'])

    def delete_teacher(self, course_id, teacher):

        teacher_white_list = [
            'hxebclassroom@gmail.com',
            'regadmin@hxeb.org',
            'dean@hxeb.org',
            'principal@hxeb.org',
        ]

        if teacher in teacher_white_list:
            print(f'Teacher {teacher} is in white list.')
            return

        try:
            self._service.courses().teachers().delete(
                courseId=course_id, userId=teacher).execute()
            print(f'Teacher {teacher} was deleted from the course with ID {course_id}')
        except errors.HttpError as e:
            error = json.loads(e.content).get('error')
            if(error.get('code') == 409):
                print(f'User "{teacher}" is not a teacher of this course.')
            else:
                raise

    def delete_teachers(self, course_id, teachers):
        for teacher in teachers:
            self.delete_teacher(course_id, teacher)

    def add_student(self, course_id, student):
        body = {
            'userId': student,
            'courseId': course_id,
            'role': 'STUDENT'
        }
        try:
            inv = self._service.invitations().create(body=body).execute()
            print(f'Student {student} was invited to the course with ID {course_id}')
        except errors.HttpError as e:
            error = json.loads(e.content).get('error')
            if(error.get('code') == 409):
                print(f'User "{student}" is already a member of this course.')
            else:
                print('ERROR: ', error['message'])

    def add_students(self, course_id, students):
        for student in students:
            self.add_student(course_id, student)

    def delete_student(self, course_id, student):
        try:
            self._service.courses().students().delete(
                courseId=course_id, userId=student).execute()
            print(f'Student {student} was deleted from the course with ID {course_id}')
        except errors.HttpError as e:
            error = json.loads(e.content).get('error')
            if(error.get('code') == 409):
                print(f'User "{student}" is not a student of this course.')
            else:
                raise

    def delete_students(self, course_id, students):
        for student in students:
            self.delete_student(course_id, student)


class Course:
    """
    https://developers.google.com/classroom/guides/manage-courses
    """

    def __init__(self, course, teachers=None, students=None):
        self._course = course
        self.teachers = teachers
        self.students = students
        # self.invitations = invitations
        self.name = course.get('name')
        self.id = course.get('id')

    def add_teacher(self):
        pass

    def add_student(self):
        pass


def get_google_alias_of_org_class(season_id, class_id):
    return f'p:hexb-{season_id}-{class_id}'


def get_google_classroom_service():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses',
        'https://www.googleapis.com/auth/classroom.rosters',
        'https://www.googleapis.com/auth/classroom.coursework.students',
        'https://www.googleapis.com/auth/classroom.profile.emails',
    ]
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)

    # # Call the Classroom API
    # results = service.courses().list(pageSize=10).execute()
    # courses = results.get('courses', [])

    return service

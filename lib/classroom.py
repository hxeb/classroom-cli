"""
Python wrapper of google classroom API
https://developers.google.com/classroom/
https://developers.google.com/classroom/quickstart/python?authuser=3
"""

import pickle
import os.path
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

    def list_courses(self):
        results = self._service.courses().list().execute()
        return results.get('courses', [])

    def get_course(self):
        course = service.courses().get(id=course_id).execute()
        return Course(course)


class Course:
    """
    https://developers.google.com/classroom/guides/manage-courses
    """

    def __init__(self, course):
        self._course = course
        self.name = course.get('name')
        self.id = course.get('id')

    def add_teacher(self):
        pass

    def add_student(self):
        pass


def get_google_classroom_service():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/classroom.courses']
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

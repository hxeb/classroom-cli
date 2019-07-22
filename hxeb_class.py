#!/user/bin/env python3
"""
    - Read class registration info from db
    - Read classrooms from google
    - Create new and delete stale ones
"""
import pprint
import click

import config
from lib.database import Database
from lib.classroom import Classroom, get_google_alias_of_org_class


@click.group()
def cli():
    pass


@cli.command()
def list_google_courses():
    """data from google classroom"""
    courses = Classroom().list_courses()
    click.echo('\tGoogle Course ID\tState\tName')
    for i, c in enumerate(courses, 1):
        id = c['id']
        name = c['name']
        state = c['courseState']
        click.echo(f'{i}\t{id}\t{state}\t{name}')
    click.echo('Help: run "hxebclass describe-google-course --id=id" to see google course details.' )


@cli.command()
@click.option('--id', help='Google Course ID')
def describe_google_course(id):
    course = Classroom().get_course(id=id)
    click.echo(pprint.pprint(course._course))
    click.echo(pprint.pprint(course.teachers))
    click.echo(pprint.pprint(course.students))
    # click.echo(pprint.pprint(course.invitations))


@cli.command()
def list_org_courses():
    """Data from hxeb.org"""
    courses = fetch_classes_from_hxeb()
    click.echo('\tClass ID\tSeason\tName')
    for i, c in enumerate(courses, 1):
        id = c['ClassId']
        season = c['SeasonNameCn']
        name = c['ClassNameCn']
        click.echo(f'{i}\t{id}\t{season}\t{name}')
    # click.echo('Help: run "hxebclass describe-google-course --id=id" to see google course details.' )


@cli.command()
@click.option('--id', help='Course ID')
@click.option('--all', default=False, is_flag=True, help='Delete all google courses')
@click.option('--force', default=False, is_flag=True, help='Delete course regardless the course state')
def delete_google_course(id, all, force):
    cr = Classroom()
    if id:
        if force:
            cr.archive_course(id=id)
        cr.delete_course(id=id)
    else:
        if all:
            print('Deleting all courses')
            courses = cr.list_courses()
            for c in courses:
                id = c['id']
                if force:
                    cr.archive_course(id=id)
                cr.delete_course(id=id)


@cli.command()
@click.option('--id', required=True, help='Course ID')
@click.option('--state', required=True, type=click.Choice(['ACTIVE', 'ARCHIVED']))
def change_google_course_state(id, state):
    Classroom().change_course_state(id=id, state=state)


@cli.command()
@click.option('--id', help='Course ID')
@click.option('--all', default=False, is_flag=True, help='Sync all courses')
@click.option('--sync_teacher', default=False, is_flag=True, help='Sync Teacher')
@click.option('--sync_student', default=False, is_flag=True, help='Sync Students')
def sync(id, all, sync_teacher, sync_student):
    """Syncing org courses to google courses
    - create new
    - delete stale
    - update teacher and students
    """
    cr = Classroom()
    if id:
        courses = fetch_classes_from_hxeb(class_id=id)
    elif all:
        courses = fetch_classes_from_hxeb()
    else:
        return

    payloads = build_course_payload(courses)
    for c in payloads:
        cr.sync_course(c)
        if sync_teacher:
            sync_teachers(id) # use hxeb.org class id here
        if sync_student:
            print('Syncing students')



@cli.command()
@click.option('--id', help='Course ID')
def archive_google_course(id):
    Classroom().archive_course(id=id)


def sync_teachers(class_id):
    """
    :param class_id: hxeb.org class id
    """
    # new_teacher = get_org_teacher(class_id)
    new_teacher = 'zhuang1316@gmail.com'

    alias_id = get_google_alias_of_org_class(config.SEASON_ID, class_id)
    cr = Classroom()
    old_teachers = cr.list_teachers(alias_id)
    old_teachers = [t['profile']['emailAddress'] for t in old_teachers]

    del_teachers = [t for t in old_teachers if t != new_teacher]
    cr.delete_teachers(alias_id, del_teachers)
    cr.add_teacher(alias_id, new_teacher)


def main():
    classes = fetch_classes_from_hxeb()
    course_payloads = build_course_payload(classes)
    classroom = Classroom()

    for payload in course_payloads:
        classroom.create_course(payload)


def fetch_classes_from_hxeb(class_id=None):

    db = Database(config)
    cursor = db.cursor()

    sql = """
    SELECT a.ArrangeID
        ,c.ClassId
        ,a.SeasonId
        ,s.SeasonNameCn
        ,c.ClassNameCn
        ,c.ClassNameEn
        ,c.Description
        ,cr.RoomNo
        ,c.TypeId
        ,t.TypeNameCn
        ,fwt.Fee AS TuitionW_J
        ,Tuition_W
        ,fwb.Fee AS BookFeeW_J
        ,BookFee_W
        ,SpecialFee_W
        ,fht.Fee AS TuitionH_J
        ,Tuition_H
        ,fhb.Fee AS BookFeeH_J
        ,BookFee_H
        ,SpecialFee_H
    FROM Arrangement a
    INNER JOIN Classes c ON a.ClassID = c.ClassID
    INNER JOIN Seasons s ON a.SeasonID = s.SeasonID
    LEFT JOIN Classrooms cr ON a.RoomID = cr.RoomID
    Left join ClassType t ON c.TypeId = t.TypeId
    LEFT JOIN Fee fwt ON a.TuitionWID = fwt.FeeID
    LEFT JOIN Fee fht ON a.TuitionHID = fht.FeeID
    LEFT JOIN Fee fwb ON a.BookFeeWID = fwb.FeeID
    LEFT JOIN Fee fhb ON a.BookFeeHID = fhb.FeeID
    WHERE a.SeasonId = {season_id}
    AND ActiveStatus = 'Active'
    """.format(season_id=config.SEASON_ID)

    if class_id:
        sql += f'\nAND c.ClassId = {class_id}'
    classes = db.read_sql(sql)
    return classes


def build_course_payload(classes):
    for class_ in classes:
        class_id = class_['ClassId']
        season_id = class_['SeasonId']
        alias = get_google_alias_of_org_class(season_id, class_id)
        payload = {
            'id': alias,
            'name': class_['ClassNameCn'].strip(),
            'section': class_['SeasonNameCn'].strip(),
            'room': class_['RoomNo'],
            'ownerId': 'me',
            'courseState': 'PROVISIONED',
        }
        # if class_['ClassNameEn']:
        #     payload['descriptionHeading'] = class_['ClassNameEn']
        if class_['Description']:
            payload['description'] = class_['Description']  # class hours

        yield payload

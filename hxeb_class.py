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
    org_courses = fetch_classes_from_hxeb()
    org_course_names = [c['ClassNameCn'].strip() for c in org_courses ]
    courses = Classroom().list_courses()
    courses = sorted(courses, key=lambda x: x['name'])
    click.echo('\tGoogle Course ID\tCode\tState\tName')
    for i, c in enumerate(courses, 1):
        id = c['id']
        name = c['name'].strip()
        state = c['courseState']
        code = c['enrollmentCode']
        if name not in org_course_names:
            click.echo(f'{i}\t{id}\t{code: <10}\t{state}\t{name}\tSTALE')
        else:
            click.echo(f'{i}\t{id}\t{code: <10}\t{state}\t{name}')
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
    courses = sorted(fetch_classes_from_hxeb(), key=lambda x: x['ClassNameCn'])
    click.echo('\tClass ID\tSeason\tTeacher\tName')
    for i, c in enumerate(courses, 1):
        id = c['ClassId']
        season = c['SeasonNameCn']
        name = c['ClassNameCn']
        teacher = c['teacher_email'] if c['teacher_email'] else ''
        click.echo(f'{i}\t{id}\t{season}\t{teacher: <30}\t{name}')
    # click.echo('Help: run "hxebclass describe-google-course --id=id" to see google course details.' )


@cli.command()
def list_org_registrations():
    registrations = sorted(fetch_class_registrations_from_hxeb(), key=lambda x: x['ClassNameCn'])
    click.echo('\tClass ID\tSeason\tEmail\tStudent')
    for i, c in enumerate(registrations, 1):
        id = c['ClassId']
        season = c['SeasonNameCn']
        name = c['ClassNameCn']
        student_name_cn = c['StudentNameCn'] if c['StudentNameCn'] else ''
        student_name_en = c['StudentNameEn'] if c['StudentNameEn'] else ''
        family_email = c['FamilyEmail']
        click.echo(f'{i}\t{id}\t{season}\t{student_name_cn}\t{student_name_en: <15}\t{family_email: <25}\t{name: <50}')


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
    if not any([id, all]):
        click.echo('Must pass either --all or --id')

    cr = Classroom()
    if id:
        courses = fetch_classes_from_hxeb(class_id=id)
    elif all:
        courses = fetch_classes_from_hxeb()
    else:
        return

    payloads = build_course_payload(courses, extra=True)
    for c in payloads:
        extra = c.pop('extra')
        cr.sync_course(c)
        if sync_teacher:
            sync_teachers(extra['teacher_email'], extra['alias']) # use hxeb.org class id here
        if sync_student:
            print('Syncing students')



@cli.command()
@click.option('--id', help='Course ID')
def archive_google_course(id):
    Classroom().archive_course(id=id)


def sync_teachers(new_teacher, alias_id):
    """
    :param new_teacher: email
    :param alias: class alias
    """

    whitelist = ['hxebclassroom@gmail.com']
    if not new_teacher or not '@' in new_teacher:
        click.echo(f'No teacher found for class alias {alias_id}')
        return

    new_teacher = new_teacher.strip()
    cr = Classroom()
    # get current teachers in google course
    old_teachers = cr.list_teachers(alias_id)
    old_teachers = [t['profile']['emailAddress'] for t in old_teachers]

    # remove teachers that don't exist in org course anymore
    del_teachers = [t for t in old_teachers if t != new_teacher and t not in whitelist]
    if del_teachers:
        print('Removing teacher', del_teachers)
        # cr.delete_teachers(alias_id, del_teachers)
    # add new teacher if they are not in google course already
    if new_teacher not in old_teachers:
        print('Inviting teacher', new_teacher)
        # cr.add_teacher(alias_id, new_teacher)


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
        ,te.email AS teacher_email
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
    LEFT JOIN Teacher te ON a.TeacherID = te.TeacherID
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


def build_course_payload(classes, extra=False):
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
        if extra:
            # keep some extra info
            payload['extra'] = {}
            payload['extra']['teacher_email'] = class_['teacher_email']
            payload['extra']['alias'] = alias

        yield payload


def fetch_class_registrations_from_hxeb():
    db = Database(config)
    cursor = db.cursor()

    sql = """
    SELECT a.ArrangeID
        ,c.ClassId
        ,a.SeasonId
        ,te.email AS TeacherEmail
        ,s.SeasonNameCn
        ,c.ClassNameCn
        ,c.ClassNameEn
        ,st.NameCn AS StudentNameCn
        ,st.NameFirstEn + ' ' + st.NameLastEn AS StudentNameEn
        ,f.email AS FamilyEmail
    FROM Arrangement a
    INNER JOIN Classes c ON a.ClassID = c.ClassID
    INNER JOIN Seasons s ON a.SeasonID = s.SeasonID
    INNER JOIN ClassRegistration cr ON a.ClassID = cr.ClassID AND a.SeasonID = cr.SeasonID
    LEFT JOIN Teacher te ON a.TeacherID = te.TeacherID
    LEFT JOIN Student st ON cr.StudentID = st.StudentID
    LEFT JOIN Family f ON cr.FamilyID = f.FamilyID
    Left join ClassType t ON c.TypeId = t.TypeId
    WHERE a.SeasonId = {season_id}
    AND ActiveStatus = 'Active'
    """.format(season_id=config.SEASON_ID)

    registrations = db.read_sql(sql)
    return registrations

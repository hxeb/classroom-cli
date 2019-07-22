# Quick Start - macos

1. install python3

2. create virtualenv

3. `brew install freetds`

4. `git clone https://github.com/hxeb/hxeb-scripts.git`

5. `pip install hxeb-scripts`

## Usages

List all google classroom courses
```
hxebclass list-google-courses
```

Show details of a google classroom course by id  
It will show course details, plus teachers and students
```
hxebclass describe-google-course --id=<id from list-google-courses>
```

List all hxeb.org classes
It is now hard coded for season 48 (2019 Fall)
```
hxebclass list-org-courses
```

Sync (auto create if not exists) one class from hxeb.org to google classroom
It is now hard coded for season 48 (2019 Fall)
```
hxebclass sync --id=<id from list-org-courses>
```

`Alias` is the unique indentifier for mapping hxeb.org class to google classroom course.  
It follows format `p:<season_id>-<class_id>`


## TODO
- update teachers list per course
- update students list per course

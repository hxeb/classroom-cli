# Quick Start

## Installation

1. install [miniconda](https://docs.conda.io/en/latest/miniconda.html), any version

2. create python3.7 virtualenv with conda
```
conda create -n classroom-cli python=3.7
```

3. activate virtualenv
```
conda activate classroom-cli
```

4. `brew install freetds` for mssql db connection, this is for MacOS only

5. `git clone https://github.com/hxeb/hxeb-scripts.git`

6. `pip install hxeb-scripts`

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
- update students list per course

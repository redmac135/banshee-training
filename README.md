# Banshee Training App

## About

Stack: Django, Django REST Api, MySQL

Made for 778 Banshee Squadron, this app assigns training, allows for easy movement of scheduled lessons, and the assignment of instructors to lessons. There are 3 different type of general users: 
- Officers: which can see all lessons and assignments, but cannot directly edit the lesson assignments
- Training Staff: create, edit, and delete assignments.
- Instructors: Can submit lesson plans to their own lesson and have a list of upcoming lesson assignments

## Deployment

Delete Test View and it's reference in urls.py
However keep training/example.html to ensure purgecss does not get rid of nesscary classes

Install requirements
```bash
pip install -r requirements.txt
```

Start dev server
```bash
cd banshee
python manage.py runserver
```

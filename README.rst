Pre Paid Autorefill Service

The system that lets you refill Pre-Paid phones on demand and on a schedule.

Start working
=============

1. Clone project from repository to your local machine:
2. Create database named 'ppars_b' on MySQL
3. Run sql script under ~/path_to_project_folder/ppars/sql (pparsb.sql) with MySQL to initialize created database with data
4. Rename settings_local.py.default to settings_local.py under ~/path_to_project_folder/ppars/ppars/settings
5. Change configs in settings_local.py according to your database
6. Create virualenv and activate it (make sure to use Python 2):
    $ virtualenv pparsenv
    $ source ~/path_to_pparsenv_folder/pparsenv/bin/activate
7. Install requirements:
    $ pip install -r requirements.txt
8. Run migrations to update database according to latest state of models:
    $ python manage.py migrate
9. Install encrypted lib:
    $ pip install django-encrypted-fields
10. Create a basic keyczar keyset. AES-256 in this case:
    $ mkdir fieldkeys
    $ keyczart create --location=fieldkeys --purpose=crypt
    $ keyczart addkey --location=fieldkeys --status=primary --size=256
11. Install gadjo:
    $ easy_install django-contrib-requestprovider
12. Start your local server:
    $ python manage.py runserver


Create admin user
=================

1. $ python manage.py createsuperuser

How to migrate database
=======================

Migrate
-------

$ python manage.py migrate <app_name> <migration_number> (<app_name> is optional, without it it will migrate all apps. <migration_number> is optional, in case you want to migrate backwards)

Create new migration (to alter tables in MySQL db)
--------------------------------------------------

$ python manage.py schemamigration <app_name> --auto

Create new data migration (to do something with data in MySQL db)
-----------------------------------------------------------------

$ python manage.py datamigration <app_name> <short_description>



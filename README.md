```
Note: Throughout this README, "automatically generated" and "automatically created" are referenced frequently due to the way Django works. "Automatically generated" refers to files that Django creates and writes all the code. We did not need to write any of the code. "Automatically created" means that Django created the file and a base to start, but the team had to write the code in the file if we chose to change it.
```

# 403-PHARMACY-SYSTEM
This folder holds all the code for our project. This includes djangoApp, .gitignore, pharmacy_info.py, README.md, and TODO.md. .gitignore, README.md, and TODO.md are automatically created by Git. We used .gitignore to set Git to ignore certain files that we did not want added to our repository such as virtual environments. The README.md file, this file, outlines all the files in our repository. We did not use TODO.md. pharmacy_info.py stores all the information for the pharmacy such as the name, phone number, and hours.

## djangoApp
This folder holds all the app code for our project including pharmacySystem, webApp, db.sqlite3, manage.py, and requirements.txt. db.sqlite3 creates our database in SQLite 3. manage.py is automatically created, but we did not make any changes. We use this file to run our project, make changes to the database, and access the database manually. requirements.txt includes all the programs for this project, which is just Django.

### pharmacySystem
This folder contains __init__.py, asgi.py, settings.py, urls.py, and wsgi.py. These files were automatically created by Django when the backend is created. __pycache__ is automatically generated. We did not change anything in the __pycache__, __init__.py, asgi.py, or wsgi.py files. We used the settings.py and urls.py files extensively. settings.py holds all the settings for the project. We used it to run Axes middleware for account locking, crispy_forms and crispy_bootstrap4 for communication with the frontend, and other various backend settings. urls.py holds all the urls for the project. It connects the API view to a URL. 

### webApp
This folders holds the content for our project including __pycache__, migrations, static, templates, __init__.py, admin.py, apps.py, forms.py, models.py, signals.py, tests.py, utils.py, and views.py. __pycache__ is automatically generated, and we did not change it. Under the folders listed below, there is are __init__.py, admin.py, apps.py, forms.py, models.py, signals.py, tests.py, utils.py, and views.py files, which are also all automatically created. We did not change __init__.py, apps.py, or tests.py but we used all the other files. admin.py allowed us to change the Django admin view, which we used to create our users. forms.py defined the forms used to collect information from the frontend and transfer to the backend. models.py defined our database tables. signals.py allowed certain events to trigger functions to run. utils.py allows us to add helpful functions that are used throughout our project. For example, the is_user function is used as a decorator for our API views to define user permissions. views.py holds all our API views. Each function is a different API.

#### migrations
This folder holds all the changes to the database. Django automatically generates these migration files to manage the changes to the database. We have 10 migration files. __pycache__ and __init__.py are also automatically created, but we do not use them.

#### static
This folder holds design elements for the frontend such as images in the images folder and css files in the webApp folder. The homepage.png is the picture shown on our home page. The global.css and main.css files dictate the base styling for the frontend website.

#### templates
This folder holds all the HTML files for our frontend pages. Each HTML is a separate page. There are two folders: users and webApp. There is no system to determine where our HTMLs are held, but most of them are in the users folder.

## How to build and run
### Requirements
Before you begin, ensure you have the following installed on your machine:
- Python 3.12
- pip (Python package manager)

### Installation
Run the following commands:

- Install all the dependencies and frameworks

```pip install -r requirements.txt```

- Switch to django directory

```cd djangoApp```

- Create the database

```python manage.py migrate```

- Run the server

```python manage.py runserver ```

The server should be running on localhost:8080
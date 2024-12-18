from school_system.wsgi import application
#指的是line bot專案中有wsgi.py，而我們的目的是要將wsgi.py內的application導入至main.py，GAE進入點從這裡開始

# App Engine by default looks for a main.py file at the root of the app
# directory with a WSGI-compatible object called app.
# This file imports the WSGI-compatible object of your Django app,
# application from mysite/wsgi.py and renames it app so it is discoverable by
# App Engine without additional configuration.
# Alternatively, you can add a custom entrypoint field in your app.yaml:
# entrypoint: gunicorn -b :$PORT mysite.wsgi
app = application
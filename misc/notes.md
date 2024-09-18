### Django basics
From: Django Tutorial on Django Project Website

## Models
each model has class variables that are instances of a field class

optional first position argument ("human readable name"), without this it will just use the machine name

Can define relationships using a class variable like ForeignKey(Other_Model)

    This shows that each instance of this class is related to exactly one of the Other Class
    Can do one-to-one, many-to-one, many-to-many (not sure how yet)

After creating the models for the first time, need to add "polls.apps.PollsConfig", to the installed apps in the settings.py of mysite

Model updating process:

    - Change your models (in models.py).
    - Run python3 manage.py makemigrations to create migrations for those changes
    - Run python3 manage.py migrate to apply those changes to the database.

Use this command to get into the interactive shell

    python3 manage.py shell
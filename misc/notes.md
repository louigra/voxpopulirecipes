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

Setting up the test client:

    $ python manage.py shell

    >>> from django.test.utils import setup_test_environment
    >>> setup_test_environment()

    >>> from django.test import Client
    >>> # create an instance of the client for our use
    >>> client = Client()

    >>> # get a response from '/'
    >>> response = client.get("/")
    Not Found: /
    >>> # we should expect a 404 from that address; if you instead see an
    >>> # "Invalid HTTP_HOST header" error and a 400 response, you probably
    >>> # omitted the setup_test_environment() call described earlier.
    >>> response.status_code
    404
    >>> # on the other hand we should expect to find something at '/polls/'
    >>> # we'll use 'reverse()' rather than a hardcoded URL
    >>> from django.urls import reverse
    >>> response = client.get(reverse("polls:index"))
    >>> response.status_code
    200
    >>> response.content
    b'\n    <ul>\n    \n        <li><a href="/polls/1/">What&#x27;s up?</a></li>\n    \n    </ul>\n\n'
    >>> response.context["latest_question_list"]
    <QuerySet [<Question: What's up?>]>

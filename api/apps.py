# what this file does: This file defines the configuration for the 'api' application in a Django project.
# The `ApiConfig` class inherits from `AppConfig`, which is a base class provided by Django for configuring
#  applications. The `name` attribute specifies the name of the application, which is 'api' in this case.
#  This configuration allows Django to recognize and manage the 'api' app within the project.
from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

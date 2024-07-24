import os
from typing import Any

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandParser
from django.contrib.auth.models import AbstractBaseUser


class Command(BaseCommand):
    """
    Create a superuser if none exist using environment variables.
    Example:
        manage.py createsuperuser_if_none_exists
    """

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--username", 
            default=os.environ.get("DJANGO_SUPERUSER_USERNAME"), 
            help="Username for the superuser"
        )
        parser.add_argument(
            "--password", 
            default=os.environ.get("DJANGO_SUPERUSER_PASSWORD"), 
            help="Password for the superuser"
        )
        parser.add_argument(
            "--email", 
            default=os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com"), 
            help="Email for the superuser"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        User: AbstractBaseUser = get_user_model()
        if User.objects.exists():
            self.stdout.write(self.style.WARNING('A user already exists. No new superuser created.'))
            return

        username: str = options["username"]
        password: str = options["password"]
        email: str = options["email"]

        if not username or not password:
            self.stdout.write(self.style.ERROR('Username and password must be provided either as arguments or environment variables.'))
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(f'Local superuser "{username}" was created'))

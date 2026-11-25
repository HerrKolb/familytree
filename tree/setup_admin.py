"""
Management Command: setup_admin
Erstellt ein FamilyProfile (Admin) für einen bestehenden Superuser.

Aufruf:
    python manage.py setup_admin --username=dein_username
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from tree.models import FamilyProfile


class Command(BaseCommand):
    help = 'Erstellt ein FamilyProfile (Admin-Rolle) für einen bestehenden Benutzer.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Benutzername des Superusers'
        )

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Benutzer "{username}" nicht gefunden.')

        profile, created = FamilyProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'admin'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✅ FamilyProfile (Admin) für "{username}" wurde erstellt.'
            ))
        else:
            profile.role = 'admin'
            profile.save()
            self.stdout.write(self.style.SUCCESS(
                f'✅ FamilyProfile für "{username}" auf Admin gesetzt.'
            ))

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='Vorname')),
                ('last_name', models.CharField(max_length=100, verbose_name='Nachname')),
                ('birth_name', models.CharField(blank=True, max_length=100, verbose_name='Geburtsname')),
                ('gender', models.CharField(
                    choices=[('M', 'Männlich'), ('F', 'Weiblich'), ('D', 'Divers'), ('U', 'Keine Angabe')],
                    default='U', max_length=1, verbose_name='Geschlecht')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Geburtsdatum')),
                ('birth_year_only', models.BooleanField(default=False, verbose_name='Nur Geburtsjahr bekannt')),
                ('birth_place', models.CharField(blank=True, max_length=200, verbose_name='Geburtsort')),
                ('death_date', models.DateField(blank=True, null=True, verbose_name='Sterbedatum')),
                ('death_place', models.CharField(blank=True, max_length=200, verbose_name='Sterbeort')),
                ('occupation', models.CharField(blank=True, max_length=200, verbose_name='Beruf')),
                ('notes', models.TextField(blank=True, verbose_name='Notizen')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='photos/', verbose_name='Foto')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_persons',
                    to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='person',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Benutzer-Account')),
            ],
            options={
                'verbose_name': 'Person',
                'verbose_name_plural': 'Personen',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(
                    choices=[
                        ('parent',   'Elternteil → Kind'),
                        ('partner',  'Partner / Ehepartner'),
                        ('sibling',  'Geschwister'),
                        ('adoptive', 'Adoptiv-Elternteil → Kind'),
                        ('half',     'Halbgeschwister'),
                    ],
                    max_length=20, verbose_name='Beziehungstyp')),
                ('note', models.CharField(blank=True, max_length=200, verbose_name='Anmerkung')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_person', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relationships_as_from',
                    to='tree.person',
                    verbose_name='Von Person')),
                ('to_person', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='relationships_as_to',
                    to='tree.person',
                    verbose_name='Zu Person')),
            ],
            options={
                'verbose_name': 'Beziehung',
                'verbose_name_plural': 'Beziehungen',
                'unique_together': {('from_person', 'to_person', 'relation_type')},
            },
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('email', models.EmailField(verbose_name='E-Mail-Adresse')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used', models.BooleanField(default=False, verbose_name='Verwendet')),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('invited_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='invitations',
                    to=settings.AUTH_USER_MODEL)),
                ('used_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='accepted_invitation',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Einladung',
                'verbose_name_plural': 'Einladungen',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FamilyProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('admin', 'Admin'), ('member', 'Familienmitglied')],
                    default='member', max_length=10, verbose_name='Rolle')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='family_profile',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Familienprofil',
                'verbose_name_plural': 'Familienprofile',
            },
        ),
    ]

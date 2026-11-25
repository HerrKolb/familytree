"""
Management Command: import_stammbaum

Spielt Personen und Beziehungen aus einem JSON-Export (manage.py dumpdata)
in die aktuelle Datenbank ein. Verknüpfungen zu Benutzerkonten
(Person.user, Person.created_by) werden dabei geleert, weil die Benutzer
neu über Authentik angelegt werden.

Aufruf:
    python manage.py import_stammbaum /import/personen.json
"""
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction

from tree.models import Person, Relationship

ERLAUBT = {'tree.person', 'tree.relationship'}


class Command(BaseCommand):
    help = 'Importiert Personen und Beziehungen aus einem dumpdata-JSON ohne Benutzerverknüpfungen.'

    def add_arguments(self, parser):
        parser.add_argument('datei', help='Pfad zur JSON-Datei aus dumpdata')
        parser.add_argument('--leeren', action='store_true',
                            help='Vorhandene Personen und Beziehungen vorher löschen')

    def handle(self, *args, **options):
        pfad = Path(options['datei'])
        if not pfad.exists():
            raise CommandError(f'Datei nicht gefunden: {pfad}')

        daten = json.loads(pfad.read_text(encoding='utf-8'))
        objekte = [o for o in daten if o.get('model') in ERLAUBT]
        uebersprungen = len(daten) - len(objekte)
        if not objekte:
            raise CommandError('Die Datei enthält keine Personen oder Beziehungen.')
        for o in objekte:
            if o['model'] == 'tree.person':
                o['fields']['user'] = None
                o['fields']['created_by'] = None

        if not options['leeren'] and (Person.objects.exists() or Relationship.objects.exists()):
            raise CommandError('Die Datenbank enthält schon Personen. '
                               'Mit --leeren werden sie vor dem Import gelöscht.')

        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(objekte, tmp, ensure_ascii=False)
            tmp_pfad = tmp.name

        with transaction.atomic():
            if options['leeren']:
                Relationship.objects.all().delete()
                Person.objects.all().delete()
            call_command('loaddata', tmp_pfad, verbosity=0)
            # Zähler (Sequenzen) an die importierten IDs anpassen, sonst
            # schlägt das Anlegen neuer Personen in PostgreSQL fehl.
            sql = connection.ops.sequence_reset_sql(no_style(), [Person, Relationship])
            with connection.cursor() as cursor:
                for statement in sql:
                    cursor.execute(statement)

        Path(tmp_pfad).unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(
            f'Importiert: {Person.objects.count()} Personen, '
            f'{Relationship.objects.count()} Beziehungen '
            f'({uebersprungen} andere Einträge übersprungen).'
        ))

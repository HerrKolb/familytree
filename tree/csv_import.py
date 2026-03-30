import csv
import io
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import Person


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV-Datei auswählen',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    encoding = forms.ChoiceField(
        label='Zeichenkodierung',
        choices=[('utf-8', 'UTF-8 (Standard)'), ('latin-1', 'Latin-1 / Windows')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='utf-8'
    )


# Mapping: CSV-Spaltenname → Modellfeld
FIELD_MAP = {
    'vorname':      'first_name',
    'nachname':     'last_name',
    'geburtsname':  'birth_name',
    'geschlecht':   'gender',
    'geburtsdatum': 'birth_date',
    'geburtsort':   'birth_place',
    'sterbedatum':  'death_date',
    'sterbeort':    'death_place',
    'beruf':        'occupation',
    'notizen':      'notes',
    # Englische Spaltenbezeichnungen ebenfalls akzeptieren
    'first_name':   'first_name',
    'last_name':    'last_name',
    'birth_name':   'birth_name',
    'gender':       'gender',
    'birth_date':   'birth_date',
    'birth_place':  'birth_place',
    'death_date':   'death_date',
    'death_place':  'death_place',
    'occupation':   'occupation',
    'notes':        'notes',
}

GENDER_MAP = {
    'm': 'M', 'männlich': 'M', 'male': 'M',
    'f': 'F', 'weiblich': 'F', 'female': 'F',
    'd': 'D', 'divers': 'D',
    '': 'U', 'u': 'U', 'keine angabe': 'U',
}

DATE_FORMATS = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y/%m/%d']


def parse_date(value):
    """Versucht ein Datum in verschiedenen Formaten zu parsen."""
    from datetime import datetime
    value = value.strip()
    if not value:
        return None
    # Nur Jahreszahl?
    if value.isdigit() and len(value) == 4:
        try:
            return datetime(int(value), 1, 1).date()
        except ValueError:
            return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


@login_required
def csv_import(request):
    if request.method == 'POST':
        form = CsvImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            encoding = form.cleaned_data['encoding']

            # Datei einlesen
            try:
                content = csv_file.read().decode(encoding)
            except UnicodeDecodeError:
                messages.error(request, 'Fehler beim Lesen der Datei. Bitte andere Zeichenkodierung wählen.')
                return render(request, 'tree/csv_import.html', {'form': form})

            reader = csv.DictReader(io.StringIO(content), delimiter=',')

            # Prüfen ob Semikolon als Trennzeichen verwendet wird (Excel-Export)
            if reader.fieldnames and len(reader.fieldnames) == 1:
                reader = csv.DictReader(io.StringIO(content), delimiter=';')

            created = 0
            skipped = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    kwargs = {'created_by': request.user}

                    for csv_col, value in row.items():
                        if csv_col is None:
                            continue
                        col_clean = csv_col.strip().lower()
                        model_field = FIELD_MAP.get(col_clean)
                        if not model_field:
                            continue
                        value = value.strip() if value else ''

                        if model_field == 'gender':
                            kwargs['gender'] = GENDER_MAP.get(value.lower(), 'U')
                        elif model_field in ('birth_date', 'death_date'):
                            parsed = parse_date(value)
                            if parsed:
                                kwargs[model_field] = parsed
                                # Nur-Jahr-Flag setzen wenn nur Jahreszahl angegeben
                                if value.isdigit() and len(value) == 4 and model_field == 'birth_date':
                                    kwargs['birth_year_only'] = True
                        else:
                            kwargs[model_field] = value

                    # Pflichtfelder prüfen
                    if not kwargs.get('first_name') or not kwargs.get('last_name'):
                        skipped += 1
                        errors.append(f'Zeile {row_num}: Vor- oder Nachname fehlt – übersprungen.')
                        continue

                    # Duplikat-Check (gleicher Vor- + Nachname + Geburtsdatum)
                    existing = Person.objects.filter(
                        first_name__iexact=kwargs.get('first_name', ''),
                        last_name__iexact=kwargs.get('last_name', ''),
                    )
                    if kwargs.get('birth_date'):
                        existing = existing.filter(birth_date=kwargs['birth_date'])
                    if existing.exists():
                        skipped += 1
                        errors.append(f'Zeile {row_num}: {kwargs["first_name"]} {kwargs["last_name"]} existiert bereits – übersprungen.')
                        continue

                    Person.objects.create(**kwargs)
                    created += 1

                except Exception as e:
                    errors.append(f'Zeile {row_num}: Fehler – {e}')
                    skipped += 1

            # Ergebnis-Meldungen
            if created:
                messages.success(request, f'✅ {created} Person(en) erfolgreich importiert.')
            if skipped:
                messages.warning(request, f'⚠️ {skipped} Zeile(n) übersprungen.')
            for err in errors[:10]:  # max. 10 Fehlermeldungen anzeigen
                messages.error(request, err)

            if created > 0:
                return redirect('person_list')

    else:
        form = CsvImportForm()

    # Beispiel-CSV zum Download
    example_csv = (
        "vorname,nachname,geburtsname,geschlecht,geburtsdatum,geburtsort,"
        "sterbedatum,sterbeort,beruf,notizen\n"
        "Heinrich,Mustermann,,M,1940-03-15,München,2010-11-02,München,Schreiner,Großvater\n"
        "Maria,Mustermann,Huber,F,1943-07-22,Augsburg,,,Lehrerin,Liebt das Backen\n"
        "Klaus,Mustermann,,M,1968-05-10,München,,,Ingenieur,\n"
    )

    return render(request, 'tree/csv_import.html', {
        'form': form,
        'example_csv': example_csv,
    })

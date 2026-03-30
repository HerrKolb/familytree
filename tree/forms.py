from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Person, Relationship, Invitation


class PersonForm(forms.ModelForm):
    """Formular zum Anlegen und Bearbeiten einer Person."""

    class Meta:
        model = Person
        fields = [
            'first_name', 'last_name', 'birth_name', 'gender',
            'birth_date', 'birth_year_only', 'birth_place',
            'death_date', 'death_place',
            'occupation', 'notes', 'photo',
        ]
        widgets = {
            'birth_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'death_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'first_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'birth_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'gender':      forms.Select(attrs={'class': 'form-select'}),
            'birth_place': forms.TextInput(attrs={'class': 'form-control'}),
            'death_place': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation':  forms.TextInput(attrs={'class': 'form-control'}),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo':       forms.FileInput(attrs={'class': 'form-control'}),
            'birth_year_only': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name':      'Vorname *',
            'last_name':       'Nachname *',
            'birth_name':      'Geburtsname',
            'gender':          'Geschlecht',
            'birth_date':      'Geburtsdatum',
            'birth_year_only': 'Nur Geburtsjahr bekannt',
            'birth_place':     'Geburtsort',
            'death_date':      'Sterbedatum',
            'death_place':     'Sterbeort',
            'occupation':      'Beruf',
            'notes':           'Notizen / Erinnerungen',
            'photo':           'Foto hochladen',
        }


class RelationshipForm(forms.ModelForm):
    """Formular zum Verknüpfen zweier Personen."""

    class Meta:
        model = Relationship
        fields = ['from_person', 'to_person', 'relation_type', 'note',
                  'marriage_date', 'marriage_place', 'divorce_date']
        widgets = {
            'from_person':    forms.Select(attrs={'class': 'form-select'}),
            'to_person':      forms.Select(attrs={'class': 'form-select'}),
            'relation_type':  forms.Select(attrs={'class': 'form-select'}),
            'note':           forms.TextInput(attrs={'class': 'form-control'}),
            'marriage_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'marriage_place': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. München, Standesamt Maxvorstadt'}),
            'divorce_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
        labels = {
            'from_person':    'Von Person',
            'to_person':      'Zu Person',
            'relation_type':  'Beziehungstyp',
            'note':           'Anmerkung (optional)',
            'marriage_date':  'Heiratsdatum',
            'marriage_place': 'Heiratsort',
            'divorce_date':   'Scheidungsdatum (falls zutreffend)',
        }

    def __init__(self, *args, exclude_person=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs_all = Person.objects.all().order_by('last_name', 'first_name')
        # from_person: alle Personen (damit die vorausgewählte Person sichtbar bleibt)
        self.fields['from_person'].queryset = qs_all
        # to_person: aktuelle Person ausschließen (man kann keine Beziehung zu sich selbst anlegen)
        if exclude_person:
            self.fields['to_person'].queryset = qs_all.exclude(pk=exclude_person.pk)
        else:
            self.fields['to_person'].queryset = qs_all
        # Select2: durchsuchbare Dropdown-Listen
        self.fields['from_person'].widget.attrs['class'] = 'form-select select2'
        self.fields['to_person'].widget.attrs['class'] = 'form-select select2'


class InvitationForm(forms.Form):
    """Formular zum Versenden einer Einladung."""
    email = forms.EmailField(
        label='E-Mail-Adresse',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )


class RegisterForm(UserCreationForm):
    """Registrierungsformular für eingeladene Benutzer."""
    first_name = forms.CharField(
        max_length=50, label='Vorname',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=50, label='Nachname',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-Mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class PersonSearchForm(forms.Form):
    """Suchformular für Personen."""
    q = forms.CharField(
        required=False, label='Name suchen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Vor- oder Nachname ...',
            'autofocus': True,
        })
    )
    birth_decade = forms.ChoiceField(
        required=False, label='Geburtsjahrzehnt',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    birth_place = forms.CharField(
        required=False, label='Geburtsort',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Berlin'})
    )
    occupation = forms.CharField(
        required=False, label='Beruf',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Lehrer'})
    )
    only_living = forms.BooleanField(
        required=False, label='Nur Lebende anzeigen',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        decades = [('', 'Alle')]
        from .models import Person
        years = Person.objects.filter(
            birth_date__isnull=False
        ).values_list('birth_date__year', flat=True).distinct().order_by('birth_date__year')
        seen = set()
        for y in years:
            d = (y // 10) * 10
            if d not in seen:
                seen.add(d)
                decades.append((str(d), f'{d}er'))
        self.fields['birth_decade'].choices = decades


class RelationshipEditForm(forms.ModelForm):
    """Formular zum Bearbeiten einer bestehenden Beziehung (Notiz + Heiratsdaten)."""

    class Meta:
        model = Relationship
        fields = ['note', 'marriage_date', 'marriage_place', 'divorce_date']
        widgets = {
            'note':           forms.TextInput(attrs={'class': 'form-control'}),
            'marriage_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'marriage_place': forms.TextInput(attrs={'class': 'form-control',
                              'placeholder': 'z.B. München, Standesamt Maxvorstadt'}),
            'divorce_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
        labels = {
            'note':           'Anmerkung',
            'marriage_date':  'Heiratsdatum',
            'marriage_place': 'Heiratsort',
            'divorce_date':   'Scheidungsdatum (falls zutreffend)',
        }

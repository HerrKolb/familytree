from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Person(models.Model):
    """Eintrag im Stammbaum – kann, muss aber kein Login-Account haben."""

    GENDER_CHOICES = [
        ('M', 'Männlich'),
        ('F', 'Weiblich'),
        ('D', 'Divers'),
        ('U', 'Keine Angabe'),
    ]

    # Basisdaten
    first_name      = models.CharField('Vorname', max_length=100)
    last_name       = models.CharField('Nachname', max_length=100)
    birth_name      = models.CharField('Geburtsname', max_length=100, blank=True)
    gender          = models.CharField('Geschlecht', max_length=1, choices=GENDER_CHOICES, default='U')

    # Geburt & Tod
    birth_date      = models.DateField('Geburtsdatum', null=True, blank=True)
    birth_year_only = models.BooleanField('Nur Geburtsjahr bekannt', default=False)
    birth_place     = models.CharField('Geburtsort', max_length=200, blank=True)
    death_date      = models.DateField('Sterbedatum', null=True, blank=True)
    death_place     = models.CharField('Sterbeort', max_length=200, blank=True)

    # Weitere Infos
    occupation      = models.CharField('Beruf', max_length=200, blank=True)
    notes           = models.TextField('Notizen', blank=True)

    # Foto
    photo           = models.ImageField('Foto', upload_to='photos/', null=True, blank=True)

    # Verknüpfung mit Login-Account (optional)
    user            = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='person',
        verbose_name='Benutzer-Account'
    )

    # Metadaten
    created_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_persons'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Personen'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_deceased(self):
        return self.death_date is not None

    @property
    def birth_year(self):
        if self.birth_date:
            return self.birth_date.year
        return None

    def get_parents(self):
        return Person.objects.filter(
            relationships_as_from__to_person=self,
            relationships_as_from__relation_type='parent'
        )

    def get_children(self):
        return Person.objects.filter(
            relationships_as_to__from_person=self,
            relationships_as_to__relation_type='parent'
        )

    def get_partners(self):
        partners_1 = Person.objects.filter(
            relationships_as_from__to_person=self,
            relationships_as_from__relation_type='partner'
        )
        partners_2 = Person.objects.filter(
            relationships_as_to__from_person=self,
            relationships_as_to__relation_type='partner'
        )
        return (partners_1 | partners_2).distinct()

    def get_siblings(self):
        parents = self.get_parents()
        if not parents.exists():
            return Person.objects.none()
        siblings = Person.objects.filter(
            relationships_as_to__from_person__in=parents,
            relationships_as_to__relation_type='parent'
        ).exclude(pk=self.pk).distinct()
        return siblings


class Relationship(models.Model):
    """Verwandtschaftsbeziehung zwischen zwei Personen."""

    RELATION_TYPES = [
        ('partner',  'Partner / Ehepartner'),
        ('parent',   'Elternteil → Kind'),
        ('adoptive', 'Adoptiv-Elternteil → Kind'),
        ('sibling',  'Geschwister'),
        ('half',     'Halbgeschwister'),
    ]

    from_person   = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        related_name='relationships_as_from',
        verbose_name='Von Person'
    )
    to_person     = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        related_name='relationships_as_to',
        verbose_name='Zu Person'
    )
    relation_type = models.CharField('Beziehungstyp', max_length=20, choices=RELATION_TYPES)
    note          = models.CharField('Anmerkung', max_length=200, blank=True)

    # Eheschließung (nur relevant bei relation_type='partner')
    marriage_date  = models.DateField('Heiratsdatum', null=True, blank=True)
    marriage_place = models.CharField('Heiratsort', max_length=200, blank=True)
    divorce_date   = models.DateField('Scheidungsdatum', null=True, blank=True)

    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Beziehung'
        verbose_name_plural = 'Beziehungen'
        unique_together = ('from_person', 'to_person', 'relation_type')

    def __str__(self):
        return f'{self.from_person} → {self.get_relation_type_display()} → {self.to_person}'


class Invitation(models.Model):
    """Einladungs-Token für neue Familienmitglieder."""

    token       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email       = models.EmailField('E-Mail-Adresse')
    invited_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    created_at  = models.DateTimeField(auto_now_add=True)
    expires_at  = models.DateTimeField()
    used        = models.BooleanField('Verwendet', default=False)
    used_at     = models.DateTimeField(null=True, blank=True)
    used_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='accepted_invitation'
    )

    class Meta:
        verbose_name = 'Einladung'
        verbose_name_plural = 'Einladungen'
        ordering = ['-created_at']

    def __str__(self):
        return f'Einladung für {self.email} ({"verwendet" if self.used else "offen"})'

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()


class FamilyProfile(models.Model):
    """Erweitertes Profil für jeden Benutzer – Rolle innerhalb der Familie."""

    ROLE_CHOICES = [
        ('admin',  'Admin'),
        ('member', 'Familienmitglied'),
    ]

    user   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='family_profile')
    role   = models.CharField('Rolle', max_length=10, choices=ROLE_CHOICES, default='member')

    class Meta:
        verbose_name = 'Familienprofil'
        verbose_name_plural = 'Familienprofile'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.user.is_staff

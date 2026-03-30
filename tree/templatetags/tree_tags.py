from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def age(birth_date):
    """Berechnet das aktuelle Alter aus einem Geburtsdatum."""
    if not birth_date:
        return ''
    today = timezone.now().date()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


@register.filter
def pluralize_de(count, forms):
    """
    Deutsches Pluralisieren. forms = 'Singular,Plural'
    Beispiel: {{ count|pluralize_de:"Person,Personen" }}
    """
    singular, plural = forms.split(',')
    return singular if count == 1 else plural

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
import datetime

from .models import Person, Relationship, Invitation, FamilyProfile
from .forms import (
    PersonForm, RelationshipForm, RelationshipEditForm, InvitationForm,
    RegisterForm, PersonSearchForm
)


# ---------------------------------------------------------------------------
# Hilfsfunktion: Admin-Check
# ---------------------------------------------------------------------------
def is_admin(user):
    try:
        return user.family_profile.is_admin
    except FamilyProfile.DoesNotExist:
        return user.is_staff


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    today = timezone.now().date()
    # Geburtstage in den nächsten 30 Tagen
    upcoming_birthdays = []
    persons_with_bday = Person.objects.filter(birth_date__isnull=False, death_date__isnull=True)
    for p in persons_with_bday:
        try:
            bday_this_year = p.birth_date.replace(year=today.year)
        except ValueError:
            continue  # 29. Feb in Nicht-Schaltjahr
        if bday_this_year < today:
            bday_this_year = p.birth_date.replace(year=today.year + 1)
        delta = (bday_this_year - today).days
        if 0 <= delta <= 30:
            upcoming_birthdays.append({'person': p, 'days': delta, 'date': bday_this_year})
    upcoming_birthdays.sort(key=lambda x: x['days'])

    recent_persons = Person.objects.order_by('-created_at')[:5]
    total_persons  = Person.objects.count()
    total_living   = Person.objects.filter(death_date__isnull=True).count()

    return render(request, 'tree/dashboard.html', {
        'upcoming_birthdays': upcoming_birthdays,
        'recent_persons':     recent_persons,
        'total_persons':      total_persons,
        'total_living':       total_living,
    })


# ---------------------------------------------------------------------------
# Stammbaum-Visualisierung
# ---------------------------------------------------------------------------
@login_required
def tree_view(request):
    return render(request, 'tree/tree.html')


@login_required
def tree_data(request):
    """JSON-API fuer D3.js – gibt Personen und Beziehungen zurueck.
    Mit ?focus=<pk> nur relevante Personen: Vorfahren, Geschwister, Partner, Kinder.
    """
    focus_pk = request.GET.get('focus')
    if focus_pk:
        try:
            focus_pk = int(focus_pk)
            relevant_ids = _get_focus_ids(focus_pk)
        except (ValueError, Person.DoesNotExist):
            focus_pk = None
            relevant_ids = None
    else:
        relevant_ids = None

    if relevant_ids is not None:
        persons = Person.objects.filter(pk__in=relevant_ids)
        relationships = Relationship.objects.filter(
            from_person__in=relevant_ids,
            to_person__in=relevant_ids
        ).select_related('from_person', 'to_person')
    else:
        persons = Person.objects.all()
        relationships = Relationship.objects.select_related('from_person', 'to_person').all()

    nodes = []
    for p in persons:
        nodes.append({
            'id':        p.pk,
            'name':      p.full_name,
            'gender':    p.gender,
            'birth_year': p.birth_year,
            'deceased':  p.is_deceased,
            'photo':     p.photo.url if p.photo else None,
            'focus':     p.pk == focus_pk,
        })

    links = []
    for r in relationships:
        links.append({
            'source': r.from_person.pk,
            'target': r.to_person.pk,
            'type':   r.relation_type,
        })

    return JsonResponse({'nodes': nodes, 'links': links, 'focus': focus_pk})


def _get_focus_ids(person_pk):
    """Alle relevanten IDs fuer Fokus-Ansicht sammeln."""
    all_rels = list(Relationship.objects.select_related('from_person', 'to_person').all())

    def get_parents(pid):
        return [r.from_person.pk for r in all_rels
                if r.to_person.pk == pid and r.relation_type in ('parent', 'adoptive')]

    def get_children(pid):
        return [r.to_person.pk for r in all_rels
                if r.from_person.pk == pid and r.relation_type in ('parent', 'adoptive')]

    def get_partners(pid):
        p1 = [r.to_person.pk for r in all_rels
              if r.from_person.pk == pid and r.relation_type == 'partner']
        p2 = [r.from_person.pk for r in all_rels
              if r.to_person.pk == pid and r.relation_type == 'partner']
        return list(set(p1 + p2))

    def get_siblings(pid):
        parents = get_parents(pid)
        sibs = set()
        for par in parents:
            for sib in get_children(par):
                if sib != pid:
                    sibs.add(sib)
        return list(sibs)

    def collect_ancestors(pid, visited=None):
        if visited is None:
            visited = set()
        if pid in visited:
            return visited
        visited.add(pid)
        for parent in get_parents(pid):
            collect_ancestors(parent, visited)
            # Partner des Elternteils ebenfalls vollständig verfolgen
            for pp in get_partners(parent):
                collect_ancestors(pp, visited)
        return visited

    ids = set([person_pk])
    ids.update(collect_ancestors(person_pk))
    partners = get_partners(person_pk)
    ids.update(partners)
    children = get_children(person_pk)
    ids.update(children)
    for child in children:
        ids.update(get_partners(child))
    siblings = get_siblings(person_pk)
    ids.update(siblings)
    for sib in siblings:
        ids.update(get_partners(sib))
    return ids


# ---------------------------------------------------------------------------
# Personenliste & Suche
# ---------------------------------------------------------------------------
@login_required
def person_list(request):
    form = PersonSearchForm(request.GET or None)
    persons = Person.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            persons = persons.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(birth_name__icontains=q)
            )
        decade = form.cleaned_data.get('birth_decade')
        if decade:
            d = int(decade)
            persons = persons.filter(birth_date__year__gte=d, birth_date__year__lt=d + 10)
        birth_place = form.cleaned_data.get('birth_place')
        if birth_place:
            persons = persons.filter(birth_place__icontains=birth_place)
        occupation = form.cleaned_data.get('occupation')
        if occupation:
            persons = persons.filter(occupation__icontains=occupation)
        if form.cleaned_data.get('only_living'):
            persons = persons.filter(death_date__isnull=True)

    return render(request, 'tree/person_list.html', {
        'persons': persons,
        'form':    form,
        'count':   persons.count(),
    })


# ---------------------------------------------------------------------------
# Person Detail
# ---------------------------------------------------------------------------
@login_required
def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)
    return render(request, 'tree/person_detail.html', {
        'person':   person,
        'parents':  person.get_parents(),
        'children': person.get_children(),
        'partners': person.get_partners(),
        'siblings': person.get_siblings(),
    })


# ---------------------------------------------------------------------------
# Person anlegen
# ---------------------------------------------------------------------------
@login_required
def person_create(request):
    if request.method == 'POST':
        form = PersonForm(request.POST, request.FILES)
        if form.is_valid():
            person = form.save(commit=False)
            person.created_by = request.user
            person.save()
            messages.success(request, f'"{person}" wurde erfolgreich angelegt.')
            return redirect('person_detail', pk=person.pk)
    else:
        form = PersonForm()
    return render(request, 'tree/person_form.html', {'form': form, 'title': 'Person hinzufügen'})


# ---------------------------------------------------------------------------
# Person bearbeiten
# ---------------------------------------------------------------------------
@login_required
def person_edit(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        form = PersonForm(request.POST, request.FILES, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{person}" wurde aktualisiert.')
            return redirect('person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person)
    return render(request, 'tree/person_form.html', {
        'form': form, 'person': person, 'title': f'{person} bearbeiten'
    })


# ---------------------------------------------------------------------------
# Person löschen (nur Admin)
# ---------------------------------------------------------------------------
@login_required
def person_delete(request, pk):
    if not is_admin(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('person_detail', pk=pk)
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        name = str(person)
        person.delete()
        messages.success(request, f'"{name}" wurde gelöscht.')
        return redirect('person_list')
    return render(request, 'tree/person_confirm_delete.html', {'person': person})


# ---------------------------------------------------------------------------
# Beziehung anlegen
# ---------------------------------------------------------------------------
@login_required
def relationship_create(request, person_pk):
    person = get_object_or_404(Person, pk=person_pk)
    if request.method == 'POST':
        form = RelationshipForm(request.POST, exclude_person=person)
        if form.is_valid():
            form.save()
            messages.success(request, 'Beziehung wurde gespeichert.')
            return redirect('person_detail', pk=person.pk)
    else:
        form = RelationshipForm(
            exclude_person=person,
            initial={'from_person': person}
        )
    return render(request, 'tree/relationship_form.html', {'form': form, 'person': person})


# ---------------------------------------------------------------------------
# Beziehungen verwalten
# ---------------------------------------------------------------------------
@login_required
def relationship_list(request, person_pk):
    """Alle Beziehungen einer Person anzeigen und bearbeitbar machen."""
    person = get_object_or_404(Person, pk=person_pk)

    # Alle Beziehungen dieser Person (von und zu)
    rels_from = person.relationships_as_from.select_related('to_person').all()
    rels_to   = person.relationships_as_to.select_related('from_person').all()

    # Zusammenführen mit Info welche Seite die Person ist
    relationships = []
    for r in rels_from:
        relationships.append({'rel': r, 'other': r.to_person, 'side': 'from'})
    for r in rels_to:
        relationships.append({'rel': r, 'other': r.from_person, 'side': 'to'})

    # Sortieren: Partner zuerst, dann Eltern/Kinder, dann Geschwister
    order = {'partner': 0, 'parent': 1, 'adoptive': 2, 'sibling': 3, 'half': 4}
    relationships.sort(key=lambda x: (order.get(x['rel'].relation_type, 9),
                                      x['other'].last_name, x['other'].first_name))

    return render(request, 'tree/relationship_list.html', {
        'person':        person,
        'relationships': relationships,
    })


@login_required
def relationship_edit(request, pk):
    """Einzelne Beziehung bearbeiten – nur Heiratsfelder und Notiz."""
    rel = get_object_or_404(Relationship, pk=pk)
    person_pk = request.GET.get('person') or request.POST.get('person')
    person = get_object_or_404(Person, pk=person_pk) if person_pk else rel.from_person

    if request.method == 'POST':
        form = RelationshipEditForm(request.POST, instance=rel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Beziehung wurde gespeichert.')
            return redirect('relationship_list', person_pk=person.pk)
    else:
        form = RelationshipEditForm(instance=rel)

    return render(request, 'tree/relationship_edit.html', {
        'form':   form,
        'rel':    rel,
        'person': person,
    })


@login_required
def relationship_delete(request, pk):
    """Beziehung löschen."""
    rel = get_object_or_404(Relationship, pk=pk)
    person_pk = request.GET.get('person') or request.POST.get('person')
    person = get_object_or_404(Person, pk=person_pk) if person_pk else rel.from_person

    if request.method == 'POST':
        rel.delete()
        messages.success(request, 'Beziehung wurde gelöscht.')
        return redirect('relationship_list', person_pk=person.pk)

    return render(request, 'tree/relationship_confirm_delete.html', {
        'rel':    rel,
        'person': person,
    })


# ---------------------------------------------------------------------------
# Einladungssystem (nur Admin)
# ---------------------------------------------------------------------------
@login_required
def invite(request):
    if not is_admin(request.user):
        messages.error(request, 'Nur Admins können Einladungen versenden.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            expiry_hours = getattr(settings, 'INVITATION_EXPIRY_HOURS', 168)
            invitation = Invitation.objects.create(
                email=email,
                invited_by=request.user,
                expires_at=timezone.now() + datetime.timedelta(hours=expiry_hours),
            )
            link = request.build_absolute_uri(f'/register/{invitation.token}/')
            try:
                send_mail(
                    subject='Einladung zu FamilyTree',
                    message=(
                        f'Hallo,\n\n'
                        f'Du wurdest von {request.user.get_full_name() or request.user.username} '
                        f'zum Familien-Stammbaum eingeladen.\n\n'
                        f'Registriere dich hier (gültig für {expiry_hours // 24} Tage):\n{link}\n\n'
                        f'Viele Grüße,\nFamilyTree'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
                messages.success(request, f'Einladung an {email} wurde versendet.')
            except Exception as e:
                messages.warning(request, f'Einladung erstellt, aber E-Mail konnte nicht gesendet werden: {e}')
                messages.info(request, f'Einladungslink: {link}')
            return redirect('invite')
    else:
        form = InvitationForm()

    invitations = Invitation.objects.order_by('-created_at')[:20]
    return render(request, 'tree/invite.html', {'form': form, 'invitations': invitations})


# ---------------------------------------------------------------------------
# Registrierung per Einladungs-Token
# ---------------------------------------------------------------------------
def register(request, token):
    invitation = get_object_or_404(Invitation, token=token)
    if not invitation.is_valid:
        messages.error(request, 'Dieser Einladungslink ist abgelaufen oder wurde bereits verwendet.')
        return redirect('login')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # FamilyProfile anlegen
            FamilyProfile.objects.create(user=user, role='member')
            # Einladung als verwendet markieren
            invitation.used    = True
            invitation.used_at = timezone.now()
            invitation.used_by = user
            invitation.save()
            login(request, user)
            messages.success(request, f'Willkommen, {user.first_name}! Dein Konto wurde erstellt.')
            return redirect('dashboard')
    else:
        form = RegisterForm(initial={'email': invitation.email})

    return render(request, 'tree/register.html', {'form': form, 'invitation': invitation})


# ---------------------------------------------------------------------------
# Mein Profil
# ---------------------------------------------------------------------------
@login_required
def my_profile(request):
    try:
        person = request.user.person
        return redirect('person_detail', pk=person.pk)
    except Person.DoesNotExist:
        messages.info(request, 'Du bist noch nicht mit einer Person im Stammbaum verknüpft.')
        return redirect('person_list')

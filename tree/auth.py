"""
Anmeldung über Authentik (Forward-Auth hinter Caddy).

Caddy fragt bei jeder Anfrage Authentik, ob der Besucher angemeldet ist, und
reicht Benutzername, Name, E-Mail und Gruppen als Header an familytree weiter:

    X-Authentik-Username, X-Authentik-Name, X-Authentik-Email, X-Authentik-Groups

Diese Header dürfen ausschließlich von Caddy kommen. Deshalb:
  * familytree veröffentlicht keinen Port, sondern ist nur im Docker-Netz
    "proxy" erreichbar,
  * Caddy entfernt eventuell vom Browser mitgeschickte X-Authentik-Header,
    bevor es die echten von Authentik einsetzt.

Rollen:
  * Gruppe aus AUTHENTIK_ADMIN_GROUPS  -> FamilyProfile.role = 'admin',
    zusätzlich is_staff/is_superuser (Zugang zu /admin/)
  * Gruppe aus AUTHENTIK_ALLOWED_GROUPS -> 'member'
  * keine dieser Gruppen (z. B. gast)  -> 403 Zugriff verweigert
"""
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.http import HttpResponseForbidden

HEADER_USERNAME = 'HTTP_X_AUTHENTIK_USERNAME'
HEADER_NAME = 'HTTP_X_AUTHENTIK_NAME'
HEADER_EMAIL = 'HTTP_X_AUTHENTIK_EMAIL'
HEADER_GROUPS = 'HTTP_X_AUTHENTIK_GROUPS'


def _groups(request):
    raw = request.META.get(HEADER_GROUPS, '')
    return {g.strip() for g in raw.split('|') if g.strip()}


class AuthentikBackend(RemoteUserBackend):
    """Legt unbekannte Benutzer beim ersten Besuch automatisch an."""
    create_unknown_user = True


class AuthentikHeaderMiddleware(RemoteUserMiddleware):
    header = HEADER_USERNAME

    def process_request(self, request):
        if not request.META.get(self.header):
            # Ohne Header kein Zugriff – passiert nur, wenn familytree
            # an Caddy/Authentik vorbei aufgerufen wird.
            super().process_request(request)  # meldet eine alte Sitzung ab
            return HttpResponseForbidden('Anmeldung über beikolbs.de erforderlich.')

        # Gruppen prüfen, bevor ein Benutzer angelegt wird
        groups = _groups(request)
        allowed = set(settings.AUTHENTIK_ALLOWED_GROUPS)
        admin = set(settings.AUTHENTIK_ADMIN_GROUPS)
        if not groups & (allowed | admin):
            return HttpResponseForbidden('Kein Zugriff auf den Stammbaum.')

        response = super().process_request(request)
        if response is not None:
            return response
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Anmeldung fehlgeschlagen.')

        self._sync_user(request, request.user, is_admin=bool(groups & admin))
        return None

    @staticmethod
    def _sync_user(request, user, is_admin):
        """Name, E-Mail und Rolle bei jeder Anfrage mit Authentik abgleichen."""
        from tree.models import FamilyProfile

        changed = []
        name = request.META.get(HEADER_NAME, '').strip()
        email = request.META.get(HEADER_EMAIL, '').strip()
        if name:
            first, _, last = name.partition(' ')
            if user.first_name != first:
                user.first_name = first
                changed.append('first_name')
            if user.last_name != last:
                user.last_name = last
                changed.append('last_name')
        if email and user.email != email:
            user.email = email
            changed.append('email')
        if user.is_staff != is_admin:
            user.is_staff = is_admin
            changed.append('is_staff')
        if user.is_superuser != is_admin:
            user.is_superuser = is_admin
            changed.append('is_superuser')
        if changed:
            user.save(update_fields=changed)

        role = 'admin' if is_admin else 'member'
        profile, _ = FamilyProfile.objects.get_or_create(user=user, defaults={'role': role})
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=['role'])

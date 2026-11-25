# FamilyTree

Django-App zur Pflege des Familien-Stammbaums. Läuft auf **stammbaum.beikolbs.de**
als Docker-Container hinter Caddy; die Anmeldung übernimmt **Authentik**.

## Betrieb auf dem Server

```
cd /opt/beikolbs/familytree
cp .env.example .env        # Werte eintragen (openssl rand -hex 32)
docker compose up -d --build
docker compose logs -f web
```

* `web`: Django mit gunicorn, nur im Docker-Netz `proxy` erreichbar (kein offener Port)
* `db`: PostgreSQL 16, Daten im Volume `db_data`
* Fotos: Ordner `./media`

### Anmeldung und Rollen

Caddy prüft jede Anfrage über Authentik (Forward-Auth) und reicht Benutzer,
Name, E-Mail und Gruppen als `X-Authentik-*`-Header weiter (`tree/auth.py`).

| Authentik-Gruppe | Rolle in familytree |
|---|---|
| `admin` | Admin (Löschen, Django-Admin unter `/admin/`) |
| `familie` | Familienmitglied (Anlegen, Bearbeiten) |
| andere, z. B. `gast` | kein Zugriff (403) |

Benutzer werden beim ersten Besuch automatisch angelegt; Name, E-Mail und
Rolle werden bei jedem Aufruf mit Authentik abgeglichen. Die Gruppen lassen
sich in `.env` über `AUTHENTIK_ALLOWED_GROUPS` und `AUTHENTIK_ADMIN_GROUPS` ändern.

### Datensicherung

```
docker compose exec db pg_dump -U familytree familytree > familytree_$(date +%F).sql
```

### Import der alten MySQL-Daten

`python manage.py import_stammbaum <datei.json>` spielt Personen und
Beziehungen aus einem `dumpdata`-Export ein und leert dabei die
Verknüpfungen zu alten Benutzerkonten. Ablauf siehe Einrichtungsanleitung.

## Lokale Entwicklung

```
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` für die Entwicklung (SQLite, klassisches Django-Login):

```
DJANGO_DEBUG=True
AUTH_MODE=local
DB_ENGINE=sqlite
```

```
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_admin --username=<name>
python manage.py runserver
```

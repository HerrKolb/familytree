# FamilyTree – Installationsanleitung

## Voraussetzungen
- Python 3.10 oder neuer
- MySQL Server (z.B. XAMPP, MySQL Community Server)
- pip

---

## 1. Datenbank anlegen

```bash
mysql -u root -p < create_database.sql
```

Oder manuell in MySQL:
```sql
CREATE DATABASE familytree CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 2. Virtuelle Umgebung erstellen & Pakete installieren

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

---

## 3. Datenbank-Zugangsdaten anpassen

In `familytree/settings.py` folgende Zeilen anpassen:

```python
DATABASES = {
    'default': {
        'NAME':     'familytree',
        'USER':     'root',          # deinen MySQL-User eintragen
        'PASSWORD': 'password',      # dein MySQL-Passwort eintragen
        'HOST':     'localhost',
        'PORT':     '3306',
    }
}
```

---

## 4. Datenbanktabellen erstellen

```bash
python manage.py migrate
```

---

## 5. Admin-Konto anlegen

```bash
python manage.py createsuperuser
```

Dann im Django-Shell das FamilyProfile als Admin anlegen:

```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from tree.models import FamilyProfile
u = User.objects.get(username='dein_username')
FamilyProfile.objects.create(user=u, role='admin')
exit()
```

---

## 6. App starten

```bash
# Nur lokal (nur du):
python manage.py runserver

# Im Heimnetz (alle Geräte im WLAN erreichbar):
python manage.py runserver 0.0.0.0:8000
```

Dann im Browser öffnen:
- Lokal:      http://localhost:8000
- Heimnetz:   http://192.168.x.x:8000  (deine lokale IP eintragen)

---

## 7. E-Mail für Einladungen einrichten (optional)

In `familytree/settings.py`:

```python
EMAIL_HOST_USER     = 'deine@gmail.com'
EMAIL_HOST_PASSWORD = 'dein-google-app-passwort'
DEFAULT_FROM_EMAIL  = 'FamilyTree <deine@gmail.com>'
```

**Google App-Passwort erstellen:**
1. Google-Konto → Sicherheit → 2-Faktor-Authentifizierung aktivieren
2. Sicherheit → App-Passwörter → Neues App-Passwort für "Mail" erstellen
3. Das generierte Passwort in settings.py eintragen

---

## Projektstruktur

```
familytree/
├── familytree/          # Django-Projektkonfiguration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tree/                # Haupt-App
│   ├── models.py        # Datenbankmodelle (Person, Relationship, Invitation)
│   ├── views.py         # Alle Views / Logik
│   ├── forms.py         # Formulare
│   ├── admin.py         # Django Admin Konfiguration
│   ├── urls.py          # URL-Routing
│   ├── templates/tree/  # HTML-Templates
│   └── static/tree/     # CSS, JS
├── media/               # Hochgeladene Fotos (automatisch erstellt)
├── create_database.sql  # MySQL-Skript
├── requirements.txt
└── manage.py
```

---

## Admin-Profil einrichten (vereinfacht)

Statt des manuellen Shell-Befehls kannst du jetzt das Management-Command nutzen:

```bash
python manage.py setup_admin --username=dein_username
```

---

## Testdaten laden (optional)

Um die App mit Beispieldaten (Familie Mustermann, 3 Generationen) zu starten:

```bash
python manage.py loaddata tree/fixtures/sample_data.json
```

---

## Häufige Probleme

**`mysqlclient` Installation schlägt fehl (Windows):**
```bash
pip install mysqlclient --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/
```
Alternativ: MySQL Connector/Python verwenden und in settings.py `ENGINE` auf
`django.db.backends.mysql` belassen, aber `mysqlclient` durch `mysql-connector-python` ersetzen.

**Port 8000 bereits belegt:**
```bash
python manage.py runserver 8080
```

**Lokale IP herausfinden:**
- Windows: `ipconfig` → IPv4-Adresse
- Mac/Linux: `ifconfig` oder `ip addr`

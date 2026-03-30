-- ============================================================
-- FamilyTree – MySQL Datenbankskript
-- Ausführen bevor Django migrate läuft:
--   mysql -u root -p < create_database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS familytree
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'familytree_user'@'localhost'
  IDENTIFIED BY 'sicheres_passwort_hier_aendern';

GRANT ALL PRIVILEGES ON familytree.* TO 'familytree_user'@'localhost';

FLUSH PRIVILEGES;

-- Wechsel zur Datenbank (nur zur Kontrolle, Tabellen erstellt Django)
USE familytree;

SELECT 'Datenbank familytree erfolgreich erstellt.' AS Status;

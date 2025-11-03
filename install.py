"""
Dieses Script:
- Installiert alle nötigen Abhängigkeiten
- Setzt die Datenbank auf
"""

import os
import sys
import subprocess
import sqlite3
import hashlib
from pathlib import Path

# Farben für die Konsole
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


HGO = r"""
##   ##   #####    #####
##   ##  ##   ##  ##   ##
##   ##  ##       ##   ##
#######  ##  ###  ##   ##
##   ##  ##   ##  ##   ##
##   ##  ##   ##  ##   ##
##   ##   #####    #####
"""


def print_ascii():
    """Druckt das ASCII-Logo und die Kontaktzeile."""
    print(f"{Colors.OKCYAN}{HGO}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Bei Fragen an jongae007@gmail.com wenden.{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def check_python_version():
    print_info("Überprüfe Python-Version...")
    
    if sys.version_info < (3, 7):
        print_error("Python 3.7 oder höher wird benötigt!")
        print_error(f"Aktuelle Version: {sys.version}")
        return False
    
    print_success(f"Python-Version OK: {sys.version.split()[0]}")
    return True


def install_dependencies():
    print_info("Installiere Python-Abhängigkeiten...")
    
    requirements = ["flask"]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_success(f"Paket '{package}' installiert")
        except subprocess.CalledProcessError:
            print_error(f"Fehler beim Installieren von '{package}'")
            return False
    
    return True



def setup_database():
    """Initialisiert die SQLite-Datenbank"""
    print_info("Initialisiere Datenbank...")
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Prüfe ob die Tabelle bereits existiert und füge fehlende Spalten hinzu
        try:
            # Prüfe ob datenschutz_datum Spalte existiert
            cursor.execute("PRAGMA table_info(schueler_daten)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Füge fehlende Spalten hinzu falls sie nicht existieren
            if 'datenschutz_einwilligung' not in columns:
                cursor.execute('ALTER TABLE schueler_daten ADD COLUMN datenschutz_einwilligung BOOLEAN NOT NULL DEFAULT 1')
            
            if 'datenschutz_datum' not in columns:
                cursor.execute('ALTER TABLE schueler_daten ADD COLUMN datenschutz_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                
        except sqlite3.OperationalError:
            # Tabelle existiert noch nicht, wird unten erstellt
            pass
        
        # Tabelle für Abitur-Jahrgänge
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abitur_jahrgaenge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jahrgang INTEGER UNIQUE NOT NULL,
                aktiv BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabelle für Schülerdaten
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schueler_daten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jahrgang_id INTEGER NOT NULL,
                vorname TEXT NOT NULL,
                nachname TEXT NOT NULL,
                email TEXT NOT NULL,
                datenschutz_einwilligung BOOLEAN NOT NULL DEFAULT 1,
                datenschutz_datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jahrgang_id) REFERENCES abitur_jahrgaenge (id)
            )
        ''')
        
        # Admin-Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzername TEXT UNIQUE NOT NULL,
                passwort_hash TEXT NOT NULL
            )
        ''')
        # Standard-Login erstellen (admin/password)
        admin_passwort = hashlib.sha256('password'.encode()).hexdigest()
        cursor.execute('INSERT OR IGNORE INTO admins (benutzername, passwort_hash) VALUES (?, ?)', 
                       ('admin', admin_passwort))
        
        conn.commit()
        conn.close()
        
        print_success("Datenbank initialisiert")
        print_success("Admin-Benutzer erstellt: admin/password")
        
        return True
        
    except Exception as e:
        print_error(f"Fehler bei der Datenbank-Initialisierung: {e}")
        return False


def main():
    """Hauptfunktion des Installationsscripts"""
    print_ascii()
    print_header("INSTALLATION")
    
    print_info("Dieses Script installiert Abhängigkeiten und setzt die Datenbank auf.")
    
    if not check_python_version():
        sys.exit(1)
    
    steps = [
        ("Python-Abhängigkeiten", install_dependencies),
        ("Datenbank", setup_database)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    print_header("INSTALLATION ABGESCHLOSSEN")
    
    if not failed_steps:
        print_info("Nächste Schritte:")
        print("   1. Starte die Anwendung: python3 main.py")
        print("   2. Öffne http://localhost")
        print("   3. Admin-Login: http://localhost/admin")
        print("   4. Standard-Anmeldung: admin / password")
        print("")
        print_warning("⚠️  WICHTIG: Ändere das Admin-Passwort nach der ersten Anmeldung!")
        # Versuche die Anwendung zu starten
        main_py = Path(__file__).resolve().parent / "main.py"
        if not main_py.exists():
            print_error("Konnte main.py nicht finden. Stelle sicher, dass sich main.py im Projektverzeichnis befindet.")
            return

        print_info("Starte main.py")
        try:
            result = subprocess.run(
                [sys.executable, str(main_py)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            if result.returncode == 0:
                print_success("main.py wurde erfolgreich ausgeführt.")
            else:
                output = (result.stdout or "").strip()
                print_error(f"main.py wurde mit Exit-Code {result.returncode} beendet.")
                if output:
                    print_error("Fehlerausgabe von main.py:")
                    for line in output.splitlines():
                        print_error(line)
        except Exception as e:
            print_error(f"Fehler beim Starten von main.py: {e}")
    else:
        print_error("❌ Installation teilweise fehlgeschlagen!")
        print(f"   Fehlgeschlagene Schritte: {', '.join(failed_steps)}")
        print("")
        print_warning("Die Anwendung funktioniert möglicherweise trotzdem.")
        print_info("Überprüfe die Fehlermeldungen und versuche es erneut.")
        
    
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n❌ Installation abgebrochen!")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
import flask
import sqlite3
import hashlib
import datetime
import csv
import io
import secrets

app = flask.Flask(__name__)
app.secret_key = secrets.token_urlsafe(48)
DATABASE = 'database.db'

def get_db_connection():
    """Hilfsfunktion für Datenbankverbindungen"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

#===========================================================
#                     Webseiten Routen
#===========================================================
@app.route('/')
def home():
    """Hauptseite mit Formular für Schülerdaten"""
    conn = get_db_connection()
    jahrgaenge = conn.execute('SELECT * FROM abitur_jahrgaenge WHERE aktiv = 1 ORDER BY jahrgang DESC').fetchall()
    conn.close()
    return flask.render_template('index.html', jahrgaenge=jahrgaenge)

@app.route('/datenschutz')
def datenschutz():
    """Datenschutzerklärung"""
    return flask.render_template('datenschutz.html')

@app.route('/admin/jahrgaenge')
def admin_jahrgaenge():
    """Jahrgangs-Verwaltung"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    jahrgaenge = conn.execute('''
        SELECT a.*, COUNT(s.id) as schueler_anzahl 
        FROM abitur_jahrgaenge a
        LEFT JOIN schueler_daten s ON a.id = s.jahrgang_id
        GROUP BY a.id
        ORDER BY a.jahrgang DESC
    ''').fetchall()
    conn.close()
    
    return flask.render_template('admin_jahrgaenge.html', jahrgaenge=jahrgaenge)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin-Dashboard mit Übersicht aller Daten"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Alle Schülerdaten mit Jahrgang abrufen
    schueler = conn.execute('''
        SELECT s.*, a.jahrgang 
        FROM schueler_daten s
        JOIN abitur_jahrgaenge a ON s.jahrgang_id = a.id
        ORDER BY s.erstellt_am DESC
    ''').fetchall()
    
    # Statistiken
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_schueler,
            COUNT(DISTINCT jahrgang_id) as aktive_jahrgaenge
        FROM schueler_daten
    ''').fetchone()
    
    conn.close()
    
    return flask.render_template('admin_dashboard.html', schueler=schueler, stats=stats)

@app.route('/admin')
def admin_login():
    """Admin-Login Seite"""
    if 'admin_logged_in' in flask.session:
        return flask.redirect(flask.url_for('admin_dashboard'))
    return flask.render_template('admin_login.html')


#===========================================================
#                      API Endpoints
#===========================================================

@app.route('/submit', methods=['POST'])
def submit_data():
    """Verarbeite eingereichte Schülerdaten"""
    jahrgang_id = flask.request.form.get('jahrgang_id')
    vorname = flask.request.form.get('vorname')
    nachname = flask.request.form.get('nachname')
    email = flask.request.form.get('email')
    datenschutz_einwilligung = flask.request.form.get('datenschutz_einwilligung')
    
    if not all([jahrgang_id, vorname, nachname, email]):
        flask.flash('Alle Felder müssen ausgefüllt werden!', 'error')
        return flask.redirect(flask.url_for('home'))
    
    if not datenschutz_einwilligung:
        flask.flash('Die Datenschutzerklärung muss akzeptiert werden!', 'error')
        return flask.redirect(flask.url_for('home'))
    
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO schueler_daten (jahrgang_id, vorname, nachname, email, datenschutz_einwilligung)
            VALUES (?, ?, ?, ?, ?)
        ''', (jahrgang_id, vorname, nachname, email, True))
        conn.commit()
        conn.close()
        flask.flash('Daten erfolgreich gespeichert!', 'success')
    except Exception as e:
        flask.flash(f'Fehler beim Speichern: {str(e)}', 'error')
    
    return flask.redirect(flask.url_for('home'))


@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Verarbeite Admin-Login"""
    benutzername = flask.request.form.get('benutzername')
    passwort = flask.request.form.get('passwort')
    
    if not benutzername or not passwort:
        flask.flash('Benutzername und Passwort erforderlich!', 'error')
        return flask.redirect(flask.url_for('admin_login'))
    
    passwort_hash = hashlib.sha256(passwort.encode()).hexdigest()
    
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM admins WHERE benutzername = ? AND passwort_hash = ?',
                        (benutzername, passwort_hash)).fetchone()
    conn.close()
    
    if admin:
        flask.session['admin_logged_in'] = True
        flask.session['admin_id'] = admin['id']
        return flask.redirect(flask.url_for('admin_dashboard'))
    else:
        flask.flash('Ungültige Anmeldedaten!', 'error')
        return flask.redirect(flask.url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin-Logout"""
    flask.session.pop('admin_logged_in', None)
    flask.session.pop('admin_id', None)
    return flask.redirect(flask.url_for('home'))




@app.route('/admin/jahrgang/add', methods=['POST'])
def admin_add_jahrgang():
    """Neuen Jahrgang hinzufügen"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    jahrgang = flask.request.form.get('jahrgang')
    
    if not jahrgang:
        flask.flash('Jahrgang ist erforderlich!', 'error')
        return flask.redirect(flask.url_for('admin_jahrgaenge'))
    
    try:
        jahrgang = int(jahrgang)
        if jahrgang < 1900 or jahrgang > 2100:
            flask.flash('Bitte geben Sie eine gültige Jahreszahl ein!', 'error')
            return flask.redirect(flask.url_for('admin_jahrgaenge'))
        
        conn = get_db_connection()
        conn.execute('INSERT INTO abitur_jahrgaenge (jahrgang) VALUES (?)', (jahrgang,))
        conn.commit()
        conn.close()
        
        flask.flash(f'Jahrgang {jahrgang} erfolgreich hinzugefügt!', 'success')
    except ValueError:
        flask.flash('Bitte geben Sie eine gültige Jahreszahl ein!', 'error')
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            flask.flash('Dieser Jahrgang existiert bereits!', 'error')
        else:
            flask.flash(f'Fehler beim Hinzufügen: {str(e)}', 'error')
    
    return flask.redirect(flask.url_for('admin_jahrgaenge'))

@app.route('/admin/jahrgang/toggle/<int:jahrgang_id>')
def admin_toggle_jahrgang(jahrgang_id):
    """Jahrgang aktivieren/deaktivieren"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    jahrgang = conn.execute('SELECT * FROM abitur_jahrgaenge WHERE id = ?', (jahrgang_id,)).fetchone()
    
    if jahrgang:
        new_status = not jahrgang['aktiv']
        conn.execute('UPDATE abitur_jahrgaenge SET aktiv = ? WHERE id = ?', (new_status, jahrgang_id))
        conn.commit()
        
        status_text = 'aktiviert' if new_status else 'deaktiviert'
        flask.flash(f'Jahrgang {jahrgang["jahrgang"]} wurde {status_text}!', 'success')
    
    conn.close()
    return flask.redirect(flask.url_for('admin_jahrgaenge'))

@app.route('/admin/jahrgang/delete/<int:jahrgang_id>')
def admin_delete_jahrgang(jahrgang_id):
    """Jahrgang und alle zugehörigen Schüler löschen"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    
    try:
        # Jahrgang-Info für Bestätigung abrufen
        jahrgang = conn.execute('SELECT jahrgang FROM abitur_jahrgaenge WHERE id = ?', (jahrgang_id,)).fetchone()
        
        if not jahrgang:
            flask.flash('Jahrgang nicht gefunden!', 'error')
            return flask.redirect(flask.url_for('admin_jahrgaenge'))
        
        # Anzahl betroffener Schüler ermitteln
        schueler_count = conn.execute('SELECT COUNT(*) as count FROM schueler_daten WHERE jahrgang_id = ?', 
                                      (jahrgang_id,)).fetchone()
        
        # Alle Schüler des Jahrgangs löschen
        conn.execute('DELETE FROM schueler_daten WHERE jahrgang_id = ?', (jahrgang_id,))
        
        # Jahrgang löschen
        conn.execute('DELETE FROM abitur_jahrgaenge WHERE id = ?', (jahrgang_id,))
        
        conn.commit()
        
        if schueler_count['count'] > 0:
            flask.flash(f'Jahrgang {jahrgang["jahrgang"]} und {schueler_count["count"]} zugehörige Schüler erfolgreich gelöscht!', 'success')
        else:
            flask.flash(f'Jahrgang {jahrgang["jahrgang"]} erfolgreich gelöscht!', 'success')
            
    except Exception as e:
        conn.rollback()
        flask.flash(f'Fehler beim Löschen: {str(e)}', 'error')
    finally:
        conn.close()
    
    return flask.redirect(flask.url_for('admin_jahrgaenge'))

@app.route('/admin/export/csv')
def admin_export_csv():
    """CSV-Export aller Schülerdaten"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Alle Schülerdaten mit Jahrgang abrufen
    try:
        schueler = conn.execute('''
            SELECT s.jahrgang_id, a.jahrgang, s.vorname, s.nachname, s.email, 
                   COALESCE(s.datenschutz_einwilligung, 1) as datenschutz_einwilligung, 
                   COALESCE(s.datenschutz_datum, s.erstellt_am) as datenschutz_datum, 
                   s.erstellt_am
            FROM schueler_daten s
            JOIN abitur_jahrgaenge a ON s.jahrgang_id = a.id
            ORDER BY a.jahrgang DESC, s.nachname, s.vorname
        ''').fetchall()
    except Exception as e:
        flask.flash(f'Fehler beim Abrufen der Schülerdaten: {str(e)}', 'error')
        return flask.redirect(flask.url_for('admin_dashboard'))

    conn.close()
    
    # CSV-Datei erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Header schreiben
    writer.writerow([
        'Jahrgang',
        'Vorname', 
        'Nachname',
        'E-Mail',
        'Datenschutz erteilt',
        'Datenschutz Datum',
        'Registriert am'
    ])
    
    # Datenzeilen schreiben
    for schueler_eintrag in schueler:
        writer.writerow([
            schueler_eintrag['jahrgang'],
            schueler_eintrag['vorname'],
            schueler_eintrag['nachname'],
            schueler_eintrag['email'],
            'Ja' if schueler_eintrag['datenschutz_einwilligung'] else 'Nein',
            schueler_eintrag['datenschutz_datum'],
            schueler_eintrag['erstellt_am']
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    # Dateiname mit aktuellem Datum
    heute = datetime.datetime.now().strftime('%Y-%m-%d')
    dateiname = f'schueler_export_{heute}.csv'
    
    response = flask.make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{dateiname}"'
    
    flask.flash(f'CSV-Export erfolgreich erstellt: {len(schueler)} Schüler exportiert', 'success')
    
    return response

@app.route('/admin/export/csv/<int:jahrgang_id>')
def admin_export_csv_jahrgang(jahrgang_id):
    """CSV-Export für einen bestimmten Jahrgang"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Jahrgang-Info abrufen
    jahrgang_info = conn.execute('SELECT jahrgang FROM abitur_jahrgaenge WHERE id = ?', (jahrgang_id,)).fetchone()
    
    if not jahrgang_info:
        flask.flash('Jahrgang nicht gefunden!', 'error')
        return flask.redirect(flask.url_for('admin_dashboard'))
    
    # Schülerdaten für diesen Jahrgang abrufen
    try:
        schueler = conn.execute('''
            SELECT s.jahrgang_id, a.jahrgang, s.vorname, s.nachname, s.email, 
                   COALESCE(s.datenschutz_einwilligung, 1) as datenschutz_einwilligung, 
                   COALESCE(s.datenschutz_datum, s.erstellt_am) as datenschutz_datum, 
                   s.erstellt_am
            FROM schueler_daten s
            JOIN abitur_jahrgaenge a ON s.jahrgang_id = a.id
            WHERE s.jahrgang_id = ?
            ORDER BY s.nachname, s.vorname
        ''', (jahrgang_id,)).fetchall()
    except Exception as e:
        flask.flash(f'Fehler beim Abrufen der Schülerdaten: {str(e)}', 'error')
        return flask.redirect(flask.url_for('admin_dashboard'))
    
    conn.close()
    
    if not schueler:
        flask.flash(f'Keine Schüler im Jahrgang {jahrgang_info["jahrgang"]} gefunden!', 'error')
        return flask.redirect(flask.url_for('admin_dashboard'))
    
    # CSV-Datei erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Header schreiben
    writer.writerow([
        'Jahrgang',
        'Vorname', 
        'Nachname',
        'E-Mail',
        'Datenschutz erteilt',
        'Datenschutz Datum',
        'Registriert am'
    ])
    
    # Datenzeilen schreiben
    for schueler_eintrag in schueler:
        writer.writerow([
            schueler_eintrag['jahrgang'],
            schueler_eintrag['vorname'],
            schueler_eintrag['nachname'],
            schueler_eintrag['email'],
            'Ja' if schueler_eintrag['datenschutz_einwilligung'] else 'Nein',
            schueler_eintrag['datenschutz_datum'],
            schueler_eintrag['erstellt_am']
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    # Dateiname mit Jahrgang und Datum
    heute = datetime.datetime.now().strftime('%Y-%m-%d')
    dateiname = f'schueler_jahrgang_{jahrgang_info["jahrgang"]}_{heute}.csv'
    
    response = flask.make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{dateiname}"'
    
    return response

@app.route('/admin/delete/<int:schueler_id>')
def admin_delete_schueler(schueler_id):
    """Lösche einen Schüler-Eintrag"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM schueler_daten WHERE id = ?', (schueler_id,))
    conn.commit()
    conn.close()
    
    flask.flash('Eintrag erfolgreich gelöscht!', 'success')
    return flask.redirect(flask.url_for('admin_dashboard'))

@app.route('/admin/benutzer')
def admin_benutzer():
    """Benutzerverwaltung"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    conn = get_db_connection()
    benutzer = conn.execute('SELECT id, benutzername FROM admins ORDER BY benutzername').fetchall()
    conn.close()
    
    return flask.render_template('admin_benutzer.html', benutzer=benutzer)

@app.route('/admin/benutzer/add', methods=['POST'])
def admin_add_benutzer():
    """Neuen Admin-Benutzer hinzufügen"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    benutzername = flask.request.form.get('benutzername')
    passwort = flask.request.form.get('passwort')
    passwort_wiederholen = flask.request.form.get('passwort_wiederholen')
    
    if not all([benutzername, passwort, passwort_wiederholen]):
        flask.flash('Alle Felder müssen ausgefüllt werden!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    if passwort != passwort_wiederholen:
        flask.flash('Passwörter stimmen nicht überein!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    if len(passwort) < 6:
        flask.flash('Passwort muss mindestens 6 Zeichen lang sein!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    # Benutzername validieren
    if len(benutzername) < 3:
        flask.flash('Benutzername muss mindestens 3 Zeichen lang sein!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    try:
        passwort_hash = hashlib.sha256(passwort.encode()).hexdigest()
        
        conn = get_db_connection()
        conn.execute('INSERT INTO admins (benutzername, passwort_hash) VALUES (?, ?)', 
                     (benutzername, passwort_hash))
        conn.commit()
        conn.close()
        
        flask.flash(f'Benutzer "{benutzername}" erfolgreich erstellt!', 'success')
    except sqlite3.IntegrityError:
        flask.flash('Benutzername bereits vergeben!', 'error')
    except Exception as e:
        flask.flash(f'Fehler beim Erstellen des Benutzers: {str(e)}', 'error')
    
    return flask.redirect(flask.url_for('admin_benutzer'))

@app.route('/admin/benutzer/change-password', methods=['POST'])
def admin_change_password():
    """Passwort eines Benutzers ändern"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    benutzer_id = flask.request.form.get('benutzer_id')
    altes_passwort = flask.request.form.get('altes_passwort')
    neues_passwort = flask.request.form.get('neues_passwort')
    neues_passwort_wiederholen = flask.request.form.get('neues_passwort_wiederholen')
    
    if not all([benutzer_id, altes_passwort, neues_passwort, neues_passwort_wiederholen]):
        flask.flash('Alle Felder müssen ausgefüllt werden!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    if neues_passwort != neues_passwort_wiederholen:
        flask.flash('Neue Passwörter stimmen nicht überein!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    if len(neues_passwort) < 6:
        flask.flash('Neues Passwort muss mindestens 6 Zeichen lang sein!', 'error')
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    try:
        altes_passwort_hash = hashlib.sha256(altes_passwort.encode()).hexdigest()
        neues_passwort_hash = hashlib.sha256(neues_passwort.encode()).hexdigest()
        
        conn = get_db_connection()
        
        # Prüfen ob altes Passwort korrekt ist
        benutzer = conn.execute('SELECT benutzername FROM admins WHERE id = ? AND passwort_hash = ?',
                               (benutzer_id, altes_passwort_hash)).fetchone()
        
        if not benutzer:
            flask.flash('Altes Passwort ist falsch!', 'error')
            conn.close()
            return flask.redirect(flask.url_for('admin_benutzer'))
        
        # Neues Passwort setzen
        conn.execute('UPDATE admins SET passwort_hash = ? WHERE id = ?',
                     (neues_passwort_hash, benutzer_id))
        conn.commit()
        conn.close()
        
        flask.flash(f'Passwort für "{benutzer["benutzername"]}" erfolgreich geändert!', 'success')
    except Exception as e:
        flask.flash(f'Fehler beim Ändern des Passworts: {str(e)}', 'error')
    
    return flask.redirect(flask.url_for('admin_benutzer'))

@app.route('/admin/benutzer/delete/<int:benutzer_id>')
def admin_delete_benutzer(benutzer_id):
    """Admin-Benutzer löschen"""
    if 'admin_logged_in' not in flask.session:
        return flask.redirect(flask.url_for('admin_login'))
    
    # Prüfen ob es der einzige Admin ist
    conn = get_db_connection()
    admin_count = conn.execute('SELECT COUNT(*) as count FROM admins').fetchone()
    
    if admin_count['count'] <= 1:
        flask.flash('Der letzte Admin-Benutzer kann nicht gelöscht werden!', 'error')
        conn.close()
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    # Prüfen ob es der aktuell eingeloggte Benutzer ist
    if int(benutzer_id) == flask.session.get('admin_id'):
        flask.flash('Sie können sich nicht selbst löschen!', 'error')
        conn.close()
        return flask.redirect(flask.url_for('admin_benutzer'))
    
    try:
        benutzer = conn.execute('SELECT benutzername FROM admins WHERE id = ?', (benutzer_id,)).fetchone()
        
        if benutzer:
            conn.execute('DELETE FROM admins WHERE id = ?', (benutzer_id,))
            conn.commit()
            flask.flash(f'Benutzer "{benutzer["benutzername"]}" erfolgreich gelöscht!', 'success')
        else:
            flask.flash('Benutzer nicht gefunden!', 'error')
    except Exception as e:
        flask.flash(f'Fehler beim Löschen des Benutzers: {str(e)}', 'error')
    finally:
        conn.close()
    
    return flask.redirect(flask.url_for('admin_benutzer'))



if __name__ == '__main__':
    app.run(port=80, debug=True, host='0.0.0.0')
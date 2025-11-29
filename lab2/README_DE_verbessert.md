# **Labor 2** - Asynchrone Kommunikation mit Remote Procedure Calls (RPC)

## 📋 Was lernen Sie in diesem Labor?

In diesem Labor lernen Sie, wie Anwendungen in verteilten Systemen miteinander kommunizieren können, als ob sie lokale Funktionen aufrufen würden - das nennt man **Remote Procedure Call (RPC)**.

### Lernziele

✅ **Verstehen**, wie RPCs funktionieren und wann man sie einsetzt  
✅ **Implementieren** einer eigenen RPC-Middleware  
✅ **Arbeiten** mit dem `lab_channel` Kommunikationsmechanismus  
✅ **Programmieren** mit Python Threads für asynchrone Verarbeitung  
✅ **Unterscheiden** zwischen synchronen und asynchronen RPCs

---

## 🎯 Das große Bild

### Was ist ein RPC?

Stellen Sie sich vor:
- **Computer A** möchte eine Funktion ausführen, die auf **Computer B** liegt
- **RPC** ermöglicht es Computer A, diese Funktion so aufzurufen, als wäre sie lokal
- Die gesamte Netzwerkkommunikation wird automatisch im Hintergrund erledigt

### Synchron vs. Asynchron

**Synchroner RPC** (wie ein Telefonanruf):
```
Client: "Berechne mir 5 + 3!"
[Client wartet... wartet... wartet...]
Server: "Das Ergebnis ist 8"
Client: "Danke!" [macht weiter]
```

**Asynchroner RPC** (wie eine SMS):
```
Client: "Berechne mir 5 + 3!"
Server: "OK, mache ich!" (ACK)
[Client kann weitermachen mit anderen Dingen]
Server: "Fertig! Das Ergebnis ist 8"
Client: [Callback-Funktion wird aufgerufen] "Danke!"
```

---

## 🔧 1. Vorbereitung

### 1.1. Benötigte Software

Falls noch nicht geschehen (von Labor 1):
- ✅ Git
- ✅ Python 3
- ✅ Pipenv
- ✅ VS Code mit Remote Containers Extension
- ✅ Jupyter

**NEU für Labor 2:**
- ✅ **Redis** - Eine Datenbank für unsere Nachrichtenwarteschlangen

> 💡 **Tipp**: Wenn Sie VS Code mit Dev Container verwenden, ist Redis bereits installiert!

### 1.2. Projekt Setup

#### Option A: Erstmalig klonen
```bash
mkdir -p ~/git
cd ~/git
git clone https://github.com/zirpins/vs2lab.git
```

#### Option B: Bestehendes Repo aktualisieren
```bash
cd ~/git/vs2lab
git pull
```

### 1.3. Python-Umgebung einrichten

```bash
cd ~/git/vs2lab
pipenv install  # Installiert alle benötigten Pakete
```

### 1.4. Zum Labor-Verzeichnis wechseln

```bash
cd ~/git/vs2lab/lab2
```

---

## 📚 2. Beispiele verstehen (Theorie & Praxis)

### 2.1. Beispiel 1: RPyC Framework (Optional zum Ausprobieren)

**Was macht es?**
Ein fertiges RPC-Framework, das zeigt, wie einfach RPCs sein können.

**Dateien:**
```
lab2/rpyc/
├── server.py      # Server mit DBList Service
├── client.py      # Client ruft Server-Funktionen auf
├── constRPYC.py   # Konfiguration (Host, Port)
└── context.py     # Bibliotheks-Einbindung
```

**Ausprobieren:**

Terminal 1 - Server starten:
```bash
cd ~/git/vs2lab/lab2/rpyc
pipenv run python server.py
```

Terminal 2 - Client starten:
```bash
cd ~/git/vs2lab/lab2/rpyc
pipenv run python client.py
```

**Was passiert?**
Der Client ruft Funktionen auf dem Server auf, als wären sie lokal. Das Framework versteckt die gesamte Netzwerkkommunikation!

---

### 2.2. Beispiel 2: Eigene RPC-Implementierung (WICHTIG!)

**Was macht es?**
Eine selbstgebaute RPC-Middleware - hier sehen Sie, was unter der Haube passiert!

**Dateien:**
```
lab2/rpc/
├── rpc.py         # Client-Stub und Server-Stub Klassen
├── runcl.py       # Client-Prozess
├── runsrv.py      # Server-Prozess
└── constRPC.py    # Konfiguration
```

#### 2.2.1. Der Kommunikationskanal (`lab_channel`)

**Was ist das?**
- Ein **Message Queue System** basierend auf Redis
- Erlaubt **asynchrone Kommunikation** zwischen Prozessen
- Nachrichten werden **persistent** gespeichert (gehen nicht verloren)

**Wie funktioniert es?**

```python
# Sender
channel.send_to(recipient_id, message)

# Empfänger  
message = channel.receive_from(sender_id)
```

**Channel-Beispiel ausprobieren:**

Terminal 1 - Redis starten:
```bash
redis-server
```

Terminal 2 - Server starten:
```bash
cd ~/git/vs2lab/lab2/channel
pipenv run python runsrv.py
```

Terminal 3 - Client starten:
```bash
cd ~/git/vs2lab/lab2/channel
pipenv run python runcl.py
```

**Was beobachten Sie?**
- Client sendet Nachricht an Server
- Server empfängt und antwortet
- Alles über Redis-Warteschlangen!

#### 2.2.2. RPC-Beispiel mit lab_channel

**Jetzt das Ganze kombinieren!**

Terminal 1 - Redis (falls noch nicht läuft):
```bash
redis-server
```

Terminal 2 - RPC Server:
```bash
cd ~/git/vs2lab/lab2/rpc
pipenv run python runsrv.py
```

Terminal 3 - RPC Client:
```bash
cd ~/git/vs2lab/lab2/rpc
pipenv run python runcl.py
```

**Was passiert hier?**
1. Client ruft `append("test")` auf dem Server auf
2. Client-Stub wandelt Aufruf in Nachricht um
3. Nachricht wird über `lab_channel` gesendet
4. Server-Stub empfängt Nachricht
5. Server führt die Funktion aus
6. Ergebnis wird zurückgesendet
7. Client erhält das Ergebnis

---

## 🎓 3. Ihre Programmieraufgabe: Asynchroner RPC

### 3.1. Das Problem

**Aktueller Zustand (Synchron):**
```
Client → Request → Server
Client [wartet blockiert] 
Server [arbeitet...]
Server → Reply → Client
Client [kann weitermachen]
```

Problem: Wenn der Server lange braucht, verschwendet der Client wertvolle Zeit mit Warten!

**Ihr Ziel (Asynchron):**
```
Client → Request → Server
Server → ACK → Client
Client [kann sofort weitermachen!]
Server [arbeitet...]
Server → Result → Client
Client [Callback verarbeitet Ergebnis]
```

### 3.2. Was Sie konkret tun müssen

#### Schritt 1: Server erweitern

**In `rpc/rpc.py` - Server-Klasse:**

1. ✅ Server empfängt Request
2. ✅ Server sendet **sofort** ein ACK (Acknowledgement) zurück
3. ✅ Server **wartet 10 Sekunden** (simuliert lange Berechnung)
4. ✅ Server führt die eigentliche Funktion aus
5. ✅ Server sendet das Ergebnis zurück

**Pseudo-Code:**
```python
def handle_request(self, request):
    # 1. Request empfangen
    
    # 2. ACK senden
    self.channel.send_to(client_id, "ACK")
    
    # 3. Simuliere lange Berechnung
    time.sleep(10)
    
    # 4. Funktion ausführen
    result = self.append(data)
    
    # 5. Ergebnis senden
    self.channel.send_to(client_id, result)
```

#### Schritt 2: Client erweitern

**In `rpc/rpc.py` - Client-Klasse:**

1. ✅ Client sendet Request
2. ✅ Client wartet auf ACK
3. ✅ Client startet einen **Thread**, der auf das Ergebnis wartet
4. ✅ Haupt-Thread kann **weitermachen** (z.B. Konsolenausgaben)
5. ✅ Wenn Ergebnis kommt → **Callback-Funktion** wird aufgerufen

**Pseudo-Code:**
```python
def async_call(self, method, params, callback_function):
    # 1. Request senden
    self.channel.send_to(server_id, request)
    
    # 2. ACK empfangen
    ack = self.channel.receive_from(server_id)
    
    # 3. Thread für Ergebnis starten
    def wait_for_result():
        result = self.channel.receive_from(server_id)
        callback_function(result)  # Callback aufrufen!
    
    thread = threading.Thread(target=wait_for_result)
    thread.start()
    
    # 4. Sofort zurückkehren (nicht blockieren!)
    return thread
```

#### Schritt 3: Client-Skript anpassen

**In `rpc/runcl.py`:**

1. ✅ Callback-Funktion definieren
2. ✅ Asynchronen RPC aufrufen
3. ✅ Während des Wartens: Ausgaben machen (zeigen, dass Client aktiv ist)
4. ✅ Auf Thread-Ende warten (damit Programm nicht zu früh beendet)

**Beispiel:**
```python
def meine_callback_funktion(result):
    print(f"✅ Ergebnis erhalten: {result}")

# Asynchronen Aufruf starten
thread = client.async_append("test_daten", meine_callback_funktion)

# Client ist aktiv während Server arbeitet
for i in range(15):
    print(f"⏱️ Client arbeitet... ({i+1})")
    time.sleep(1)

# Warten bis Callback fertig ist
thread.join()
print("🎉 Alles fertig!")
```

### 3.3. Detaillierte Anforderungen

| Anforderung | Beschreibung | Wo |
|------------|--------------|-----|
| ✅ Asynchroner RPC | Implement ACK und Result Pattern | `rpc/rpc.py` |
| ✅ 10 Sek. Pause | Simuliere lange Server-Berechnung | `rpc/rpc.py` (Server) |
| ✅ Threading | Thread wartet auf Server-Antwort | `rpc/rpc.py` (Client) |
| ✅ Callback | Funktion verarbeitet Ergebnis | `rpc/runcl.py` |
| ✅ Konsolenausgabe | Zeige Client-Aktivität während Warten | `rpc/runcl.py` |
| ✅ Ergebnis ausgeben | Drucke finales Ergebnis | Callback-Funktion |

### 3.4. Tipps & Tricks

#### Threading in Python

**Einfaches Thread-Beispiel:**
```python
import threading
import time

def meine_aufgabe():
    print("Thread startet")
    time.sleep(2)
    print("Thread fertig")

# Thread erstellen
t = threading.Thread(target=meine_aufgabe)

# Thread starten
t.start()

# Hauptprogramm läuft weiter
print("Hauptprogramm macht weiter")

# Auf Thread warten
t.join()
print("Alles fertig")
```

**Threading-Beispiel anschauen:**
```bash
cd ~/git/vs2lab/lab2/threading
pipenv run python async_zip.py
```

#### Debugging-Tipps

1. **Logging nutzen:**
   ```python
   print("[CLIENT] Sende Request...")
   print("[SERVER] Empfange Request...")
   print("[CLIENT] ACK erhalten!")
   ```

2. **Schritt für Schritt testen:**
   - Erst nur ACK-Mechanismus
   - Dann Threading hinzufügen
   - Dann Callback implementieren

3. **Redis überwachen:**
   ```bash
   redis-cli MONITOR  # Zeigt alle Redis-Operationen
   ```

### 3.5. Beispiel-Ablauf

```
[CLIENT] 🚀 Starte asynchronen RPC...
[CLIENT] 📤 Sende Request an Server
[SERVER] 📥 Request empfangen
[SERVER] ✅ Sende ACK
[CLIENT] ✅ ACK empfangen! Kann weitermachen
[CLIENT] 🔄 Starte Background-Thread für Ergebnis
[CLIENT] ⏱️  Tue andere Dinge... (1/15)
[CLIENT] ⏱️  Tue andere Dinge... (2/15)
[CLIENT] ⏱️  Tue andere Dinge... (3/15)
[SERVER] ⏳ Berechne... (10 Sekunden)
[CLIENT] ⏱️  Tue andere Dinge... (10/15)
[SERVER] ✅ Berechnung fertig!
[SERVER] 📤 Sende Ergebnis
[CLIENT-THREAD] 📥 Ergebnis empfangen
[CLIENT-THREAD] 🎯 Callback wird aufgerufen
[CALLBACK] 🎉 Ergebnis: [1, 2, 3, 'test_daten']
[CLIENT] ⏱️  Tue andere Dinge... (15/15)
[CLIENT] 🏁 Programm beendet
```

---

## 📦 4. Abgabe

### Was einreichen?

1. ✅ Modifizierte Dateien:
   - `rpc/rpc.py`
   - `rpc/runcl.py`
   - `rpc/runsrv.py` (falls geändert)

2. ✅ Als **ZIP-Archiv** auf ILIAS hochladen

3. ✅ **Präsentation beim Dozenten**:
   - Redis starten
   - Server starten
   - Client starten
   - Ablauf erklären


### Checkliste vor Abgabe

- [x] Server sendet ACK sofort nach Request-Empfang
- [x] Server wartet 10 Sekunden vor Berechnung
- [x] Client verwendet Thread für Ergebnis-Empfang
- [x] Callback-Funktion wird korrekt aufgerufen
- [x] Client zeigt Aktivität während des Wartens
- [x] Ergebnis wird am Ende ausgegeben
- [x] Code ist kommentiert und verständlich
- [ ] Alles wurde getestet

---

## 🆘 Häufige Probleme

### Redis-Fehler: "Connection refused"

**Lösung:**
```bash
# Terminal 1: Redis starten
redis-server

# Terminal 2: Prüfen ob Redis läuft
redis-cli ping
# Sollte antworten: PONG
```

### Import-Fehler: "No module named 'lab_channel'"

**Lösung:**
```bash
# Stelle sicher, dass du im richtigen Verzeichnis bist
cd ~/git/vs2lab/lab2/rpc

# Stelle sicher, dass context.py korrekt ist
cat context.py
```

### Thread beendet sich nicht

**Lösung:**
```python
# Nutze Daemon-Threads ODER join()
thread = threading.Thread(target=wait_for_result)
thread.daemon = True  # Option 1: Daemon
thread.start()
# ODER
thread.join()  # Option 2: Explizit warten
```

---

## 📖 Weiterführende Ressourcen

- [Python Threading Dokumentation](https://docs.python.org/3/library/threading.html)
- [RPyC Framework](https://rpyc.readthedocs.io/en/latest/)
- [Redis Dokumentation](https://redis.io/documentation)
- [Asynchronous Programming Konzepte](https://realpython.com/async-io-python/)

---

**Viel Erfolg! 🚀**

# Mutex-System: Aufbau, Ablauf und Verhalten

## **Überblick**
- Ziel: Voll verteilter wechselseitiger Ausschluss (Mutex) mit Lamport-Uhren.
- Komponenten: Anwendung in [lab5/mutex/doit.py](lab5/mutex/doit.py) und Peer-Logik in [lab5/mutex/process.py](lab5/mutex/process.py).
- Kommunikation: Über das `lab_channel`-Framework (Redis) aus [lab5/mutex/context.py](lab5/mutex/context.py).
- Nachrichten und Typen: Definiert in [lab5/mutex/constMutex.py](lab5/mutex/constMutex.py).

## **Architektur**
- **Peers**: Mehrere Prozesse ("Peers") treten der Gruppe `proc` bei und koordinieren Zugriffe auf eine kritische Sektion.
- **Channel**: Gemeinsamer Kommunikationskanal (Redis) zum Multicast an andere Peers.
- **Lamport-Uhr**: Jeder Peer hält eine logische Uhr; jede Nachricht trägt einen Zeitstempel.
- **Warteschlange**: Jeder Peer verwaltet eine lokale, zeit-stabilisierte Queue der eingehenden Nachrichten.

## **Startablauf mit doit.py**
- **Parameter**: `m` (Adressbereich in Bits, default 8), `n` (Anzahl Prozesse, default 4). Optional über CLI: `python doit.py <m> <n>`.
- **Initialisierung**:
  - Redis-Channel wird geleert.
  - `multiprocessing` Startmethode `spawn` (Windows-kompatibel).
  - Zwei Barrieren: `bar1` (alle Peers haben Channel betreten), `bar2` (Bootstrap abgeschlossen).
- **Starten der Peers**:
  - Es werden `n` Prozesse erstellt; jeder erhält einen Namen (`Peer-i`) und zufälligen Verhaltenstyp (`ACTIVE` oder `PASSIVE`).
  - Jeder Prozess ruft `create_and_run()` auf: Channel anlegen, Peer-Klasse instanziieren, synchron warten (Barrieren), dann `proc.run()` starten.
- **Crash-Simulation**:
  - Nach ~10 Sekunden wird ein zufälliger Peer beendet (`terminate()` + `join()`), der Rest läuft weiter.

## **Peer-Verhalten in process.py**
- **Zustände**:
  - `self.clock`: Lamport-Uhr (Ganzzahl).
  - `self.queue`: Sortierte Liste von Nachrichten `(clock, process_id, type)`.
  - `self.all_processes` und `self.other_processes`: Mitgliederverwaltung.
- **Nachrichtentypen**:
  - `ENTER`: Antrag zum Eintritt in die kritische Sektion.
  - `ALLOW`: Erlaubnis, die CS zu betreten.
  - `RELEASE`: Freigabe der CS nach Benutzung.
  - `ALIVE`: Lebenszeichen zur Ausfallerkennung.
- **Aktives vs. passives Verhalten**:
  - `ACTIVE`: konkurriert periodisch um Eintritt in die CS.
  - `PASSIVE`: fordert nie Eintritt an, antwortet aber korrekt auf Koordinationsnachrichten.

## **Koordinationslogik (Lamport Mutex)**
- **ENTER senden**: Uhr ++, eigene `ENTER` in die Queue, Multicast an andere.
- **ALLOW senden**: Bei Empfang eines fremden `ENTER` wird Uhr ++ und `ALLOW` an den Anfragenden gesendet.
- **Zugangskriterium**:
  - Erstes Element der Queue ist die eigene `ENTER`-Nachricht.
  - Von allen anderen Prozessen liegt eine spätere Nachricht (entweder `ENTER` oder `ALLOW`) vor.
- **CS-Benutzung**:
  - Nach Erfüllung der Kriterien betritt der Peer die CS für eine zufällige Dauer.
  - Beim Verlassen sendet er `RELEASE` und bereinigt die Queue (alte `ENTER`/`ALLOW` entfernen).
- **Queue-Pflege**:
  - Alle Nachrichten werden nach `(clock, process_id, type)` sortiert.
  - Alte, führende `ALLOW`-Nachrichten werden entfernt.

## **Lamport-Uhrenregeln**
- **Senden/Empfangen**: `self.clock = max(self.clock, msg_clock) + 1`.
- **Monotonie**: Jede Aktion (Senden) erhöht die Uhr um 1.
- **Totale Ordnung**: Nachrichten werden durch `(clock, process_id)` total geordnet.

## **Ausfallerkennung und -behandlung**
- **ALIVE-Protokoll**:
  - Bei Zeitüberschreitung im Empfang: Peer sendet `ALIVE` und wartet kurz auf `ALIVE` anderer.
  - Empfangene `ALIVE`-Sender werden als lebendig markiert.
- **Unresponsive Peers**:
  - Peers ohne `ALIVE` werden aus `self.all_processes` und `self.other_processes` entfernt.
  - Alle Nachrichten dieser Peers werden aus der lokalen Queue gelöscht, um Blockaden (z.B. veraltete `ENTER`) zu vermeiden.
- **Wirkung**:
  - Das System bleibt weiter lauffähig, trotz simuliertem Prozessabsturz.

## **Ablauf von Nachrichten**
- **ENTER-Flow**:
  - Aktiver Peer sendet `ENTER` → andere Peers fügen in ihre Queue ein und antworten ggf. mit `ALLOW`.
- **ALLOW-Flow**:
  - Für den Anfragenden dient `ALLOW` als „spätere Nachricht“ und trägt zur Freigabekondition bei.
- **RELEASE-Flow**:
  - Nach der CS wird `RELEASE` gesendet, wodurch andere Peers die entsprechende `ENTER` entfernen.

## **Starten & Testen**
- **Redis** starten:
```bash
redis-server
```
- **Applikation** starten (aus dem Mutex-Ordner):
```bash
pipenv run python lab5/mutex/doit.py
```
- **Optional**: Prozessanzahl/Adressbits angeben:
```bash
pipenv run python lab5/mutex/doit.py 8 6
```

## **Hinweise für die Abgabe**
- **Logs**: Aktivieren/prüfen Sie die Logs (Info/Debug) zur Laufzeitbeobachtung.
- **Mehrfache Läufe**: Wegen Zufall (aktiv/passiv, Zeiten, Crash) mehrere Runs durchführen.
- **Stabilität**: Verifizieren, dass aktive und passive Peers korrekt koordinieren und Ausfälle maskiert werden.
- **Codepfade**: Relevante Implementierung in [lab5/mutex/process.py](lab5/mutex/process.py) und Steuerung in [lab5/mutex/doit.py](lab5/mutex/doit.py).
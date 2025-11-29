# **Labor 3** - Kommunikation über Nachrichten mit ZeroMQ

Im dritten Labor untersuchen wir eine konkrete Technik der
*Nachrichtenkommunikation*. Dabei werden zunächst drei Beispiele der wichtigsten
Kommunikationsmuster mit dem [ZeroMQ Framework](http://zeromq.org) (0MQ)
betrachtet. Eines davon, das *Paralel Pipeline* Muster, bildet in der Folge die
Grundlage der Programmieraufgabe. Dabei wird ein einfaches System für die
verteilte Datenverarbeitung realisiert, das dem Grundprinzip von MapReduce
Algorithmen aus der bekannten [Hadoop
Plattform](https://de.wikipedia.org/wiki/Apache_Hadoop) entspricht.

Allgemeine **Ziele** dieses Labors:

- Untersuchung höherwertiger Dienste zur Nachrichtenkommunikation
- Kennenlernen verschiedener Kommunikationsmuster
- Anwendung des verbreiteten ZeroMQ Frameworks
- Veranschaulichung von Konzepten der Massendatenverarbeitung

## 1. Vorbereitung

### 1.1. Software installieren

Für diese Aufgabe werden keine neuen Installationen benötigt.

### 1.2. Projekt aktualisieren

Aktualisieren Sie die Kopie des VS2Lab Repositories auf Ihrem Arbeitsrechner (alle Beispiele für Linux/Mac):

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
git add . # ggf. eigene Änderungen vormerken
git commit -m 'update' # ggf eigene Änderungen per Commit festschreiben
git checkout master # branch auswählen (falls nicht schon aktiv)
git pull # aktualisieren
```

### 1.3. Python Umgebung installieren

Hier hat sich nichts geändert. Ggf. aktualisieren wie folgt:

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
pipenv update
```

### 1.4. Beispielcode für diese Aufgabe

Wechseln Sie auf Ihrem Arbeitsrechner in das Unterverzeichnis dieser Aufgabe:

```bash
cd ~/git/vs2lab # angenommen hier liegt das vs2lab Repo
cd lab3
```

## 2. Beispiele: einfache und erweiterte Kommunikationsmuster

Das Labor beginnt mit einigen Beispielen zum Messaging mit 0MQ. Die Beispiele
zeigen die drei gängigsten 0MQ-Muster.

Allgemeine Beschreibungen der Muster und der dazugehörigen 0MQ Sockets finden
sich z.B. hier:

- [Request-Reply: Ask and Ye Shall
  Receive](https://zguide.zeromq.org/docs/chapter1/#Ask-and-Ye-Shall-Receive)
- [Publish-Subscribe: Getting the Message
  Out](https://zguide.zeromq.org/docs/chapter1/#Getting-the-Message-Out)
- [Parallel Pipeline: Divide and
  Conquer](https://zguide.zeromq.org/docs/chapter1/#Divide-and-Conquer)

### 2.1. Request-Reply

Das erste Beispiel zeigt, wie die gängige Request-Reply Kommunikation mit 0MQ
*Request-* und *Reply-Sockets* gegenüber den einfachen Berkeley Sockets
vereinfacht werden kann. 0MQ verwendet dabei Nachrichten statt Streams und es
wird keine Angabe der Übertragungsgröße benötigt. Ein Request Socket des Client
wird jeweils mit einem Reply Socket des Server gekoppelt.

Sie starten Server und Client nach dem nun schon bekannten Muster in zwei
Terminals.

#### Terminal1

```bash
cd ~/git/vs2lab/lab3/zmq1 # angenommen hier liegt das vs2lab Repo
pipenv run python server.py
```

#### Terminal2

```bash
cd ~/git/vs2lab/lab3/zmq1 # angenommen hier liegt das vs2lab Repo
pipenv run python client.py
```

Wir wollen nun noch etwas experimentieren. Zunächst schauen wir uns an, was es
bedeutet, dass 0MQ asynchron arbeitet. Probieren Sie dazu folgende Kombination
aus:

1. Terminal1: `pipenv run python client.py`
2. Terminal2: `pipenv run python server.py`

Die Kopplung von je zwei Sockets können Sie durch folgendes erweiterte
Experiment nachverfolgen:

1. Terminal1: `pipenv run python client.py`
2. Terminal2: `pipenv run python client1.py`
3. Terminal3: `pipenv run python server.py`

**Aufgabe Lab3.1:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

**Antwort Lab3.1:**

**Experiment 1: Client startet vor Server**

Beobachtung:
- Der Client sendet seine erste Request und wartet (blockiert bei `recv()`)
- Wenn der Server danach gestartet wird, empfängt er alle gepufferten Nachrichten
- Der Client erhält dann seine Responses und kann normal weiterarbeiten

Erklärung:
ZeroMQ arbeitet **asynchron** mit internem Message-Buffering. Wenn der Client eine 
Nachricht sendet bevor der Server läuft, wird die Nachricht nicht verloren, sondern 
in einem internen Puffer zwischengespeichert. Sobald der Server startet und den 
Socket bindet, werden die gepufferten Nachrichten zugestellt. Der Client blockiert 
bei `recv()` bis eine Antwort vom Server kommt. Dies zeigt die **Entkopplung** von 
Sender und Empfänger - sie müssen nicht gleichzeitig aktiv sein.

**Experiment 2: Zwei Clients auf einen Server**

Beobachtung:
- `client.py` verbindet sich mit PORT1 und sendet "Hello world"
- `client1.py` verbindet sich mit PORT2 und sendet "Hello vs2lab"
- Der Server bindet beide Ports (PORT1 und PORT2) und empfängt Nachrichten von beiden
- Die Nachrichten werden abwechselnd verarbeitet (fair queuing)

Erklärung:
Ein einzelner ZeroMQ REP-Socket kann an **mehrere Adressen binden** (hier PORT1 und 
PORT2). Jeder REQ-Socket (Client) wird mit genau einem REP-Socket (Server) gekoppelt.
Der Server verarbeitet die eingehenden Requests in einer fairen Reihenfolge 
(**round-robin**). Dies demonstriert das Request-Reply-Muster mit mehreren Clients:
Jeder Request bekommt genau eine Reply, und die Kopplung zwischen REQ- und REP-Socket
stellt sicher, dass die Antwort zum richtigen Client zurückgeht.

### 2.2. Publish-Subscribe

Mit dem Publish-Subscribe Muster lässt sich *1-n Kommunikation* (ein Sender, n
Empfänger) realisieren. Zudem können Nachrichten nach Themen gefiltert werden.

Wechseln Sie zunächst in das entsprechende Verzeichnis:

```bash
cd ~/git/vs2lab/lab3/zmq2 # angenommen hier liegt das vs2lab Repo
```

#### Experiment1

1. Terminal1: `pipenv run python server.py`
2. Terminal2: `pipenv run python client.py`
3. Terminal3: `pipenv run python client.py`

#### Experiment 2

1. Terminal1: `pipenv run python server.py`
2. Terminal2: `pipenv run python client.py`
3. Terminal3: `pipenv run python client1.py`

**Aufgabe Lab3.2:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

**Antwort Lab3.2:**

**Experiment 1: Zwei identische Subscriber (beide subscriben TIME)**

Beobachtung:
- Der Server sendet alle 5 Sekunden zwei Nachrichten: TIME und DATE
- Beide Clients empfangen exakt die gleichen TIME-Nachrichten mit identischen Zeitstempeln
- Jeder Client erhält 5 TIME-Nachrichten

Erklärung:
Im Publish-Subscribe-Muster sendet ein **Publisher (PUB-Socket)** Nachrichten an alle 
verbundenen **Subscriber (SUB-Sockets)**. Dies ist **Broadcasting** - jede Nachricht 
wird an alle Subscriber kopiert, die das entsprechende Topic abonniert haben. Beide 
Clients subscriben "TIME" (`setsockopt(zmq.SUBSCRIBE, b"TIME")`), daher empfangen 
beide alle TIME-Nachrichten. Die DATE-Nachrichten werden ignoriert, da sie nicht 
abonniert sind.

**Experiment 2: Zwei Subscriber mit unterschiedlichen Topics**

Beobachtung:
- `client.py` subscribt "TIME" und empfängt nur TIME-Nachrichten
- `client1.py` subscribt "DATE" und empfängt nur DATE-Nachrichten
- Beide empfangen ihre Nachrichten gleichzeitig, aber gefiltert nach Topic
- `client1.py` beendet sich schneller (nur 3 Iterationen statt 5)

Erklärung:
ZeroMQ ermöglicht **Topic-basierte Filterung**. Der Publisher sendet beide Nachrichtentypen
(TIME und DATE), aber jeder Subscriber empfängt nur die Nachrichten, die mit seinem 
abonnierten Prefix übereinstimmen. Dies zeigt die Stärke des Pub-Sub-Musters: 
**selektives Empfangen** von Nachrichten ohne dass der Publisher wissen muss, 
wer was empfängt. Die Filterung erfolgt effizient auf Subscriber-Seite.

### 2.3. Parallel Pipeline

Das letzte Beispiel zeigt die Verteilung von Nachrichten von mehreren Sendern
auf mehrere Empfänger. Sogenannte 'Farmer' (`tasksrc.py`) erstellen Aufgaben
('Tasks') die von einer Menge von 'Workern' (`taskwork.py`) verarbeitet werden.
Die Tasks eines Farmers können an jeden Worker gehen und Worker akzeptieren
Tasks von jedem Farmer. Bei mehreren Alternativen Farmer/Worker Prozessen werden
die Tasks gleichverteilt.

`tasksrc.py` wird mit der Farmer-ID (1 oder 2) als Parameter gestartet. Jede
Farmer-ID darf nur einmal verwendet werden, da sie einen *PUSH-Socket* bindet.

`taskwork.py` wird mit der Worker-ID (beliebig) als Parameter gestartet. Die
Worker-ID dient nur der Anzeige. Es können beliebig viele Worker gestartet
werden, die jeweils mit ihrem *PULL-Sockets* die beiden Farmer kontaktieren.

Wechseln Sie zunächst in das entsprechende Verzeichnis:

```bash
cd ~/git/vs2lab/lab3/zmq3 # angenommen hier liegt das vs2lab Repo
```

Gehen sie nun wie folgt vor:

#### Experiment1

1. Terminal1: `pipenv run python tasksrc.py 1`
2. Terminal2: `pipenv run python tasksrc.py 2`
3. Terminal3: `pipenv run python taskwork.py 1`

#### Experiment 2

1. Terminal1: `pipenv run python taskwork.py 1`
2. Terminal2: `pipenv run python taskwork.py 2`
3. Terminal3: `pipenv run python tasksrc.py 1`

**Aufgabe Lab3.3:** Erklären Sie das Verhalten der Systeme in den beiden
Experimenten.

**Antwort Lab3.3:**

**Experiment 1: Farmer zuerst, dann Worker**

Beobachtung:
- Beide Farmer (1 und 2) senden je 100 Tasks
- Ein einzelner Worker empfängt alle 200 Tasks
- Die Tasks kommen abwechselnd von Farmer 1 und Farmer 2 (round-robin)
- Beispiel: "from 1", "from 2", "from 1", "from 2", ...

Erklärung:
Im **Parallel Pipeline-Muster** verwenden Farmer **PUSH-Sockets** (senden) und Worker 
**PULL-Sockets** (empfangen). Der Worker verbindet sich mit beiden Farmern 
(`pull_socket.connect(address1)` und `pull_socket.connect(address2)`). ZeroMQ verteilt 
eingehende Nachrichten von mehreren Sendern fair auf die Pull-Sockets (**fair queuing**).
Da nur ein Worker aktiv ist, empfängt er alle Tasks von beiden Farmern in gleichmäßiger
Verteilung.

**Experiment 2: Worker zuerst, dann nur ein Farmer**

Beobachtung:
- Nur Farmer 1 sendet 100 Tasks
- Zwei Worker empfangen die Tasks
- Jeder Worker bekommt ca. 50 Tasks (gleichmäßige Verteilung)
- Alle Tasks kommen nur "from 1"

Erklärung:
Der PUSH-Socket des Farmers verteilt seine Nachrichten gleichmäßig an alle verbundenen
PULL-Sockets (**load balancing / round-robin**). Farmer 1 sendet abwechselnd an 
Worker 1 und Worker 2. Dies zeigt die Stärke des Pipeline-Musters: **automatische 
Lastverteilung** für parallele Verarbeitung. Die Worker müssen nicht wissen, wie viele
Farmer existieren, und die Farmer müssen nicht wissen, wie viele Worker verfügbar sind.

## 3 Aufgabe

In der Programmieraufgabe soll das Parallel Pipeline Muster verwendet werden, um
die verteilte Verarbeitung von Textdaten zu realisieren.

## 3.1 Übersicht

Wir wollen das berühmte **Wordcount** Beispiel für *Hadoop MapReduce* mit 0MQ
nachprogrammieren (näherungsweise). Das Prinzip ist wie folgt:

- Das verteilte System besteht aus einem zentralen 'Split'-Prozess ('Splitter'),
  einer variablem Menge von 'Map'-Prozessen ('Mapper') und einer festen Menge
  von 'Reduce'-Prozessen ('Reducer').
- Der Splitter lädt aus einer Datei zeilenweise Sätze aus und verteilt sie als
  Nachrichten gleichmäßig an die die Mapper.
- Ein Mapper nimmt jeweils Sätze entgegen. Jeder Satz wird dann zunächst in
  seine Wörter zerlegt. Schließlich ordnet der Mapper jedes Wort nach einem
  festen Schema genau einem der Reducer zu und sendet es als Nachricht an
  diesen.
- Ein Reducer sammelt die an ihn geschickten Wörter ein und zählt sie. Beachten
  sie: durch das feste zuordnungsschema kommen alle gleichen Wörter beim selben
  Reducer an und dieser Zählt 'seine' Wörter also garantiert komplett. Das
  Gesamtergebnis ergibt sich aus der Vereinigung der Teilergebnisse aller
  Reducer.

## 3.2 Aufgabe und Anforderungen kurz und knapp

Sie sollen die oben beschriebenen Prozesse als Python Skripte implementieren und
die Kommunikation zwischen diesen mit dem 0MQ Parallel Pipeline Muster
realisieren. Verwenden Sie:

- einen Splitter
- drei Mapper
- zwei Reducer

Der Splitter kann entweder eine Datei lesen oder die Sätze zufällig generieren.
Der Reducer soll bei jeder Aktualisierung den aktuellen Zähler des neuen Wortes
ausgeben.

### 3.3 Tipps

Neben dem dritten Beispiel liefert die Beschreibung in

- [Parallel Pipeline: Divide and
  Conquer](https://zguide.zeromq.org/docs/chapter1/#Divide-and-Conquer)

ein nützliches Beispiel, an dem Sie sich orientieren können.

... stay tuned (Hinweise zur Installation/Konfiguration im Labor-README)

### 3.4 Abgabe

Die Abgabe erfolgt durch Abnahme durch einen Dozenten. Packen Sie den kompletten
Code zudem als Zip Archiv und laden Sie dieses im ILIAS hoch.

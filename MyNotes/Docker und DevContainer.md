# 💻 Was sind Dev Container und Docker?

## 🐳 Docker
Docker ist eine Plattform, die es ermöglicht, Anwendungen in Containern zu verpacken, bereitzustellen und auszuführen.

Container sind isolierte, portable Umgebungen, die alles Notwendige zur Ausführung einer Anwendung (Code, Laufzeitumgebung, Systemwerkzeuge, Bibliotheken und Einstellungen) enthalten.

Sie sind leichter und starten schneller als herkömmliche virtuelle Maschinen (VMs), da sie den Kernel des Host-Betriebssystems teilen, anstatt ein komplettes Betriebssystem zu emulieren.

## 📦 Dev Container (VS Code Remote Containers)
Ein Dev Container ist ein Docker-Container, der speziell für die Entwicklung konfiguriert ist.

Die VS Code Remote Containers-Erweiterung ermöglicht es Ihnen, direkt in diesem Container zu arbeiten, als ob er Ihr lokales System wäre.

Der Container enthält alle für Ihr Projekt erforderlichen Tools und Abhängigkeiten (z.B. Git, Python 3, Pipenv, Jupyter), die im vs2lab Repository vordefiniert sind.

Dies gewährleistet, dass jeder Entwickler die exakt gleiche Umgebung hat, was Probleme wie "Bei mir funktioniert es aber!" vermeidet.
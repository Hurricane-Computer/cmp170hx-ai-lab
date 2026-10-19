# CMP 170HX AI Research Lab

**Direkte Modellübertragung, 19. Oktober 2026:** Echte CUDA-/PyTorch-Puffer und die Pipeline-Tensoren von R3 V3 BF16 lassen sich zwischen der 40er und der 64er direkt kopieren. Sämtliche übertragenen Modelltensoren bestehen den vollständigen Prüfsummenvergleich. Mit wiederverwendetem Kopierkanal erreicht der Modelllauf jetzt 18,18 Token/s; die frühere Vergleichsmessung über den Arbeitsspeicher lag bei 20,10. Kleine Summen- und Zusammenfügeoperationen auf beiden Karten bestehen ebenfalls vollständige GPU-Prüfungen. Ein echter TP2-Modelllauf ist inzwischen ebenfalls datenbelegt; mit voller Prüfung ist er jedoch deutlich langsamer als SHM (1,12 gegenüber 17,11 Token/s im gesonderten Vergleich mit maximal 32 Ausgabetokens). Beide Karten behalten 64 MiB BAR1; keine BIOS-Änderung nötig. Der eigene Adapter wurde gegen die bisherige Übertragung über den Arbeitsspeicher gemessen. Normales CUDA/NCCL meldet weiterhin keine Peer-Unterstützung. Prüfaufwand, experimenteller Umfang und offene Grenzen bleiben ausdrücklich sichtbar. [Messwerte und Methode](docs/cuda-application-transport.md).

Unser öffentliches Forschungstagebuch zu Speicher, Recheneinheiten, Firmware und KI-Einsatz der CMP 170HX. Die Arbeit wird mit KI-Unterstützung durchgeführt; entscheidend sind nachvollziehbare Belege.

[English](README.md) · [Erkenntnisse](docs/findings.md) · [Versuche](docs/experiments.md) · [Offene Fragen](docs/roadmap.md)

## CMP40-Speicher übertaktet: 1215 → 1350 MHz

**Unsere 40-GiB-CMP mit Samsung-HBM (`10de:2082`) hat bisher 1350 statt ursprünglich 1215 MHz erreicht: plus 11,11 %.** Den Takteingang haben wir aus dem ursprünglichen Initialisierungscode der Karte nachvollzogen. Die Stufen 1242, 1269, 1296, 1323 und 1350 MHz haben jeweils einen kurzen Datenvergleich bestanden. Ein BIOS-Flash war dafür nicht nötig.

**Die Forschung läuft seit dem 17. Oktober wieder: 1350 MHz ist eine getestete Stufe, keine ermittelte Obergrenze.** Langzeitstabilität, vollständiger Speicher, Bandbreitengewinn und LLM-Beschleunigung sind damit noch nicht nachgewiesen. Die Einstellung ist flüchtig. [Methode und Ergebnisse](docs/clocks.md) sowie [bereinigte Versuchsdatensätze](data/clock-trials.json) halten den genauen Umfang fest.

Eine weltweite Erstheit behaupten wir nicht: Es gibt bereits einen [früheren Besitzerbericht, der ausdrücklich eine 40-GB-Übertaktung beschreibt](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/). Fremde Angaben und eigene Messungen bleiben getrennt.

Ein anschließender begrenzter Lasttest bei 1350 MHz ergab **1.53 TB/s** beim internen Kopieren und **1.54 TB/s** mit einem Streaming-Rechenkern, jeweils Lesen+Schreiben. Alle geprüften Ausgaben waren korrekt. [90-Sekunden-Test und Grenzen](docs/bandwidth-load.md).

## Stand: 17. Oktober 2026

Es sind noch keine zusätzlichen tatsächlich nutzbaren GiB oberhalb der bisherigen 40-/64-GiB-Basis und keine zusätzlichen funktionierenden SMs jenseits der bereits etablierten 74 nachgewiesen. Mehrere vermeintliche Hebel sind inzwischen genauer eingegrenzt.

Wir unterscheiden zwischen Vermutung, angekündigtem Erfolg, angenommenem Registerwert, geändertem Hardwarezustand, angezeigter Größe und wirklich nachgewiesen nutzbarem Speicher. Ein kurzer 64-MiB-Datenvergleich ist kein Volltest von 40 oder 64 GiB.

Die beiden untersuchten Varianten sind unterschiedlich: 2082 meldet Samsung-Speicher mit 8 GiB je vollständigem Stapel, 20c2 SK Hynix mit 16 GiB. Daraus folgt noch nicht, wie viele weitere Stapel physisch bestückt, erreichbar und funktionsfähig sind.

Die erste [P2P-Abfrage](docs/peer-memory.md) meldete mit dem damaligen Gasttreiber in keiner der sechs Kartenrichtungen Unterstützung. Die CMP64 war nach einem gezielten Reset wieder ansprechbar, meldete aber ihre 8-GiB-Grundkonfiguration; der frühere 64-GiB-Unlock wurde in diesem Start nicht wiederhergestellt. Das war der Stand vor den anschließenden [Treiberversuchen](docs/driver-candidates.md). Nach fünf fehlgeschlagenen Kandidaten funktioniert F: Die BAR1-Erzwingungen des Forks sind deaktiviert, beide CMPs starten wieder und melden 40 beziehungsweise 64 GiB. Beide und Blackwell haben je einen vollständigen 8-MiB-Zufallsdatenvergleich nach Hin-, Geräte- und Rückkopie bestanden. Bei der Wiederherstellung am 17. Oktober um 17:39 UTC meldeten CMP40 und CMP64 wieder 40/64 GiB bei 1215/1728 MHz. Zusätzliche Kapazität und P2P sind noch nicht gewonnen; die früheren 1350 MHz bleiben ein belegter vergangener Betriebspunkt.

**Neuer Speicherbefund:** Ein zusammenpassendes 80-GiB-Profil startete und ließ 41 GiB reservieren. Nach einem normalen Cache-Flush enthielten aber 512 KiB des unteren Prüffensters Daten aus dem oberen Fenster, obwohl dessen Eigenprüfung sauber blieb. Ein späterer GSP-Ausfall erforderte die erfolgreiche Rückkehr zu G. [Alias-Befund, Grenzen und Wiederherstellung](docs/cache-alias.md). Zusätzlicher nutzbarer Speicher ist damit nicht gewonnen; die großen Fremdberichte bleiben offen.

**48 GiB ist bei der CMP40 das erste Ziel, keine belegte Obergrenze.** Der fremde 77,5-GiB-Bericht hält die 80-GiB-Hypothese offen. Unser [Quellenabgleich und kleiner CPU-Gegenversuch](docs/capacity-evidence.md) trennen diesen Hinweis von den eigenen Alias-Befunden.

Das Repository wächst mit wichtigen neuen Ergebnissen. Dazu gehören auch erfolglose Versuche, damit wir bekannte Sackgassen nicht immer wieder ablaufen. Technische Berichte und öffentliche Primärquellen stehen in den verlinkten englischen Fachnotizen; bereinigte Messdaten liegen unter [data/](data/README.md).

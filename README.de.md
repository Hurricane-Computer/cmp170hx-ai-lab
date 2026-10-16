# CMP 170HX AI Research Lab

Unser öffentliches Forschungstagebuch zu Speicher, Recheneinheiten, Firmware und KI-Einsatz der CMP 170HX. Die Arbeit wird mit KI-Unterstützung durchgeführt; entscheidend sind nachvollziehbare Belege.

[English](README.md) · [Erkenntnisse](docs/findings.md) · [Versuche](docs/experiments.md) · [Offene Fragen](docs/roadmap.md)

## CMP40-Speicher übertaktet: 1215 → 1323 MHz

**Unsere 40-GiB-CMP mit Samsung-HBM (`10de:2082`) läuft jetzt mit 1323 statt ursprünglich 1215 MHz: plus 8,89 %.** Den Takteingang haben wir aus dem ursprünglichen Initialisierungscode der Karte nachvollzogen. Die Stufen 1242, 1269, 1296 und 1323 MHz haben jeweils einen kurzen Datenvergleich bestanden. Ein BIOS-Flash war dafür nicht nötig.

**Die Forschung läuft weiter: 1323 MHz ist eine getestete Stufe, keine ermittelte Obergrenze.** Langzeitstabilität, vollständiger Speicher, Bandbreitengewinn und LLM-Beschleunigung sind damit noch nicht nachgewiesen. Die Einstellung ist flüchtig. [Methode und Ergebnisse](docs/clocks.md) sowie [bereinigte Versuchsdatensätze](data/clock-trials.json) halten den genauen Umfang fest.

Eine weltweite Erstheit behaupten wir nicht: Es gibt bereits einen [früheren Besitzerbericht, der ausdrücklich eine 40-GB-Übertaktung beschreibt](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/). Fremde Angaben und eigene Messungen bleiben getrennt.

## Stand: 16. Oktober 2026

Es sind noch keine zusätzlichen tatsächlich nutzbaren GiB oberhalb der bisherigen 40-/64-GiB-Basis und keine zusätzlichen funktionierenden SMs jenseits der bereits etablierten 74 nachgewiesen. Mehrere vermeintliche Hebel sind inzwischen genauer eingegrenzt.

Wir unterscheiden zwischen Vermutung, angekündigtem Erfolg, angenommenem Registerwert, geändertem Hardwarezustand, angezeigter Größe und wirklich nachgewiesen nutzbarem Speicher. Ein kurzer 64-MiB-Datenvergleich ist kein Volltest von 40 oder 64 GiB.

Die beiden untersuchten Varianten sind unterschiedlich: 2082 meldet Samsung-Speicher mit 8 GiB je vollständigem Stapel, 20c2 SK Hynix mit 16 GiB. Daraus folgt noch nicht, wie viele weitere Stapel physisch bestückt, erreichbar und funktionsfähig sind.

Das Repository wächst mit wichtigen neuen Ergebnissen. Dazu gehören auch erfolglose Versuche, damit wir bekannte Sackgassen nicht immer wieder ablaufen. Technische Berichte und öffentliche Primärquellen stehen in den verlinkten englischen Fachnotizen; bereinigte Messdaten liegen unter [data/](data/README.md).

# CMP 170HX AI Research Lab

Unser öffentliches Forschungstagebuch zu Speicher, Recheneinheiten, Firmware und KI-Einsatz der CMP170HX. Die Arbeit wird mit KI-Unterstützung durchgeführt; entscheidend sind nachvollziehbare Belege.

[English](README.md) · [Erkenntnisse](docs/findings.md) · [Versuche](docs/experiments.md) · [Offene Fragen](docs/roadmap.md)

**Stand16. Oktober2026:** Es sind noch keine zusätzlichen tatsächlich nutzbaren GiB oberhalb der bisherigen40-/64-GiB-Basis und keine zusätzlichen funktionierenden SMs jenseits der bereits etablierten74 nachgewiesen. Ein kleiner Speichertaktschritt auf der40er hat funktioniert. Mehrere vermeintliche Hebel sind inzwischen genauer eingegrenzt.

Wir unterscheiden konsequent zwischen Vermutung, angekündigtem Erfolg, angenommenem Registerwert, geändertem Hardwarezustand, angezeigter Größe und wirklich nachgewiesen nutzbarem Speicher. Ein kurzer64-MiB-Datenvergleich ist kein Volltest von40 oder64GiB.

Die beiden untersuchten Varianten sind unterschiedlich:2082 meldet Samsung-Speicher mit8GiB je vollständigem Stapel,20c2 SKHynix mit16GiB. Daraus folgt noch nicht, wie viele weitere Stapel physisch bestückt, erreichbar und funktionsfähig sind.

Das Repository wächst mit wichtigen neuen Ergebnissen. Dazu gehören ausdrücklich auch erfolglose Versuche, damit wir bekannte Sackgassen nicht immer wieder ablaufen. Technische Berichte und öffentliche Primärquellen stehen in den verlinkten englischen Fachnotizen; bereinigte Messdaten liegen unter [data/](data/README.md).

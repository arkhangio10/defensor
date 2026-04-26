# Defensor — Demo Storyboard (3 min)

Built solo by Abel Mancilla (Lima) · Built with Opus 4.7 Hackathon · April 2026

---

## Beat 1 — The Human Hook (30 s)

**Say:**
> "Abner Rivera tenía 47 años. Su médico pidió una resonancia magnética en EsSalud.
> La cita llegó seis semanas tarde. Para entonces, el tumor era inoperable.
> Abner murió. Su familia nunca supo qué artículo de la ley los protegía.
> Defensor existe para que eso no vuelva a pasar."

**Screen:** blank page with just the title "Defensor" and the tagline
*"Te negaron atención. Nosotros sí la leemos."*

---

## Beat 2 — Live Document Read (60 s)

**Say:**
> "Esto es una foto tomada con un celular barato en la sala de espera de un hospital.
> Borrosa. Sin metadata. Tal como la tomaría Abner."

**Action:**
1. Open `https://defensor.vercel.app`
2. Tap the upload zone — pick `tests/fixtures/vision/fixture_abner_denial.png`
3. Click **Analizar documento**
4. Wait ~10 s — result page loads

**Point at the screen:**
> "Opus 4.7 con visión de 3.75 megapíxeles lee el documento.
> Extrae el nombre del paciente, la fecha, la especialidad denegada.
> Identifica que se violó el Artículo 15 de la Ley 29414 — derecho a atención oportuna.
> Y redacta la carta en registro legal peruano — lista para firmar y presentar."

**Backup:** if wifi fails, open the pre-loaded result page saved in browser history.

---

## Beat 3 — Follow-Up 100× Replay (30 s)

**Say:**
> "Pero presentar la queja es solo el día 1.
> Con Managed Agents, Defensor hace el seguimiento solo durante 25 días.
> Esto es lo que pasa en tiempo real — comprimido 100 veces."

**Action:** in the terminal (pre-run before demo):
```bash
source ../defensor/Scripts/activate
python - <<'EOF'
from agents.follow_up.agent import FollowUpAgent
from agents.memory.agent import MemoryAgent, StoredCaseData
import json, pathlib

# Load the Abner fixture case
cases = list(pathlib.Path("tmp/cases").glob("*.json"))
case = json.loads(cases[0].read_text()) if cases else None
if case:
    events = FollowUpAgent().replay_events(case["case_id"])
    for e in events:
        print(f"  Día {e['day']:>2} — {e['event_type']}: {e['notes'][:60]}")
EOF
```

**Show:** 5 lines printing — day 1 confirmation, day 7 reminder, day 15 reminder,
day 20 escalation to SUSALUD, day 25 closure summary.

---

## Beat 4 — Country Switch Peru → Colombia → Mexico (15 s)

**Say:**
> "Perú es el módulo primario. Pero el mismo motor funciona en toda la región."

**Action:** in the browser dev tools console on the result page (or show config files):
```
Peru  → Ley 29414 · SUSALUD · EsSalud / MINSA / EPS
Colombia → Tutela · Superintendencia Nacional de Salud
México  → Queja ante IMSS · CONAMED
```

**Show** `country-modules/colombia/config.json` and `country-modules/mexico/config.json`
side by side in the editor.

**Say:**
> "15 segundos. Un archivo JSON por país. Sin tocar el motor."

---

## Beat 5 — Close (15 s)

**Say:**
> "En América Latina, 200 millones de personas dependen de sistemas de salud
> que les niegan atención sin explicación legal.
> La mayoría no sabe que tiene derechos. Defensor los ayuda a ejercerlos.
>
> Como dijo la Defensoría del Pueblo del Perú:
> *'El derecho a la salud no termina en la receta — termina en la cura.'*"

**Screen:** end card with:
- `defensor.vercel.app`
- GitHub: `github.com/arkhangio10/defensor`
- *"Defensor no reemplaza a un abogado. Esta es información legal, no asesoría legal."*

---

## Pre-demo checklist

- [ ] Railway URL warm (hit `/` endpoint 10 min before)
- [ ] `fixture_abner_denial.png` loaded and ready to upload
- [ ] Pre-analyzed result page open in a browser tab (wifi backup)
- [ ] Terminal with venv activated, `replay_events` script ready to paste
- [ ] Country config files open in editor side by side
- [ ] Vercel URL confirmed live

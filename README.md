# Defensor

**Defensor lee tu documento de atención denegada, identifica qué artículo de
la ley se violó, y redacta tu reclamo formal — en minutos.**

Un abogado-IA de bolsillo, en español, para pacientes que el sistema de salud
peruano dejó afuera. Construido sobre **Claude Opus 4.7** para el hackathon
*Built with Opus 4.7* de Anthropic (abril 2026).

> Defensor no reemplaza a un abogado. Esta es información legal, no asesoría
> legal.

---

## ¿Qué hace?

1. Lees. Defensor lee la foto con visión de alta resolución de Opus 4.7.
2. Cita. Identifica el artículo de la **Ley 29414** o la **Ley 26842** que se
   vulneró.
3. Redacta. Escribe un reclamo en registro formal peruano.
4. Escala. Elige el canal correcto: Libro de Reclamaciones → SUSALUD →
   Defensoría del Pueblo → amparo judicial.
5. Sigue. Con **Managed Agents**, tu caso se sigue solo durante 25 días.

## Países soportados

- Perú (primario) — Ley 29414, SUSALUD, EsSalud/MINSA/EPS.
- Colombia (día 3) — Tutela.
- México (día 3) — Queja ante IMSS.

## Alcance del Día 1 (23 abril 2026)

Hoy funciona únicamente el **Agente Visión**: subir foto → ver JSON
estructurado del documento. Los otros cinco agentes llegan en los días
siguientes. Ver `CLAUDE.md` para el plan día-por-día.

---

## Desarrollo local

### Requisitos

- Node.js 20+ y npm
- Python 3.11+
- Una clave `ANTHROPIC_API_KEY` con acceso a Opus 4.7

### Primera vez

```bash
# 1. Crear el venv una vez (vive un nivel arriba del repo, fuera de git)
cd ..
python -m venv defensor
cd v1

# 2. Activar el venv (cada nueva terminal)
source ../defensor/Scripts/activate     # Git Bash en Windows
..\defensor\Scripts\activate            # PowerShell
source ../defensor/bin/activate         # macOS / Linux

# 3. Instalar dependencias
pip install -r requirements.txt
npm install

# 4. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local y pegar tu ANTHROPIC_API_KEY
```

### Arrancar la app

Dos procesos en dos terminales (ambas con el venv activado):

```bash
# Terminal 1: servicio Python de agentes (puerto 8000)
npm run agents

# Terminal 2: frontend Next.js (puerto 3000)
npm run dev
```

Luego abrir http://localhost:3000 y subir una foto.

### Ejecutar tests

```bash
npm run test:agents
```

El test del Agente Visión usa un documento **sintético** (`SINTÉTICO / NO
REAL` visible al pie). Consume tokens reales de la API. Si `ANTHROPIC_API_KEY`
no está definido, el test se salta limpiamente.

---

## Estructura del repo

```
/app              Frontend Next.js 16 (App Router)
  /api/analyze    Ruta API que orquesta el upload hacia el servicio Python
  /result/[id]    Página de resultado por caso
/agents           Agentes Python (uno por carpeta)
  /vision         ✅ Día 1 — lector de documentos
  /violation      ⏳ Día 2 — identificador de violaciones legales
  /channel        ⏳ Día 2 — selector de canal de escalamiento
  /drafter        ⏳ Día 2 — redactor del reclamo formal
  /memory         ⏳ Día 3 — persistencia del caso en memoria-filesystem
  /follow_up      ⏳ Día 3 — Managed Agent de seguimiento 25 días
  /orchestrator   ⏳ Día 3 — orquestador principal
  server.py       Servidor FastAPI (puerto 8000)
/legal-corpus     PDFs + extractos markdown de leyes peruanas
/country-modules  Módulos por país: Perú, Colombia, México
/tests/fixtures   Casos de prueba gold-standard
/docs             ADRs y documentación
/demo             Storyboard y guion del demo de 3 minutos
```

---

## Créditos

Construido en solitario por **Abel Mancilla** (Lima, Perú).

*En memoria de todos los pacientes cuya cita llegó tarde.*

# Agente de Memoria — Defensor

Almacena y recupera el estado de cada caso de paciente en archivos JSON persistentes.
No realiza llamadas a la API. Opera sobre archivos en `tmp/cases/<uuid>.json`.

## Operaciones disponibles
- `load_case(case_id)` — carga el JSON del caso
- `save_case(case_id, data)` — guarda o actualiza el caso  
- `append_event(case_id, event)` — agrega un evento de seguimiento
- `list_cases()` — lista todos los IDs de casos activos

## Estructura de un caso almacenado
- `case_id`: UUID del caso
- `created_at`: timestamp ISO
- `vision`: salida del Agente Visión
- `analysis`: salida del pipeline completo (violation + channel + draft)
- `events`: lista de eventos de seguimiento (FollowUpEvent)
- `status`: pending | filed | following_up | resolved | closed

---
name: jktic-company
description: Conexión al ambiente Condor de JKTIC (credenciales, script de conexión) y relación de módulos nombre en español → nombre técnico leída del Condor de JKTIC. Úsala para cualquier consulta u operación en el Condor de JKTIC, o cuando el usuario mencione un módulo por su nombre en español. La documentación del API está en la skill condor-soap.
---

# Ambiente Condor de JKTIC

Documentación del API SOAP (operaciones, tipos, particularidades): skill **`condor-soap`**. Esta skill solo contiene lo propio del ambiente de JKTIC.

## Credenciales

- Archivo: `.claude/skills/jktic-company/.env` (plantilla: `.env.example`). Variables `CONDOR_SOAP_*`, descritas en `condor-soap`.
- Opcional: `CONDOR_MODULES_ARTICLE_ID` para leer la relación de módulos de otro artículo.
- Nunca escribir los valores en código, comandos ni documentación.

## Conexión (`scripts/connect.py`)

```bash
.venv/bin/python .claude/skills/jktic-company/scripts/connect.py            # Linux: prueba la conexión
.venv\Scripts\python.exe .claude\skills\jktic-company\scripts\connect.py    # Windows
```

Hace un `login`, cuenta los módulos y hace `logout`. Desde otros scripts de esta carpeta:

```python
from connect import jktic_session

with jktic_session() as condor:
    ...  # condor.service, condor.session_id, condor.get_entry(), condor.entry_to_dict()
```

## Relación de módulos (`scripts/fetch_modules.py`)

`fetch_modules.py` y `fetch_catalog.py` usan `scripts/article_sync.py` (actualizar artículo → `.md` local → cargar al contexto).

Fuente: artículo `jkk_articles` id `b5a6fee1-f170-afa7-c27b-6af0b48ffdb8` ("JKTIC-VEN - Relación de módulos Condor") en el Condor de JKTIC.

Cada llamada:
1. **Actualiza:** consulta el artículo y reescribe `scripts/modules_es.md`.
2. **Carga:** lee `scripts/modules_es.md` y lo imprime; esa salida queda en el contexto.

Si Condor no responde, la primera línea dice `no actualizado: <motivo>` y se carga la última versión guardada. Siempre termina con código 0.

- **Al iniciar cada sesión:** lo ejecuta el hook `SessionStart` (`.claude/settings.json`) mediante `.claude/hooks/run_python.sh`.
- **Al usar esta skill:** ejecutarlo primero y usar su salida, no una copia anterior del contexto.

```bash
.venv/bin/python .claude/skills/jktic-company/scripts/fetch_modules.py          # artículo por defecto
.venv/bin/python .claude/skills/jktic-company/scripts/fetch_modules.py <id>     # otro artículo
```

Cuando el usuario mencione un módulo en español, buscarlo en la tabla cargada y usar el nombre técnico como `module_name`.

Limitaciones conocidas del artículo:
- No cubre todos los módulos visibles por SOAP (lista técnica completa: `../condor-soap/modules.md`).
- Algunas celdas tienen dos nombres técnicos (`Teams / team`, `Reports / Reports_1`, `jkp_schedules / jkp_schedule`): confirmar con `get_available_modules` cuál existe.

## Índice de instrucciones (artículo "JKTIC COMPANY GESTOR CATALOGO INDEX")

- Artículo `jkk_articles` N° 373, id `db9d1f2b-0538-a162-c809-6af12d4b9cae` (`01 : JKTIC COMPANY GESTOR CATALOGO INDEX`), creado el 2026-11-08 (renombrado el mismo día).
- Contenido en Markdown: tabla con N°, nombre, descripción breve e id de cada instrucción (`jkrg_registers`) de la planilla "Instrucciones Agentes".
- Es el **catálogo** del gestor (ver `AGENTS.md`). `scripts/fetch_catalog.py` lo actualiza en `scripts/catalog_index.md` y lo carga; lo ejecuta el hook `SessionStart`. Opcional: `CONDOR_CATALOG_ARTICLE_ID` en el `.env` para usar otro artículo.
- Para consultar una instrucción: tomar su id del índice y leer `get_entry("jkrg_registers", "<id>")` y su `jkrg_fields` con identificador `contenido`.
- Creación y formato de artículos: ver `condor-soap` (sección *Artículos*).

## Particularidades del ambiente de JKTIC

- **Usuario SOAP:** autenticado con clave de aplicación `jkapp_…`; ve 245 módulos (consulta del 2026-11-08).
- **Interfaz web protegida con HTTP Basic** (`realm="System Access"`) delante del login de Condor: la clave `jkapp_…` no sirve para esa capa. Para automatizar con Playwright se necesitan credenciales de "System Access" (pendientes).
- **HTTP 500 en métodos SOAP sin parámetros:** observado el 2026-11-08; pendiente confirmar si JKTIC ya ejecutó el deploy con el commit `d6dad9351` (ver `condor-soap`).

## Recorrido previo (antes de crear o editar una instrucción)

Regla 10 de `AGENTS.md`.

1. Ejecutar en Chrome el proceso tal como lo describe el usuario, en una pestaña nueva y **solo con lecturas**: navegar, buscar, filtrar, abrir vistas. Si el proceso tiene pasos que escriben (guardar, enviar, cerrar, borrar), llegar hasta antes de ese botón y no pulsarlo.
2. Anotar en cada paso lo que hará más fácil la ejecución posterior:
   - **URL directa** de cada pantalla, incluidas las de búsquedas guardadas (`saved_search_select=<id>`, `orderBy`, `sortOrder`).
   - **Identificadores** de campos y botones (`id`, `name`, `data-input`, `aria-label` o el texto exacto), sobre todo cuando hay varios con el mismo texto (por ejemplo, varios "Limpiar").
   - **Comportamientos especiales:** botones que recargan la página, enlaces que abren otra pestaña, autocompletados.
   - **Formato de los datos:** cómo se ve un valor (`6498509` frente a `4,081,499`) o un nombre (`JKTIC - Extracto bancario | Banco | Número - Tipo | Desde | Hasta`), y un **ejemplo real** con su N° de registro.
   - **Datos equivalentes por SOAP** cuando existan (módulo, identificador del campo en `jkrg_fields`), como alternativa más rápida.
   - **Casos de parada:** campos vacíos, listados sin resultados, sesión cerrada.
3. Incluir esos datos en el `contenido` de la instrucción, en el paso donde se usan o en una sección `## Datos técnicos`. Mostrarlos al usuario en el plan.
4. Si el recorrido muestra algo distinto a lo que describió el usuario (un campo vacío, otro orden, otro número), informarlo en el plan antes de redactar.

## Crear una instrucción (planilla "Instrucciones Agentes")

Las instrucciones de agentes son registros (`jkrg_registers`) de la planilla `jkrg_templates` **01 : 1159 - Instrucciones Agentes** (id `94a5f4cf-7bcb-a726-4b98-6af0b16de716`; objetos `creador` [Texto] y `contenido` [Párrafo], ambos obligatorios). Se crean **desde el formulario web en Chrome** (skill `claude-in-chrome`), no por SOAP.

0. Hacer el **Recorrido previo** del proceso que describe la instrucción.
1. Definir con el usuario el **título** y el **contenido** de la instrucción y mostrarlos completos en el plan.
2. Abrir una **pestaña nueva** de Chrome en:
   `https://jklo.jktic.com/jktic/system/custom/jk/jkondor5/jkrg-templates/createrg?id=94a5f4cf-7bcb-a726-4b98-6af0b16de716`
3. Campo `#JkrgObjectsRegisterName`: trae `Instrucciones Agentes`; conservarlo y **agregar al final** ` | ` + título (queda `Instrucciones Agentes | <título>`).
4. Campo `[data-input=creador]`: el código de agente, variable `CONDOR_AGENT_CODE` del `.env` de esta skill (leerla del `.env`, no escribirla en otro lado).
5. Campo `[data-input=contenido]` (textarea simple, sin editor enriquecido): todas las instrucciones en Markdown, siguiendo el **Formato del campo `contenido`** (abajo).
6. **Guardar** haciendo clic en **Guardar y Visualizar** (no usar *Limpiar* ni *Cancelar*), sin pedir otra confirmación: la aprobación es la del plan (regla 6 de `AGENTS.md`), donde el usuario ya vio título y contenido.
7. **No tomar ni mostrar capturas.** Verificar el registro por SOAP (`jkrg_registers` y sus `jkrg_fields`) y que `assigned_user_id` sea el usuario del `.env` (corregir con `set_entry` si no; regla 9 de `AGENTS.md`); informar en texto título, número, id y estado.
8. Agregar la instrucción al artículo índice **JKTIC COMPANY GESTOR CATALOGO INDEX** (fila con N°, instrucción, descripción breve e id del registro) con `set_entry` (incluir `id` del artículo) y verificarlo.
   - El `contenido` del artículo es **un único bloque `<pre>…</pre>`**, y el `</pre>` puede venir pegado al final de la última fila (`… | </pre>`). Leer la versión vigente (`html.unescape`), **quitar el `</pre>`**, agregar la fila nueva al final de la tabla y **volver a cerrar con `</pre>` en su propia línea al final**. Nunca insertar después de la línea que contiene `</pre>`.
   - Verificar al releer: exactamente un `<pre>` (al inicio) y un `</pre>` (al final, sin texto después), la fila nueva **antes** del `</pre>` y las filas anteriores intactas. Luego ejecutar `fetch_catalog.py`.

### Formato del campo `contenido`

- Todo el Markdown va dentro de **un único bloque `<pre>…</pre>`**: `<pre>` al inicio y `</pre>` al final, cada uno en su propia línea, sin texto antes ni después. Así la vista de Condor respeta la sangría de los subpasos.
- Dentro del bloque no escribir `<` ni `>` sueltos (p. ej. `<id>`): el navegador los toma como etiquetas y los oculta. Usar llaves: `{id}`.
- Al leer el `contenido` de una instrucción, quitar `<pre>` y `</pre>` (igual que con los artículos).
- Al verificar después de guardar: exactamente un `<pre>` y un `</pre>`, y en la vista del registro la sangría visible y la etiqueta sin aparecer como texto.

No mostrar imágenes al usuario; las capturas solo se usan internamente si hacen falta para ubicar un elemento en la página.

Si Chrome no tiene sesión en Condor o pide el acceso HTTP Basic ("System Access"), pedir al usuario que inicie sesión; no intentar credenciales.

Verificado el 2026-11-08: el formulario carga con la sesión de Chrome del usuario y los tres selectores existen.

## Editar una instrucción existente

0. Hacer el **Recorrido previo** del proceso con los cambios que pide el usuario.
1. Tomar el id del registro desde el catálogo (**JKTIC COMPANY GESTOR CATALOGO INDEX**).
2. Buscar su campo: `get_entry_list("jkrg_fields", "jkrg_fields.jkrg_register_id = '<id>' AND jkrg_fields.identificador = 'contenido'")` (debe haber exactamente uno).
3. `condor.set_entry("jkrg_fields", {"id": <id del campo>, "contenido": <Markdown completo>})` y releerlo (`html.unescape`) para comparar. El contenido sigue el **Formato del campo `contenido`** (dentro de `<pre>…</pre>`).
4. Si cambia el propósito, actualizar la descripción de esa fila en el catálogo (`set_entry` en `jkk_articles` con su `id` y `contenido` en `<pre>…</pre>`) y verificarlo con las mismas reglas del paso 8 de *Crear una instrucción*: todo el contenido dentro de un único bloque `<pre>…</pre>`, con el `</pre>` solo al final.

Editar por SOAP no deja el registro de cambios que deja el formulario web.


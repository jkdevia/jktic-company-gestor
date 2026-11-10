# Gestor de JKTIC

Este proyecto lee un índice con el catálogo de instrucciones de Condor Suite y guía al usuario según lo que solicite. Este archivo es la fuente de verdad de las instrucciones para los agentes.

## Reglas obligatorias

1. **Siempre** que el usuario solicite algo, indicarle que está interactuando con el **gestor de JKTIC**.
2. **Lo primero** ante cualquier solicitud: consultar el artículo **JKTIC COMPANY GESTOR CATALOGO INDEX** (id `db9d1f2b-0538-a162-c809-6af12d4b9cae`) ejecutando `.claude/skills/jktic-company/scripts/fetch_catalog.py`, que lee la versión vigente en Condor (no la copia del inicio de sesión). Con esa información, identificar qué instrucciones sirven para saber cómo ejecutar la actividad.
3. Si aplica **una** instrucción: leer su registro completo (`jkrg_registers` con el id del índice y su `jkrg_fields` con identificador `contenido`) y seguirla.
4. Si aplican **varias**: listarlas al usuario (N°, nombre y descripción), pedirle que escoja cuál se usará y seguir solo la escogida.
5. Si **ninguna** aplica: informarlo al usuario antes de responder con otro criterio.
6. **Siempre** que el usuario pida algo, presentarle primero un **plan de trabajo** (pasos, archivos o sistemas afectados, riesgos) y **únicamente ejecutarlo cuando el usuario lo apruebe** de forma explícita.
   - Antes de la aprobación solo se permiten lecturas necesarias para armar el plan (consultar el catálogo, leer archivos, consultas SOAP de solo lectura). Nada que cree, modifique o borre archivos o datos, ni que llame operaciones de escritura en Condor.
   - Si durante la ejecución el plan debe cambiar, detenerse, presentar el ajuste y esperar una nueva aprobación.
   - La aprobación vale solo para el plan presentado; una nueva solicitud requiere un nuevo plan.
7. Siempre que el usuario pida crear una instrucción, o sea necesario crearla, hacerlo con el procedimiento **Crear una instrucción** de la skill `jktic-company` (formulario web de la planilla "Instrucciones Agentes" en Chrome), respetando la regla 6.
8. **No mostrar imágenes** (capturas de pantalla) al usuario. Informar los resultados en texto; las capturas solo se usan internamente si hacen falta para ubicar un elemento en la página.
9. **Todo lo que se cree en Condor** debe quedar asignado al usuario del `.env` del cliente (`CONDOR_SOAP_USER`). Por SOAP lo hace `CondorSession.set_entry` al crear; por formulario web, verificar `assigned_user_id` por SOAP después de guardar y corregirlo con `set_entry` si no coincide.
10. Al crear o editar una instrucción, **antes** de redactar el paso a paso, recorrer el proceso real en Condor (paso *Recorrido previo* de la skill `jktic-company`) y escribir en la instrucción los datos concretos que encuentres: URLs directas, búsquedas guardadas, identificadores de campos y botones, formato de los datos y casos que hacen detener el proceso. El objetivo es que, al ejecutarla después, no haya que buscar nada.

## Catálogo de instrucciones

- Fuente: artículo `jkk_articles` **JKTIC COMPANY GESTOR CATALOGO INDEX** (N° 373, id `db9d1f2b-0538-a162-c809-6af12d4b9cae`) en el Condor de JKTIC. Es una tabla en Markdown con N°, nombre, descripción e id de cada instrucción.
- Se consulta al inicio de cada solicitud (regla 2). Además, el hook `SessionStart` lo actualiza y carga al iniciar la sesión (`.claude/skills/jktic-company/scripts/fetch_catalog.py` → `catalog_index.md`). Si Condor no responde, se usa la última copia guardada.
- Para ver una instrucción completa, leer por SOAP el registro `jkrg_registers` con el id del catálogo y su `jkrg_fields` con identificador `contenido`.
- Al crear una instrucción, agregarla al catálogo (procedimiento *Crear una instrucción* de la skill `jktic-company`).

## Entorno técnico

- El proyecto corre en **Windows y Linux**. Todos los scripts se escriben en **Python 3.10+**, con rutas en `pathlib` y sin comandos propios de un solo sistema.
- Dependencias en `requirements.txt` (SOAP: `zeep`; configuración: `python-dotenv`). Automatización de navegador: `playwright` (Chromium, instalado por el setup). Prueba de humo: `scripts/browser_smoke_test.py`; capturas en `output/` (no se versiona).
- Instalación: `setup.sh` (Linux) o `setup.ps1` (Windows) crean el `.venv` en la raíz del proyecto.
- Ejecutar siempre con el Python del `.venv`. En hooks, usar `.claude/hooks/run_python.sh`.

## Recursos

- Skill `condor-soap` (`.claude/skills/condor-soap/`): documentación **genérica** del API SOAP de Condor, cliente Python `condor_soap.py` y lista técnica de módulos. No contiene credenciales de ningún cliente.
- Skill `jktic-company` (`.claude/skills/jktic-company/`): **ambiente de JKTIC**. Credenciales en su `.env` (plantilla `.env.example`), conexión con `scripts/connect.py` y relación de módulos nombre en español → técnico con `scripts/fetch_modules.py` (artículo `jkk_articles` `b5a6fee1-f170-afa7-c27b-6af0b48ffdb8`), que el hook `SessionStart` actualiza y carga en cada sesión.
- **Clientes:** cada cliente tiene su propia skill `<cliente>-company` con su `.env` (variables `CONDOR_SOAP_*`), su `connect.py` e instrucciones específicas. Las credenciales viven solo en la skill de su cliente; nunca en `condor-soap`, en código ni en documentación.

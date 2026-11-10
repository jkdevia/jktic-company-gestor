---
name: condor-soap
description: Documentación genérica del API SOAP de Condor Suite (SugarCRM, NuSOAP "sugarsoap") y cliente Python reutilizable. Úsala para saber qué operaciones, tipos y particularidades tiene el API al consultar o crear datos en el Condor de cualquier cliente; las credenciales y la conexión de cada cliente están en su propia skill (p. ej. jktic-company).
---

# API SOAP de Condor Suite

Esta skill es **genérica**: no contiene URL ni credenciales de ningún cliente. Cada cliente tiene su propia skill con su `.env`, su script de conexión y sus instrucciones específicas.

| Cliente | Skill |
|---|---|
| JKTIC | `jktic-company` |

## Clientes: estructura y cómo agregar uno nuevo

```
.claude/skills/<cliente>-company/
├── SKILL.md           particularidades del ambiente del cliente
├── .env               CONDOR_SOAP_* del cliente (no se versiona)
├── .env.example       plantilla sin valores
└── scripts/
    └── connect.py     conexión al ambiente del cliente (copiar de jktic-company y cambiar CLIENT)
```

Variables del `.env` de cada cliente (mismos nombres para todos):

| Variable | Uso |
|---|---|
| `CONDOR_SOAP_URL` | URL del endpoint SOAP (el WSDL se obtiene añadiendo `?wsdl`) |
| `CONDOR_SOAP_USER` | Nombre de usuario exacto de Condor (no el correo, salvo que el correo sea el user_name). Activo, no de portal ni de grupo |
| `CONDOR_SOAP_PASSWORD` | **Clave de aplicación `jkapp_…`** (recomendado), generada en Condor, módulo `jk_app_passwords`. Se envía tal cual. Alternativa: MD5 en minúsculas de la contraseña. Nunca texto plano |
| `CONDOR_SOAP_VERSION` | Versión para `user_auth` (por defecto `1.0`) |

**Nunca** escribir URL, usuario ni contraseña en código, comandos ni documentación. Si falta el `.env` o alguna variable, pedírselo al usuario; no inventar valores. No imprimir ni registrar credenciales.

## Características técnicas

- Plataforma: SugarCRM (API SOAP v1, NuSOAP), servicio `sugarsoap`.
- Estilo: **rpc/encoded**, binding `sugarsoapBinding`. Namespace: `http://www.sugarcrm.com/sugarcrm`. SoapAction: `<URL>/<operación>`.
- Lenguaje del proyecto: **Python 3.10+** con **`zeep`** (Windows y Linux). TLS siempre verificado.
- Entorno: `.venv` en la raíz del proyecto (`setup.sh` / `setup.ps1`). Ejecutar con `.venv/bin/python` (Linux) o `.venv\Scripts\python.exe` (Windows).

## Flujo de uso

1. `login(user_auth{user_name, password, version}, application_name)` → `id` = **session id**. Revisar `error.number` (`0` = OK).
2. Usar `session` en las demás operaciones.
3. `logout(session)` al terminar.

### Cliente genérico (`scripts/condor_soap.py`)

Todo script debe usar este cliente en lugar de repetir el login. `CondorSession(config)` hace `login` al entrar y `logout` al salir, y lanza `CondorError` con el mensaje del servicio si algo falla. La configuración la entrega el `connect.py` de cada cliente.

```python
# Dentro de la skill de un cliente (scripts/ de jktic-company):
from connect import jktic_session

with jktic_session() as condor:
    res = condor.service.get_entry_list(condor.session_id, "Accounts", "accounts.name LIKE 'A%'", "name", 0, [], 20, 0)
    for entry in res.entry_list or []:
        print(condor.entry_to_dict(entry).get("name"))
    registro = condor.entry_to_dict(condor.get_entry("jkk_articles", "<id>"))
```

Para escribir: `rid = condor.set_entry("<módulo>", {"campo": "valor", ...})` (sin `id` crea, con `id` actualiza; devuelve el id). Al crear, si no se pasa `assigned_user_id`, lo asigna al usuario de la sesión (`condor.user_id()`, el del `.env` del cliente). Otras funciones: `load_config(env_file)` y `load_client_config("<cliente>-company")`. Las listas de `zeep` (`entry_list`, `name_value_list`, `modules`) se recorren con `for` y admiten `len()`.

## Tipos comunes

- `name_value` = `{name, value}`; `name_value_list` = array de `name_value` (campos de un registro).
- `name_value_lists` = array de `name_value_list` (varios registros).
- `select_fields` = array de strings (campos o ids).
- `entry_value` = `{id, module_name, name_value_list}`.
- `error_value` = `{number, name, description}` (`number` `0` = sin error).
- `user_auth` = `{user_name, password(clave jkapp_… o md5), version}`.
- `note_attachment` = `{id, filename, file(base64)}`; `document_revision` = `{id, document_name, revision, filename, file(base64)}`.
- `set_relationship_value` = `{module1, module1_id, module2, module2_id}`.

## Operaciones con sesión (principales)

| Operación | Parámetros | Devuelve |
|---|---|---|
| `login` | user_auth, application_name | set_entry_result (id = sesión) |
| `logout` | session | error_value |
| `seamless_login` | session | int |
| `is_user_admin` | session | int |
| `get_user_id` / `get_user_team_id` | session | string |
| `get_available_modules` | session | module_list |
| `get_module_fields` | session, module_name | module_fields |
| `get_entry_list` | session, module_name, query (SQL WHERE), order_by, offset, select_fields, max_results, deleted | get_entry_list_result (result_count, next_offset, field_list, entry_list) |
| `get_entry` | session, module_name, id, select_fields | get_entry_result |
| `get_entries` | session, module_name, ids, select_fields | get_entry_result |
| `get_entries_count` | session, module_name, query, deleted | get_entries_count_result |
| `set_entry` | session, module_name, name_value_list | set_entry_result (id; sin `id` crea, con `id` actualiza) |
| `set_entries` | session, module_name, name_value_lists | set_entries_result |
| `set_entries_details` | session, module_name, name_value_lists, select_fields | set_entries_detail_result |
| `get_relationships` | session, module_name, module_id, related_module, related_module_query, deleted | get_relationships_result |
| `set_relationship` | session, set_relationship_value | error_value |
| `set_relationships` | session, set_relationship_list | set_relationship_list_result |
| `set_note_attachment` / `get_note_attachment` | session, note / session, id | set_entry_result / return_note_attachment |
| `relate_note_to_module` | session, note_id, module_name, module_id | error_value |
| `get_related_notes` | session, module_name, module_id, select_fields | get_entry_result |
| `set_document_revision` / `get_document_revision` | session, note / session, i | set_entry_result / return_document_revision |
| `update_portal_user` | session, portal_name, name_value_list | error_value |
| `get_modified_entries` | session, module_name, ids, select_fields | get_sync_result_encoded |
| `sync_get_modified_relationships` | session, module_name, related_module, from_date, to_date, offset, max_results, deleted, module_id, select_fields, ids, relationship_name, deletion_date, php_serialize | get_entry_list_result_encoded |
| `get_attendee_list` | session, module_name, id | get_sync_result_encoded |
| `get_mailmerge_document` / `get_mailmerge_document2` | session, file_name, fields | get_sync_result_encoded / get_mailmerge_document_result |
| `set_campaign_merge` | session, targets, campaign_id | error_value |

## Operaciones sin sesión (reciben usuario y contraseña en cada llamada)

Preferir el flujo con `login`; estas envían credenciales en cada petición.

`create_session(user_name, password)`, `end_session(user_name)`, `search_by_module(user_name, password, search_string, modules, offset, max_results)`, `contact_by_email(user_name, password, email_address)`, `get_contact_relationships(user_name, password, id)`, `user_list(user_name, password)`, `search(user_name, password, name)`, `track_email(user_name, password, parent_id, contact_ids, date_sent, email_subject, email_body)`, `create_contact(…, first_name, last_name, email_address)`, `create_lead(…, first_name, last_name, email_address)`, `create_account(…, name, phone, website)`, `create_opportunity(…, name, amount)`, `create_case(…, name)`.

## Operaciones públicas (sin autenticación)

`is_loopback()`, `get_server_time()`, `get_gmt_time()`, `get_sugar_flavor()`, `get_server_version()`.

## Particularidades del API (aplican a todos los clientes)

- **Login y bloqueo:** `login` NO acepta la contraseña en texto plano (`[10] Invalid Login`). Cada fallo cuenta para el bloqueo por intentos (`lockout_reached`): como máximo un intento por cada cambio de configuración; no reintentar en bucle.
- **`select_fields` en `get_entry`:** Condor devuelve `name_value_list` vacío si se pasa una lista de campos; usar `[]` (todos) y filtrar en el cliente. `CondorSession.get_entry` ya lo hace.
- **HTTP 500 en métodos sin parámetros** (`get_server_version`, `get_server_time`, `get_gmt_time`, `get_sugar_flavor`, `is_loopback`): bug corregido en el commit `d6dad9351`; cada ambiente lo tiene resuelto solo si actualizó y ejecutó el deploy (`jkondor_update.sh`). No es un problema de credenciales.
- **Filtro por equipos:** si el ambiente tiene activo `jk.soap_team_filter` (`config_local.php`), el usuario solo ve registros de sus equipos, del equipo "Todos" o asignados a él. Si una consulta vuelve vacía, asignar el equipo al usuario; no desactivar el filtro.
- `query` de `get_entry_list` es un fragmento SQL `WHERE` con prefijo de tabla (p. ej. `accounts.name LIKE 'A%'`); escapar los valores para evitar inyección.
- Paginar con `offset`/`next_offset`; `deleted=0` excluye borrados. Archivos (`file`) en base64.
- Las operaciones `set_*`, `create_*`, `track_email` y `set_campaign_merge` **modifican datos**: confirmar con el usuario antes de ejecutarlas.
- Respuestas con `error.number != 0` indican fallo; mostrar `error.description`.

## Escritura (`set_entry`) y formato `<item>` de NuSOAP

- El servidor (NuSOAP 0.7.2, `soap/SoapSugarUsers.php`) recorre `$name_value_list['item']`: cada par debe llegar como `<item><name>…</name><value>…</value></item>`.
- `zeep` genera `<name_value>` en su lugar: el servidor no recibe **ningún** campo, el bean se guarda vacío y el INSERT falla (p. ej. `Column 'articulo' cannot be null`). Los warnings están suprimidos en el servidor, así que no hay otro aviso.
- `CondorSession` registra el plugin `NuSoapArrays`, que renombra los elementos a `<item>` y agrega `SOAP-ENC:arrayType`/`xsi:type`. Usar siempre `condor.set_entry(...)` o `condor.service.*` de esa sesión; no armar `name_value_list` con diccionarios sueltos.
- `set_entries` tiene el mismo formato; si se usa, agregar su arreglo a `NuSoapArrays.ARRAYS` y probar.

## Artículos (`jkk_articles`)

- El título va en el campo **`articulo`**; **no enviar `name`**. Condor arma `name` como `<version> : <articulo>` (p. ej. `01 : JKTIC COMPANY GESTOR CATALOGO INDEX`).
- Campos al crear: `articulo`, `version` (`01`), `type` (`Controlado` / `No Controlado`), `status` (`En modificacion`, `En aprobacion`, `En revision`, `Publicado`, `Obsoleto`), `team_id`, `contenido`.
- `contenido`: Markdown dentro de `<pre>…</pre>` (Condor lo guarda escapado: `&lt;pre&gt;…`). Al leer: `html.unescape` y quitar las etiquetas `pre`.
- Verificar después de crear: releer con `get_entry` y comparar el contenido.

## Inventario de módulos

`modules.md` (esta carpeta) lista los nombres técnicos de los módulos (`module_name`), obtenidos con `get_available_modules` en el ambiente de JKTIC. Otros clientes pueden tener más o menos módulos según su versión y permisos: confirmar con `get_available_modules`. La relación nombre en español → nombre técnico se carga desde la skill `jktic-company`.

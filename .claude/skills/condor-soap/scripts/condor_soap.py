"""Cliente SOAP genérico para Condor Suite (SugarCRM, servicio "sugarsoap").

No contiene credenciales ni rutas de ningún cliente: cada cliente tiene su propia
skill (p. ej. .claude/skills/jktic-company/) con su .env y su script de conexión.
Funciona igual en Windows y Linux (rutas con pathlib).

Uso desde la skill de un cliente:
    from condor_soap import CondorSession, load_client_config

    with CondorSession(load_client_config("jktic-company")) as condor:
        modules = condor.service.get_available_modules(condor.session_id).modules
        fields = condor.entry_to_dict(condor.get_entry("Accounts", "<id>"))
"""
from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values
from zeep import Client, Plugin
from zeep.transports import Transport

SKILLS_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_NAME = "jktic-gestor"
REQUIRED_VARS = ("CONDOR_SOAP_URL", "CONDOR_SOAP_USER", "CONDOR_SOAP_PASSWORD")


SUGAR_NS = "http://www.sugarcrm.com/sugarcrm"
SOAP_ENC_NS = "http://schemas.xmlsoap.org/soap/encoding/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class NuSoapArrays(Plugin):
    """Ajusta los arreglos SOAP-ENC al formato que lee NuSOAP.

    El servidor recorre $name_value_list['item']: cada par debe llegar como
    <item>, no como <name_value> (lo que genera zeep). Sin esto, set_entry
    no recibe ningún campo.
    """

    ARRAYS = {"name_value_list": "name_value"}

    def egress(self, envelope, http_headers, operation, binding_options):
        for array_tag, item_type in self.ARRAYS.items():
            for el in envelope.iter(array_tag):
                for child in el:
                    child.tag = "item"
                el.set(f"{{{SOAP_ENC_NS}}}arrayType", "x")  # declara el namespace SOAP-ENC
                prefix = {v: k for k, v in el.nsmap.items()}
                el.set(f"{{{SOAP_ENC_NS}}}arrayType", f"{prefix[SUGAR_NS]}:{item_type}[{len(el)}]")
                el.set(f"{{{XSI_NS}}}type", f"{prefix[SUGAR_NS]}:{array_tag}")
        return envelope, http_headers


class CondorError(RuntimeError):
    """Error de configuración, conexión o respuesta del servicio Condor."""


def load_config(env_file: Path) -> dict[str, str]:
    """Carga y valida las variables CONDOR_SOAP_* de un archivo .env."""
    env_file = Path(env_file)
    if not env_file.is_file():
        raise CondorError(f"no existe {env_file}")
    config = {k: (v or "").strip() for k, v in dotenv_values(env_file).items()}
    missing = [k for k in REQUIRED_VARS if not config.get(k)]
    if missing:
        raise CondorError(f"faltan variables en {env_file.name}: {', '.join(missing)}")
    config.setdefault("CONDOR_SOAP_VERSION", "1.0")
    if not config["CONDOR_SOAP_VERSION"]:
        config["CONDOR_SOAP_VERSION"] = "1.0"
    return config


def load_client_config(client: str) -> dict[str, str]:
    """Carga el .env de la skill de un cliente (.claude/skills/<client>/.env)."""
    return load_config(SKILLS_ROOT / client / ".env")


def _check(error, action: str) -> None:
    """Lanza CondorError si un error_value del servicio indica fallo."""
    if error is not None and str(error.number) != "0":
        raise CondorError(f"{action}: [{error.number}] {error.name} - {error.description}")


class CondorSession:
    """Sesión SOAP: login al entrar, logout al salir (un solo login por uso)."""

    def __init__(self, config: dict[str, str], timeout: int = 20):
        self.config = config
        self.timeout = timeout
        self.client: Client | None = None
        self.session_id: str | None = None

    @property
    def service(self):
        if self.client is None:
            raise CondorError("la sesión no está abierta")
        return self.client.service

    def __enter__(self) -> "CondorSession":
        try:
            transport = Transport(timeout=self.timeout, operation_timeout=self.timeout)
            self.client = Client(self.config["CONDOR_SOAP_URL"] + "?wsdl", transport=transport,
                                 plugins=[NuSoapArrays()])
            result = self.client.service.login(
                {
                    "user_name": self.config["CONDOR_SOAP_USER"],
                    # Clave de aplicación jkapp_... tal cual (no texto plano).
                    "password": self.config["CONDOR_SOAP_PASSWORD"],
                    "version": self.config["CONDOR_SOAP_VERSION"],
                },
                APPLICATION_NAME,
            )
        except CondorError:
            raise
        except Exception as exc:  # conexión, WSDL, TLS...
            raise CondorError(f"conexión SOAP: {exc}") from exc
        _check(result.error, "login")
        self.session_id = result.id
        return self

    def __exit__(self, *exc_info) -> None:
        if self.client is not None and self.session_id:
            try:
                self.client.service.logout(self.session_id)
            except Exception:
                pass  # el logout fallido no debe ocultar el error original
        self.session_id = None

    def get_entry(self, module_name: str, record_id: str):
        """Lee un registro. Condor devuelve campos vacíos si se pasa
        select_fields, así que siempre se piden todos ([])."""
        result = self.service.get_entry(self.session_id, module_name, record_id, [])
        _check(result.error, f"get_entry {module_name}")
        if not result.entry_list:
            raise CondorError(f"{module_name} {record_id} no encontrado")
        return result.entry_list[0]

    def set_entry(self, module_name: str, fields: dict[str, str]) -> str:
        """Crea (sin "id") o actualiza (con "id") un registro. Devuelve el id.

        Al crear, si no se indica "assigned_user_id", el registro se asigna al
        usuario de la sesión (el del .env del cliente).
        Escribe datos en Condor: confirmar con el usuario antes de usarlo.
        """
        fields = dict(fields)
        if not fields.get("id") and not fields.get("assigned_user_id"):
            fields["assigned_user_id"] = self.user_id()
        nv = self.client.get_type(f"{{{SUGAR_NS}}}name_value")
        nvl = self.client.get_type(f"{{{SUGAR_NS}}}name_value_list")
        payload = nvl([nv(name=k, value=str(v)) for k, v in fields.items()])
        result = self.service.set_entry(self.session_id, module_name, payload)
        _check(result.error, f"set_entry {module_name}")
        return result.id

    def user_id(self) -> str:
        """Id del usuario autenticado en la sesión."""
        if not getattr(self, "_user_id", None):
            self._user_id = self.service.get_user_id(self.session_id)
        return self._user_id

    @staticmethod
    def entry_to_dict(entry) -> dict[str, str]:
        """Convierte el name_value_list de un registro en diccionario."""
        return {nv.name: nv.value or "" for nv in (entry.name_value_list or [])}

"""Propaga el paquete compartido dentro de cada microservicio (vendoring).

Uso (desde la raíz del repositorio de infraestructura):

    python shared/sync_vendored.py

La copia canónica es `shared/service_discovery/src/service_discovery`.
Cada servicio recibe el paquete bajo su capa de infraestructura con el
namespace que le corresponde. Los imports internos son relativos, así
que la copia no requiere reescrituras.
"""

import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = Path(__file__).resolve().parent / "service_discovery" / "src" / "service_discovery"

VENDORED_PATHS = {
    "orchestrator-svc": "pdf-extractext-orchestrator-svc/src/orchestrator/infrastructure/service_discovery",
    "validator-svc": "pdf-extractext-validator-svc/app/infrastructure/service_discovery",
    "extractor-svc": "pdf-extractext-extractor-svc/infrastructure/service_discovery",
    "persistence-svc": "pdf-extractext-persistence-svc/app/infrastructure/service_discovery",
}


def sync() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"No se encontró el paquete canónico: {SOURCE}")
    for service, relative in VENDORED_PATHS.items():
        target = WORKSPACE_ROOT / relative
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(SOURCE, target)
        print(f"sync {service}: {target}")


if __name__ == "__main__":
    sync()

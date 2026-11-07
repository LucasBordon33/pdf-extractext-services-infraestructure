# shared / service_discovery

Módulo compartido de **Service Discovery** (HashiCorp Consul) para los
microservicios `pdf-extractext`. Es código exclusivamente de
infraestructura: `domain` y `application` de cada servicio nunca lo
conocen.

## Contenido

| Módulo | Responsabilidad |
| --- | --- |
| `interfaces.py` | Contratos `IServiceRegistry` / `IServiceDiscovery` (Protocol). |
| `models.py` | `ServiceInstance` (instancia saludable). |
| `settings.py` | `ServiceDiscoverySettings` (pydantic-settings, env vars) + `load_settings`. |
| `logging.py` | Logging estructurado (`get_logger`, `JsonFormatter`). |
| `consul/client.py` | Cliente mínimo del Agent API de Consul (stdlib `urllib`). |
| `consul/registry.py` | `ConsulServiceRegistry`: registro/desregistro con health check. |
| `consul/discovery.py` | `ConsulServiceDiscovery`: resolución con caché TTL + round-robin. |
| `fastapi.py` | `add_health_route` + `attach_consul_lifespan` (SIGINT/SIGTERM safe). |

## Distribución (vendoring)

Cada repositorio de servicio construye su propia imagen Docker, por lo
que el paquete se **vende** dentro de cada servicio:

- `orchestrator-svc` -> `src/orchestrator/infrastructure/service_discovery/`
- `validator-svc` -> `app/infrastructure/service_discovery/`
- `extractor-svc` -> `infrastructure/service_discovery/`
- `persistence-svc` -> `app/infrastructure/service_discovery/`

La copia canónica es `src/service_discovery` (este directorio). Para
propagar cambios a los cuatro servicios:

```bash
python shared/sync_vendored.py
```

Los imports internos son relativos: la copia funciona bajo cualquier
namespace. Cuando el proyecto requiera versionado formal del paquete,
el mismo árbol se publica como dependencia git/PyPI sin cambios de
código (`pyproject.toml` ya está preparado).

## Variables de entorno

| Variable | Default | Descripción |
| --- | --- | --- |
| `SERVICE_DISCOVERY_ENABLED` | `true` | Interruptor general (permite correr sin Consul). |
| `CONSUL_HOST` | `consul` | Host del agente Consul. |
| `CONSUL_PORT` | `8500` | Puerto HTTP API del agente. |
| `CONSUL_TIMEOUT` | `2.0` | Timeout (s) de cada llamada HTTP a Consul. |
| `SERVICE_NAME` | — | Nombre lógico en Consul (requerido para registrar). |
| `SERVICE_ID` | `{name}-{hostname}` | ID de instancia (único por contenedor). |
| `SERVICE_HOST` | — | Si se define, fija la dirección registrada (modo dns). |
| `SERVICE_ADDRESS_MODE` | `ip` | `ip`: registra la IP del contenedor (check por instancia real, purga de muertas y round-robin real). `dns`: registra el alias del compose (comportamiento histórico). |
| `SERVICE_PORT` | `8000` | Puerto HTTP del servicio. |
| `SERVICE_HEALTH_PATH` | `/health` | Path del health check HTTP. |
| `HEALTH_CHECK_INTERVAL` | `10s` | Intervalo del check en Consul. |
| `HEALTH_CHECK_TIMEOUT` | `5s` | Timeout del check en Consul. |
| `DEREGISTER_CRITICAL_AFTER` | `60s` | Purga automática de instancias caídas. |
| `CONSUL_REGISTER_RETRIES` | `1` | Reintentos de registro al iniciar. |
| `CONSUL_REGISTER_BACKOFF` | `0.5` | Backoff (s) entre reintentos. |
| `DISCOVERY_CACHE_TTL` | `5.0` | TTL (s) de la caché de descubrimiento. |

## Semántica de fallos y recuperación

- **Instancia muerta (SIGKILL/OOM):** con modo `ip` el check falla contra
  la IP exacta → `critical` → Consul purga a los ~60s
  (`DeregisterCriticalServiceAfter`). Con modo `dns` y réplicas bajo un
  mismo alias, un contenedor muerto puede quedar `passing` para siempre
  (otra réplica responde el check): por eso `ip` es el default.
- **Dependencia caída > 60s:** si el health check del servicio depende de
  MongoDB/Redis y devuelve 503, Consul purga el registro. El sistema
  sigue funcionando: el orquestador degrada a sus URLs estáticas.
  El registro se restaura al reiniciar el servicio (o al recrear el
  contenedor); si se quiere re-registro automático sin reinicio, la
  evolución natural es un heartbeat de re-registro idempotente en
  `ConsulServiceRegistry` (no implementado: YAGNI).

# servicios / consul

HashiCorp Consul como mecanismo de **Service Discovery** para los
microservicios `pdf-extractext`.

- Agente único en modo servidor (`-server`, `bootstrap_expect = 1`).
- Sin Connect, sin sidecars, sin ACLs, sin multi-DC (KISS/YAGNI).
- Health checks HTTP contra `GET /health` de cada microservicio.
- La imagen es la oficial: `hashicorp/consul:1.21`.

## Levantar

```bash
# La red externa compartida (si aún no existe)
docker network create pdf-extractext-network

docker compose -f servicios/consul/docker-compose.yml up -d
```

El puerto HTTP API queda publicado **solo en loopback** del host
(`127.0.0.1:8500`) para inspección manual. Dentro de la red Docker los
microservicios lo alcanzan como `consul:8500`.

## Verificación con CLI (sin GUI)

```bash
# Miembros del clúster y salud del agente
docker compose -f servicios/consul/docker-compose.yml exec consul consul members

# Servicios registrados (catálogo)
curl http://127.0.0.1:8500/v1/catalog/services

# Instancias saludables de un servicio (lo que consume el discovery)
curl "http://127.0.0.1:8500/v1/health/service/validator?passing=true"

# Desregistrar manualmente una instancia huérfana
curl -X PUT http://127.0.0.1:8500/v1/agent/service/deregister/<service-id>
```

La UI web incluida en el binario queda activa (`-ui` via `ui_config`)
pero sin exponerla más allá de loopback; la administración esperada es
por CLI/API/logs.

## Integración con los microservicios

Cada microservicio se registra/desregistra solo mediante el paquete
compartido `shared/service_discovery` (vendido dentro de cada repo):

| Servicio | Nombre en Consul | Health check |
| --- | --- | --- |
| orchestrator | `orchestrator` | `GET /health` |
| validator | `validator` | `GET /health` |
| extractor | `extractor` | `GET /health` |
| persistence | `store` | `GET /api/v1/health` |

- Registro al iniciar (lifespan de FastAPI), desregistro al apagar
  (SIGINT/SIGTERM). Ante SIGKILL/OOM, Consul purga la instancia tras
  `DeregisterCriticalServiceAfter` (60s).
- El orquestador resuelve `validator`/`extractor`/`store` dinámicamente
  (caché TTL 5s + round-robin) y degrada a las URLs estáticas de su
  config si Consul no responde.

Para propagar cambios del paquete compartido a los cuatro servicios:

```bash
python shared/sync_vendored.py
```

## Variables relevantes (por servicio)

`SERVICE_DISCOVERY_ENABLED`, `CONSUL_HOST`, `CONSUL_PORT`, `SERVICE_NAME`,
`SERVICE_ID`, `SERVICE_HOST`, `SERVICE_PORT`, `SERVICE_HEALTH_PATH`,
`HEALTH_CHECK_INTERVAL`, `HEALTH_CHECK_TIMEOUT`,
`DEREGISTER_CRITICAL_AFTER`, `CONSUL_REGISTER_RETRIES`,
`CONSUL_REGISTER_BACKOFF`, `DISCOVERY_CACHE_TTL`, `CONSUL_TIMEOUT`.
Ver `.env.example` de cada repositorio.

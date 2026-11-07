# servicios / mongodb

MongoDB como base de datos documental para los microservicios
`pdf-extractext` (backing store del servicio `store` / persistence).

- Imagen oficial: `mongo:7-jammy`.
- **0% exposición al host**: sin bloque `ports`. Dentro de la red Docker
  los microservicios lo alcanzan como `mongodb:27017`.
- Autenticación obligatoria: usuario root inyectado desde `.env`
  (`MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD`).
- Persistencia en volumen nombrado `mongo-data` (`/data/db`).
- Healthcheck con `mongosh` ping autenticado.

## Levantar

```bash
# La red externa compartida (si aún no existe)
docker network create pdf-extractext-network

# Credenciales (no commitear el .env real)
cp servicios/mongodb/.env.example servicios/mongodb/.env
# editar servicios/mongodb/.env

docker compose -f servicios/mongodb/docker-compose.yml up -d
```

Las credenciales root solo se aplican en el **primer arranque** (volumen
vacío, initdb). Para cambiarlas luego hay que eliminar el volumen
(`docker compose -f servicios/mongodb/docker-compose.yml down -v`) o
administrar usuarios vía mongosh.

## Verificación con CLI (sin exponer puertos)

```bash
# Estado del healthcheck
docker compose -f servicios/mongodb/docker-compose.yml ps

# Ping autenticado (reutiliza las credenciales del .env)
set -a; source servicios/mongodb/.env; set +a
docker compose -f servicios/mongodb/docker-compose.yml exec mongodb \
  mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" \
  --eval 'db.adminCommand("ping")'
```

## Integración con los microservicios

Cadena de conexión desde cualquier servicio de la red compartida
(`authSource=admin` porque el usuario vive en la base `admin`):

```
mongodb://<usuario>:<password>@mongodb:27017/?authSource=admin
```

| Microservicio | Uso |
| --- | --- |
| persistence (`store`) | Cliente primario de MongoDB para persistir documentos. |

- El hostname `mongodb` solo resuelve dentro de `pdf-extractext-network`;
  Traefik no publica nada de este servicio (no hay routers ni `ports`).
- `restart: unless-stopped` y `no-new-privileges` alineados con el resto
  de la infraestructura (Traefik/Consul).

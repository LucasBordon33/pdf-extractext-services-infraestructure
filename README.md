# pdf-extractext-services-infraestructure
Servicios de infraestructura para aplicacion microservicios pdf-extractext con configuración de cada servicio

| Directorio | Componente | Rol |
| --- | --- | --- |
| `servicios/traefik` | Traefik v3 | Reverse proxy / ingress (north-south). Provider Docker. |
| `servicios/consul` | HashiCorp Consul | Service discovery interno (east-west): registro, health checks y resolución dinámica. |
| `servicios/mongodb` | MongoDB 7 | Base de datos documental (backing store del servicio `store`). Sin exposición al host, red interna + auth root. |
| `shared/service_discovery` | Paquete Python compartido | Cliente/registro/discovery vendido dentro de cada microservicio. |


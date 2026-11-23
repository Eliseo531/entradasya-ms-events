# Microservicio ms-events (Catálogo de Eventos, Sectores y Reserva Atómica)

Microservicio de gestión de cartelera de eventos, definición de aforos por sectores y control estricto de concurrencia para **EntradasYa**.

* **Servicio:** `ms-events`
* **Tecnología:** Python 3.11+ + FastAPI + SQLAlchemy 2.0 (Async) + Pydantic v2
* **Puerto:** `8002`
* **Base de datos:** `events_db` (PostgreSQL 16)
* **Autenticación:** JWT simétrico HS256 local y cabecera `X-Internal-Token`

---

## 1. Características Principales

1. **Catálogo Público de Eventos:** Búsqueda en texto completo (título, descripción, lugar), paginación y filtro automático de eventos en estado `PUBLISHED` con fechas futuras.
2. **Gestión de Organizador:** Creación de eventos con sectores, aforos y precios en estado `DRAFT`, edición y transición de estados (`PUBLISHED`, `CANCELLED`).
3. **Reserva Atómica y Antilibre/Sobreveta:** Bloqueo a nivel de fila (`SELECT ... FOR UPDATE`) sobre la tabla `sectors` para evitar el *overselling* ante solicitudes concurrentes de `ms-orders`.
4. **Transacción Compensatoria (`/release`):** Reposición automática de cupos cuando una orden falla o es rechazada por la pasarela de pagos.
5. **Observabilidad Estándar:** Probes de salud `/health/live` y `/health/ready` (validación de conexión a PostgreSQL con `SELECT 1`).

---

## 2. Requisitos Previos

* Python >= 3.11
* PostgreSQL 16+ (base de datos `events_db` en puerto 5432)

---

## 3. Instalación y Ejecución Local

```bash
# Crear y activar entorno virtual
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar el servidor uvicorn en puerto 8002
python main.py
```

---

## 4. Endpoints Principales

### Públicos
* `GET /api/v1/events` - Cartelera pública con paginación (`?search=rock&page=1&limit=10`)
* `GET /api/v1/events/{id}` - Detalle completo de evento con sectores, aforo y cupos disponibles

### Organizador (Requiere `Authorization: Bearer <JWT_ORGANIZADOR>`)
* `GET /api/v1/organizer/events` - Lista eventos creados por el organizador autenticado
* `POST /api/v1/events` - Crear evento y sectores en estado `DRAFT`
* `PUT /api/v1/events/{id}` - Modificar evento del organizador
* `PATCH /api/v1/events/{id}/status` - Cambiar estado a `PUBLISHED` o `CANCELLED`

### Inter-Servicio (Invocados por `ms-orders`, requiere JWT o `X-Internal-Token`)
* `POST /api/v1/events/{id}/reserve` - Reserva atómica de cupos (responde 200 con importes o 409 `EVENTS_OUT_OF_STOCK`)
* `POST /api/v1/events/{id}/release` - Liberación compensatoria de cupos
* `POST /api/v1/events/{id}/confirm-reservation` - Confirmación tras pago exitoso

### Diagnóstico
* `GET /health/live` - Liveness probe (200 UP)
* `GET /health/ready` - Readiness probe (200 UP con `SELECT 1` o 503 DOWN)

---

## 5. Pruebas Automatizadas

```bash
pytest -v
```

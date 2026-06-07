# Gym Detection

Sistema de reconocimiento facial para gimnasios. Permite identificar miembros y validar el estado de su membresía en tiempo real.

> **Etapa actual: 1 — Auth & base ✅.** Auth con JWT, modelos `User`/`Gym`/`GymUser` con RBAC por gym, endpoint público de onboarding (`POST /gyms/public/onboarding`) para que un usuario nuevo registre su gym como OWNER.

---

## Stack

**Backend**
- Python 3.12 · FastAPI · SQLAlchemy 2 async · Alembic
- PostgreSQL 16 con **pgvector** para embeddings faciales
- InsightFace (`buffalo_l`, ArcFace) sobre onnxruntime — CPU
- JWT (python-jose) · Argon2 (passlib)

**Frontend**
- Next.js 15 (App Router) · React 19 · TypeScript estricto
- TailwindCSS 3.4 · shadcn/ui · lucide-react

**Infra**
- Docker Compose (postgres + backend + frontend)
- Sin Redis / Celery / S3 en MVP (decisión justificada en el plan)

---

## Prerrequisitos

- Docker >= 24
- Docker Compose v2
- (Opcional) `uv` para correr el backend fuera de Docker

---

## Levantar localmente

```bash
# 1) Clonar y entrar
cd gym-detection

# 2) Crear el .env del backend copiando el ejemplo
cp backend/.env.example backend/.env
# ⚠️ Cambiar JWT_SECRET por algo aleatorio largo en cualquier ambiente serio

# 3) Levantar todo
docker compose up --build
```

Servicios:
- Frontend: <http://localhost:3000>
- Backend: <http://localhost:8000>
- API Docs (Swagger): <http://localhost:8000/docs>
- Healthcheck: <http://localhost:8000/health>
- Postgres: `localhost:5433` (user/pass `gym`/`gym`) — mapeo a 5433 para no chocar con un postgres local

> **Nota:** la primera vez que se levante el backend, InsightFace descargará los modelos (~300MB) en su primera invocación. Esto se hace en el directorio `/home/appuser/.insightface` que está montado como volumen.

### Comandos útiles

```bash
# Ver logs de un servicio
docker compose logs -f backend

# Entrar al backend
docker compose exec backend bash

# Crear una migración nueva (Etapa 1+)
docker compose exec backend alembic revision --autogenerate -m "descripcion"

# Correr migraciones
docker compose exec backend alembic upgrade head

# Correr tests (corre setup de DB de tests automáticamente)
make test

# Bajar todo y limpiar volúmenes
docker compose down -v
```

---

## Estructura del proyecto

```
gym-detection/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app
│   │   ├── core/                  # config, db, security, exceptions
│   │   ├── models/                # SQLAlchemy (centralizado)
│   │   ├── modules/               # auth, gyms, members, memberships, face, access_logs
│   │   ├── api/                   # routers v1
│   │   └── seed.py                # seed inicial (Etapa 1)
│   ├── alembic/                   # migraciones
│   ├── tests/
│   ├── pyproject.toml             # uv
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                       # App Router
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/                       # api-client, utils
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Roadmap de etapas

- [x] **Etapa 0**: Setup base (estructura, docker, configs)
- [x] **Etapa 1**: Auth & base — modelos User/Gym/GymUser, login JWT, RBAC por gym, onboarding público
- [x] **Etapa 2**: ~~Members + Memberships CRUD + consentimiento biométrico~~ (saltada: overengineering)
- [ ] **Etapa 3**: Motor facial (InsightFace engine, carga en lifespan)
- [ ] **Etapa 4**: Enrolamiento facial (`POST /face/enroll`)
- [ ] **Etapa 5**: Verificación facial (`POST /access/verify-face`)
- [ ] **Etapa 6**: Frontend base (login, dashboard, ABM miembros)
- [ ] **Etapa 7**: Frontend webcam (enrolamiento + control de acceso)
- [ ] **Etapa 8**: Docker final + docs + colección de requests

### Mejoras futuras (post-MVP)

- Liveness / anti-spoofing
- Re-enrolamiento periódico
- Audit logs detallados + exportación de datos del miembro
- Rate limiting
- Logging estructurado + métricas (Prometheus)
- Cifrado app-side de embeddings con KMS
- Índice HNSW cuando un gym supere ~2k miembros
- App mobile / integración con molinetes
- Pagos online y notificaciones

---

## Decisiones arquitectónicas (resumen)

| Tema | Decisión | Por qué |
|------|----------|---------|
| Motor facial | InsightFace `buffalo_l` (CPU) | SOTA accuracy, ONNX runtime, integr. detección+embedding |
| Vector store | pgvector | Una sola DB, filtro multi-tenant en SQL, escala a HNSW |
| Multi-tenant | Shared DB + `gym_id` denormalizado | Simple para MVP, suficiente aislamiento |
| Imágenes | NO se guardan frames de verificación | Minimización de datos biométricos |
| Consentimiento | `biometric_consent_at` bloqueante | Requisito legal y técnico |
| Auth | JWT stateless (sin Redis) | Suficiente para MVP |
| Tasks async | Sin Celery/Redis | La verificación es real-time, no batch |

Detalle completo en los mensajes de planificación previos.

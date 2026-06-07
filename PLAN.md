# Plan del proyecto — Gym Detection

Documento de tracking interno. Refleja el plan original acordado y el estado de cada etapa.

## Decisiones arquitectónicas lockeadas

| Tema | Decisión | Por qué |
|------|----------|---------|
| Motor facial | InsightFace `buffalo_l` (CPU) | SOTA accuracy, ONNX runtime, pipeline detección+embedding |
| Vector store | pgvector | Una sola DB, filtro multi-tenant en SQL, escala a HNSW |
| Multi-tenant | Shared DB + `gym_id` denormalizado | Simple para MVP, suficiente aislamiento |
| Imágenes de verificación | NO se guardan | Minimización de datos biométricos |
| Consentimiento | `biometric_consent_at` bloqueante en enrolamiento | Requisito legal y técnico |
| Auth | JWT stateless (sin Redis) | Suficiente para MVP |
| Tareas async | Sin Celery/Redis en MVP | La verificación es real-time |
| Backend | Python 3.12 + FastAPI async + SQLAlchemy 2 async + Alembic | Stack moderno, async nativo |
| Frontend | Next.js 15 App Router + TS + Tailwind + shadcn | Estandar de la industria |
| Deps Python | `uv` | Rápido, lock determinista |
| Idiomas | UI y mensajes user-facing en español, código en inglés | |
| GPU | CPU para MVP (RDNA2 + ROCm no es estable) | Documentado como TODO experimental |
| Bootstrap | `python -m app.seed` | Script idempotente |

---

## Stack final

**Backend**
- Python 3.12 · FastAPI · SQLAlchemy 2 async · asyncpg · Alembic
- PostgreSQL 16 + pgvector (embeddings 512-d)
- InsightFace `buffalo_l` + onnxruntime (CPU)
- JWT (python-jose) · Argon2 (passlib) · structlog

**Frontend**
- Next.js 15 (App Router) · React 19 · TypeScript estricto
- TailwindCSS 3.4 · shadcn/ui · lucide-react

**Infra**
- Docker Compose: postgres+pgvector, backend, frontend
- Makefile para tareas comunes

---

## Etapas de implementación

### ~~Etapa 0 — Setup base~~ ✅
- ~~Estructura de carpetas backend/frontend~~
- ~~Docker Compose (postgres+pgvector, backend, frontend)~~
- ~~pyproject.toml con uv y dependencias core~~
- ~~Configuración: pydantic-settings, env vars, JWT, thresholds~~
- ~~Frontend base: Next.js + Tailwind + shadcn config~~
- ~~API client esqueleto y utils~~
- ~~Alembic init con env.py async~~
- ~~Makefile con 24 targets~~
- ~~README con guía para levantar localmente~~
- ~~Smoke tests: backend arranca, /health, frontend renderiza, postgres+pgvector OK, alembic conecta~~

### ~~Etapa 1 — Auth & base~~ ✅
- ~~Modelos: `User`, `Gym`, `GymUser`~~
- ~~Enum `GymUserRole` (client < manager < owner) con jerarquía~~
- ~~Migración inicial (autogenerada, con `CREATE EXTENSION vector` y `DO $$` para idempotencia del enum)~~
- ~~`core/security.py`: argon2 hashing + JWT con python-jose~~
- ~~`core/dependencies.py`: `get_current_user`, `require_superadmin`, `GymRoleChecker` (class-based dependency)~~
- ~~`modules/auth/`: `POST /auth/login`, `GET /auth/me`~~
- ~~`modules/gyms/`: `GET/POST/PATCH /gyms` con RBAC por gym, `POST /gyms/public/onboarding` (público: registra user+owner+gym en una transacción)~~
- ~~`modules/users/`: `POST /gyms/{gym_id}/users` (owner/manager crea user con rol CLIENT o MANAGER, atado al gym)~~
- ~~`modules/admin/`: `POST /admin/users` (solo superadmin, flags especiales is_superadmin/is_active)~~
- ~~`api/v1.py`: agrega routers bajo `/api/v1`~~
- ~~`seed.py` funcional: crea superadmin + gym demo + owner link (idempotente)~~
- ~~Tests: conftest con test DB dedicada (`gym_test`), fixtures (users, gym, tokens, manager), tests para auth + gyms + users + admin~~

### ~~Etapa 2 — Members + Memberships~~ ❌ (saltada: overengineering)
- ~~Modelos: `Member`, `Membership` con enums `MemberStatus` y `MembershipStatus`~~
- ~~Campo `biometric_consent_at` en Member (bloqueante para enrolar)~~
- ~~Tabla `members` con `UNIQUE(gym_id, document)`~~
- ~~Tabla `memberships` con FK a members~~
- ~~Cálculo de membresía vigente (start_date/end_date + status)~~
- ~~Endpoints CRUD para members y memberships~~
- ~~Tests~~

> **Razón del skip:** `User` + `GymUser(rol=CLIENT)` ya modelan "esta persona es miembro de este gym". Crear tablas separadas para `Member` y `Membership` duplicaba el modelo y agregaba un `biometric_consent_at` redundante. Los embeddings faciales y access logs se atan a `user_id` directamente. El consentimiento biométrico (cuando llegue el momento) vive en `GymUser`.

### Etapa 3 — Motor facial
- `app/modules/face/engine.py`: wrapper de InsightFace
- Carga del modelo en `lifespan` de FastAPI (en startup)
- Configuración desde env (modelo, provider, det_size, thresholds)
- Tests unitarios del engine con imágenes fixture

### Etapa 4 — Enrolamiento facial
- `POST /api/v1/gyms/{gym_id}/members/{member_id}/face/enroll` (multipart)
- Validaciones: exactamente 1 rostro, det_score mínimo, tamaño mínimo
- Anti-duplicado: buscar similitud >= 0.60 contra otros miembros del gym
- Tabla `face_embeddings` con columna `vector(512)` (pgvector) y `gym_id` denormalizado
- `GET/DELETE /face` y `DELETE /face/{id}`
- Audit log de enrolamientos
- Tests

### Etapa 5 — Verificación facial
- `POST /api/v1/gyms/{gym_id}/access/verify-face` (multipart)
- Query pgvector: top-1 por cosine distance filtrado por `gym_id`
- Thresholds: >=0.55 match, 0.40-0.55 low_confidence, <0.40 unknown
- Validación de membresía vigente
- Tabla `access_logs` con member_id (nullable) y resultado
- Respuesta con el formato exacto pedido (matched/confidence/member/membership/access)
- Tests

### Etapa 6 — Frontend base
- Setup login con shadcn `Form`, `Input`, `Button`
- Protected layout con `getMe()` al cargar
- Dashboard con métricas (total miembros, membresías activas/vencidas, accesos del día)
- ABM miembros (lista, crear, editar, ver)
- ABM membresías
- TanStack Query para fetching

### Etapa 7 — Frontend webcam
- Hook `useWebcam` con `getUserMedia`
- Pantalla de enrolamiento: cámara + captura + preview + resultado
- Pantalla de control de acceso (modo recepción): cámara + verificar + resultado grande
  - ✅ Acceso permitido · ❌ Acceso denegado · ⚠️ Rostro no reconocido
  - Mostrar nombre, documento, estado membresía, fecha vencimiento, confianza
- Manejo claro de errores y permisos de cámara

### Etapa 8 — Docker + docs
- Dockerfile optimizado para producción (multi-stage sin dev deps)
- `docker-compose.prod.yml` con build args de producción
- README final con guía de producción
- Colección de requests (`.http` o `requests.http`) para todos los endpoints
- Healthcheck en frontend contra backend

---

## Mejoras futuras (post-MVP)

- 🔴 **Crítico:** Liveness / anti-spoofing (detectar fotos impresas, videos)
- Re-enrolamiento periódico (los rostros cambian con el tiempo)
- Audit logs detallados + exportación de datos del miembro (GDPR-style)
- Rate limiting por IP y por user (slowapi o middleware custom)
- Logging estructurado en archivos + rotación
- Métricas Prometheus + dashboard Grafana
- Cifrado app-side de embeddings con KMS
- Índice HNSW cuando un gym supere ~2k miembros
- App mobile / integración con molinetes
- Pagos online y notificaciones (email/push)
- Multi-cámara y tracking de personas
- Reconocimiento en tiempo real continuo (streaming)
- Sistema de backups cifrados

---

## Riesgos identificados

- 🟡 **Riesgo de baja calidad de embeddings** con mala iluminación → mitigado con validación de `det_score` y `face_size` en enrolamiento
- 🟡 **Spoofing con foto impresa** → TODO crítico para v1, no resuelto en MVP
- 🟡 **Performance de pgvector con muchos miembros** → empezar sin índice, agregar HNSW cuando se vea degradación
- 🟡 **Falsos positivos en verificación** → threshold conservador (0.55), `low_confidence` para zona gris
- 🟡 **Privacidad biométrica** → embeddings son vectores opacos, no reversibles a foto, pero técnicamente sensibles

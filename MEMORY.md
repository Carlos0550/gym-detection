# MEMORY — Aprendizajes del proyecto gym-detection

Lecciones duras (las que costaron timeouts, rebuilds y tests rotos). Guardadas para no repetirlas en futuros proyectos.

---

## Reglas de oro (las que rompen cosas si no las seguís)

### 1. `.dockerignore` SIEMPRE, desde el día 1
Un `.venv/` local con symlinks a `~/.local/share/uv/python/...` en el host se copia a la imagen con `COPY . .` y rompe TODO el venv dentro del contenedor. Síntoma: `exec /app/.venv/bin/uvicorn: no such file or directory`, el `pyvenv.cfg` apunta a `/home/<user>/.local/share/uv/python/...`, `python` symlink roto.

**Fix:** `backend/.dockerignore` con `.venv/`, `__pycache__/`, `.env`, `.env.*`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `*.egg-info/`, `dist/`, `build/`, `.insightface/`. Confirmar que ignora bien con `docker run --rm <img> ls /app/`.

### 2. NO usar `uv venv` en Dockerfiles
`uv venv` cachea el interpreter en `~/.local/share/uv/python/...` y crea symlinks absolutos. En el container build esto queda apuntando al host. El container runtime no puede resolverlo.

**Fix:** usar `python -m venv /app/.venv` (stdlib, sin sorpresas) o `uv venv --python=/usr/local/bin/python` + `UV_PYTHON_PREFERENCE=only-system` (pero el primero es más simple y siempre funciona).

### 3. Alembic env.py SIEMPRE lee el env var
`alembic/env.py` hace `config.set_main_option("sqlalchemy.url", settings.database_url)` y OVERRIDEA cualquier `cfg.set_main_option(...)` que hayas hecho programáticamente. Si querés apuntar Alembic a otra DB, seteá `os.environ["DATABASE_URL"]` ANTES de cualquier import. El `setup_test_db.py` debe hacer esto en la línea 1.

### 4. pytest-asyncio 1.0+ requiere matching loop scopes
`pytest-asyncio>=0.24` (1.0+) tiene cambios breaking. El default de `loop_scope` es `function` para tests y `None` para fixtures. Engine session-scoped + tests function-scoped = "Future attached to a different loop".

**Fix universal** en `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

Y marcar cada fixture session-scoped con `loop_scope="session"` explícito.

### 5. DB de tests SIEMPRE separada de la de dev
El backend en runtime tiene connection pool con conexiones que pueden quedar `idle in transaction` con locks. Esas conexiones bloquean `TRUNCATE` en tablas referenciadas por FK. Resultado: tests cuelgan indefinidamente y se acumulan hasta 20+ queries esperando lock.

**Fix:** DB dedicada (`gym_test`), recreada por `setup_test_db.py`. Configurar con pool chico (o deshabilitar pool con `NullPool` en tests para evitar conexiones zombie).

### 6. `os.environ.setdefault` no funciona si docker-compose ya inyecta la var
`os.environ.setdefault("DATABASE_URL", "gym_test")` en conftest es NO-OP si `docker-compose.yml` ya tiene `environment: DATABASE_URL=...`. Usar asignación directa `os.environ["DATABASE_URL"] = "gym_test"`.

### 7. pydantic-settings + list[str] env vars requiere NoDecode
Pydantic-settings intenta parsear el env var como JSON por default. `CORS_ORIGINS="http://a,http://b"` rompe. Solución:

```python
from typing import Annotated
from pydantic_settings import BaseSettings, NoDecode

class Settings(BaseSettings):
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v
```

---

## Patrones confirmados para este usuario

### Stack lockeado
- **Backend:** Python 3.12 · FastAPI async · SQLAlchemy 2 async · asyncpg · Alembic · pydantic-settings v2 · structlog · uv (no Poetry, no pip)
- **DB:** PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16`)
- **Auth:** JWT con python-jose · Argon2 con passlib · Multi-tenant con `gym_id` denormalizado
- **Motor facial:** InsightFace `buffalo_l` + onnxruntime (CPU por ahora)
- **Frontend:** Next.js 15 App Router · React 19 · TypeScript estricto · Tailwind 3.4 · shadcn/ui · lucide-react
- **Tests:** pytest + pytest-asyncio (session loop scope) + httpx AsyncClient + DB de tests separada

### Preferencias de código
- UI y mensajes user-facing en **español** · código/variables en inglés
- Sin overengineering: solución más simple que funcione
- Migrations idempotentes: `CREATE EXTENSION IF NOT EXISTS`, `DO $$ ... EXCEPTION ... $$` para enums
- `uv pip install --group dev -e .` para que pytest/ruff estén en el container dev
- `pool_pre_ping=True` en el engine (recomendado por el usuario para conexiones que se pueden caer)

### Preferencias operativas
- Postgresql del container expuesto en `localhost:5433` (no 5432, ya hay un postgres local)
- `make help` autogenerado de comments `##` en targets
- `PLAN.md` en la raíz con tareas tachadas cuando se completan
- Tests con conftest + fixtures descriptivos (superadmin_user, owner_user, gym, etc.)
- Setup script separado (`setup_test_db.py`) + `make test` que lo encadena

### GPU: tiene RX 6650 XT / 6700S / 6800S (RDNA2)
ROCm oficial no soporta RDNA2 consumer. NO habilitar ROCm/onnxruntime-gpu por ahora. CPU es la opción correcta. Marcar como TODO experimental.

---

## Gotchas específicos de SQLAlchemy 2 async

### Idempotencia de CREATE TYPE en Postgres
`op.create_table(... sa.Enum('A','B', name='my_enum') ...)` falla con `DuplicateObjectError` si se corre dos veces (downgrade + upgrade). Solución:

```python
op.execute("""
DO $$ BEGIN
    CREATE TYPE my_enum AS ENUM ('A', 'B');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$
""")

# Luego en la tabla:
sa.Column('role', postgresql.ENUM('A', 'B', name='my_enum', create_type=False), nullable=False)
```

Y en `downgrade()` agregar `op.execute("DROP TYPE IF EXISTS my_enum")` explícito (PG no dropea enums al dropear la tabla).

### Password hash con Argon2
passlib + argon2 funciona bien. NO usar bcrypt (límite de 72 bytes, problemas con passwords largos).

### JWT con python-jose
`jose.jwt.decode()` con `algorithms=[settings.jwt_algorithm]` estricto (no dejar que decodee cualquier algoritmo).

---

## Patrones de tests que funcionan

### Conftest para FastAPI async con DB de tests
```python
# 1. Setear env var ANTES de cualquier import
os.environ["DATABASE_URL"] = "...test_db..."

# 2. Engine session-scoped + loop_scope explícito
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    e = create_async_engine(TEST_DB_URL)
    yield e
    await e.dispose()

# 3. TRUNCATE autouse antes de cada test
@pytest_asyncio.fixture(autouse=True)
async def _truncate(engine):
    async with engine.begin() as conn:
        # TRUNCATE todas las tablas excepto alembic_version
        ...
    yield

# 4. Cliente AsyncClient (no TestClient — incompatible con fixtures async)
@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

### Pyproject config mínima
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
testpaths = ["tests"]
pythonpath = ["."]
```

---

## Trampas que NO se deben repetir

1. **No asumir que un rebuild con cache va a refrescar el venv.** Si cambian deps o venv-related, hacer `docker builder prune -af` + `docker image rm` + rebuild.

2. **No mezclar `python -m venv` con `uv venv`** en el mismo Dockerfile. Elige uno.

3. **No usar `os.environ.setdefault`** para test DB URL si docker-compose inyecta una. Usar asignación directa.

4. **No usar `TestClient` (sync) de FastAPI** con fixtures async. El resultado: tests que fallan o nunca terminan. Usar `AsyncClient` con `ASGITransport`.

5. **No usar `asyncio.run()` dentro de fixtures async** — genera loops separados que rompen las conexiones de asyncpg.

6. **No usar `pip install` directo en el Dockerfile** — usar `uv pip install` consistente con el resto del proyecto.

7. **No olvidar `asyncio.run(algo())` requiere un loop CERRADO al final**, sino el garbage collector tira warnings.

8. **No dejar conexiones idle en el backend en runtime** durante tests en la misma DB. Solución: DB de tests separada.

9. **No confiar en que `--no-cache` reconstruye todo** si BuildKit tiene cache externo. Verificar con `docker image ls` que la imagen cambió.

10. **No incluir `--reload` con uvicorn en tests** — causa re-inicialización del engine que rompe conexiones.

---

## Comandos frecuentes que valen oro

```bash
# Setup completo desde cero
make fclean && make build && make up

# Ver estado y logs
make ps && make logs-be

# DB de tests y tests
make test-setup && make test

# Generar migración nueva
make makemigration m="descripcion"

# Debug: entrar al container
make shell

# DB shell directo
make db-shell

# Inspeccionar imagen si algo está raro
docker run --rm --entrypoint bash <image> -c 'ls -la /app/.venv/bin/python; cat /app/.venv/pyvenv.cfg'

# Matar conexiones colgadas en Postgres
docker exec gym-postgres psql -U gym -d gym -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'gym';"

# Limpiar todo el build cache si está corrupto
docker builder prune -af
```

---

## Workflow recomendado para nuevos features (Etapas futuras)

1. Definir modelos en `app/models/` (centralizados, no por módulo)
2. `make makemigration m="..."` para generar migración
3. Editar la migración si necesita `CREATE EXTENSION`, `DO $$` para enums, o seed data
4. `make migrate` para aplicar
5. Schemas Pydantic en `app/modules/<feature>/schemas.py`
6. Service en `app/modules/<feature>/service.py` (lógica de negocio)
7. Router en `app/modules/<feature>/router.py` (con `GymRoleChecker` si aplica)
8. Registrar en `app/api/v1.py`
9. Tests en `tests/test_<feature>.py`
10. `make test` para validar

---

## Estado al cierre de este bloque

- Etapa 0 ✅ Setup base (Docker, configs, Makefile)
- Etapa 1 ✅ Auth + Gyms + Users + Tests (40 tests passing)
  - `POST /gyms/{gym_id}/users` (nuevo): owner/manager crea user con rol CLIENT o MANAGER
  - `kind_role` solo respetado si caller es OWNER; MANAGER siempre crea CLIENT
  - `POST /auth/register` eliminado (era bug: no creaba GymUser)
- Etapa 2 ❌ Saltada: Members + Memberships como tablas separadas = overengineering
  - `User` + `GymUser(role=CLIENT)` ya modelan el concepto
  - Embeddings faciales y access logs se atan a `user_id` directamente
- Etapa 3 ⏳ Motor facial (6/8 fases hechas)
  - `app/modules/face/`: schemas, exceptions, engine, dependencies
  - Enum rename: `OPERATOR` → `CLIENT` (migración `b67c2a3d4e5f`)
  - `FaceEngine` con `_app: FaceAnalysis | None` para degraded mode
  - Provider name correcto: `CPUExecutionProvider` (no `CPU`)
  - Defense in depth: size → magic bytes → format whitelist → RGB
  - Pendiente: Fase 7 (lifespan + dependency integration) y Fase 8 (tests con caras reales LFW)
- Pendientes: Etapas 4-8 (enrolamiento, verificación, frontend, docs)

## Sobre la skill `instructor-mode`

Creada en `~/.claude/skills/instructor-mode/SKILL.md`. Actívala cuando el usuario pida aprender paso a paso o después de planificar una feature. NO para tareas mecánicas ni bugfixes donde pidió solución directa.

## Aprendizajes específicos de InsightFace (Etapa 3)

### `buffalo_l` y los "packs" de modelos
- `buffalo_l` = bundle con detector + recognizer + landmarks + genderage
- Solo cargamos `["detection", "recognition"]` (allowed_modules), ahorrando ~100MB
- El recognizer (`w600k_r50.onnx`) produce embeddings de 512-d normalizados

### Nombres de providers en ONNX Runtime
- "CPU" NO es el nombre correcto — es `"CPUExecutionProvider"`
- InsightFace hace fallback automático pero ensucia logs con `EP Error`
- Fix: usar el nombre completo en `.env` y en `Settings` default

### `docker compose restart` vs `down`+`up` para env_file
- `restart` a veces no re-lee `env_file` (el container mantiene env viejo)
- `down` + `up` siempre toma los cambios
- Para cambios en `.env` usar `down` + `up`

### Errores comunes de Python que aprendimos
- `len(x > 10)` vs `len(x) > 10` (paréntesis mal = TypeError)
- `try/except` con `return` en el except → olvidar el success path → función no hace nada
- `tuple[str, str] = [...]` (type hint de tupla pero asignación de lista) — type hint incorrecto

### Degraded mode pattern
- `app.state.X: T | None` con check en dependency
- Permite que la app arranque aunque un componente crítico falle
- Trade-off: complejidad vs disponibilidad

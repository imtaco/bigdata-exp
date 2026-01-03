
superset mgr init
https://github.com/apache/superset/blob/465e2a9631994892cf399d13dd926c56cecd58ca/docker/entrypoints/run-server.sh

https://superset.apache.org/docs/6.0.0/intro

```bash
# create table schema
superset db upgrade
# setup roles & permissions
superset init

# create admin
superset fab create-admin \
    --username admin \
    --password admin \
    --firstname admin \
    --lastname admin \
    --email admin@local
```

trino://trino@trino:8080/iceberg

### superset config to be tried
async query

```py
import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DATABASE_URI",
    "sqlite:////app/superset_home/superset.db",
)

# 啟動 Celery（async SQL query）
class CeleryConfig(object):
    broker_url = "redis://redis:6379/0"
    result_backend = "redis://redis:6379/1"

CELERY_CONFIG = CeleryConfig

# Redis cache
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 2,
}

# async query
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ASYNC_QUERIES": True,
}
```

```yaml
  superset:
    image: apache/superset:2.1.0
    container_name: superset
    ports:
      - "8088:8088"
    environment:
      SUPERSET_SECRET_KEY: "superset_secret_key"
      SUPERSET_DATABASE_URI: "postgresql+psycopg2://superset:superset@superset-db:5432/superset"

      # async query 需要
      REDIS_HOST: redis
      FROM_SUPERSET: "1"
    volumes:
      - ./superset/superset_config.py:/app/pythonpath/superset_config.py
    depends_on:
      - superset-db
      - redis
    command:
      - /bin/bash
      - -c
      - |
        superset db upgrade
        superset init
        superset fab create-admin \
            --username admin \
            --password admin \
            --firstname admin \
            --lastname admin \
            --email admin@local || true
        superset run -h 0.0.0.0 -p 8088

  worker:
    image: apache/superset:2.1.0
    container_name: superset-worker
    depends_on:
      - superset-db
      - redis
    environment:
      SUPERSET_SECRET_KEY: "superset_secret_key"
      SUPERSET_DATABASE_URI: "postgresql+psycopg2://superset:superset@superset-db:5432/superset"
      CELERY_BROKER_URL: "redis://redis:6379/0"
      CELERY_RESULT_BACKEND: "redis://redis:6379/1"
    command: "celery --app=superset.tasks.celery_app:app worker"

  beat:
    image: apache/superset:2.1.0
    container_name: superset-beat
    depends_on:
      - superset-db
      - redis
    environment:
      SUPERSET_SECRET_KEY: "superset_secret_key"
      SUPERSET_DATABASE_URI: "postgresql+psycopg2://superset:superset@superset-db:5432/superset"
      CELERY_BROKER_URL: "redis://redis:6379/0"
      CELERY_RESULT_BACKEND: "redis://redis:6379/1"
    command: "celery --app=superset.tasks.celery_app:app beat --pidfile=/tmp/celerybeat.pid"
```

check beat

```bash
/app/.venv/bin/python3 - <<EOF
from superset.app import create_app

app = create_app()

with app.app_context():
    print("FEATURE_FLAGS =", app.config.get("FEATURE_FLAGS"))
    print("ENABLE_ALERTS =", app.config.get("ENABLE_ALERTS"))
EOF

/app/.venv/bin/python3 - <<EOF
from superset.tasks.celery_app import app
import pprint
pprint.pprint(app.conf.beat_schedule)
EOF

/app/.venv/bin/python3 /app/.venv/bin/celery -A superset.tasks.celery_app inspect scheduled
```

### parquet compaction

| 操作                 | 頻率    | 保留期    |
|---------------------|---------|--------|
| optimize            | 每天/每週 | -      |
| expire_snapshots    | 每週    | 7-30 天 |
| remove_orphan_files | 每週    | 3-7 天  |


```sql
create table iceberg.demo.compact_demo (
    id BIGINT,
    name VARCHAR,
    category VARCHAR
) WITH (
    format = 'PARQUET',
    partitioning = ARRAY['category']
);


-- one insert one file -> 8 files
INSERT INTO iceberg.demo.compact_demo VALUES (1, 'item1', 'A');
INSERT INTO iceberg.demo.compact_demo VALUES (2, 'item2', 'A');
INSERT INTO iceberg.demo.compact_demo VALUES (3, 'item3', 'A');
INSERT INTO iceberg.demo.compact_demo VALUES (4, 'item5', 'A');
INSERT INTO iceberg.demo.compact_demo VALUES (7, 'item1', 'B');
INSERT INTO iceberg.demo.compact_demo VALUES (8, 'item2', 'B');
INSERT INTO iceberg.demo.compact_demo VALUES (9, 'item3', 'B');
INSERT INTO iceberg.demo.compact_demo VALUES (6, 'item5', 'B');

-- investigation
SELECT * FROM iceberg.demo."compact_demo$snapshots";
SELECT * FROM iceberg.demo."compact_demo$files";

-- compaction
ALTER TABLE iceberg.demo.compact_demo  EXECUTE optimize;

-- remove minIO files
-- parquets are de-reference, but files remains
SET SESSION iceberg.expire_snapshots_min_retention = '0s';
SET SESSION iceberg.remove_orphan_files_min_retention = '0s';

ALTER TABLE iceberg.demo.compact_demo
EXECUTE expire_snapshots(retention_threshold => '0s');

ALTER TABLE iceberg.demo.compact_demo
EXECUTE remove_orphan_files(retention_threshold => '0s');
```
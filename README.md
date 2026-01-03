# Modern Data Analytics Stack Experiment

A self-hosted data analytics platform featuring Trino, Apache Iceberg, Apache Superset, and MinIO. This stack provides a cost-effective alternative to cloud data warehouses like BigQuery, with full support for ACID transactions, time travel queries, and complex analytical workloads.

## Architecture Overview

```mermaid
graph TB
    subgraph Superset["Apache Superset<br/>(Business Intelligence & Visualization)"]
        SupersetWeb[Superset Web]
        SupersetWorker[Superset Workers]
        SupersetBeat[Beat Scheduler]
    end

    Redis[Redis<br/>Cache & Broker]

    subgraph Trino["Trino Query Engine<br/>(Distributed Processing)"]
        TrinoCoordinator[Trino Coordinator]
        TrinoWorkers[Trino Workers]
        NginxProxy[Nginx Proxy<br/>Optional Delay Testing]
    end

    PostgreSQL["PostgreSQL<br/>(Iceberg Catalog)"]
    MinIO["MinIO<br/>(S3-Compatible Storage)"]

    subgraph Iceberg["Apache Iceberg"]
        IcebergFeatures["✓ ACID Transactions<br/>✓ Time Travel<br/>✓ Schema Evolution"]
    end

    SupersetWeb --> Redis
    SupersetWorker --> Redis
    SupersetBeat --> Redis
    Redis --> TrinoCoordinator
    NginxProxy -.-> TrinoCoordinator
    TrinoCoordinator --> TrinoWorkers
    TrinoCoordinator --> PostgreSQL
    TrinoCoordinator --> MinIO
    PostgreSQL --> IcebergFeatures
    MinIO --> IcebergFeatures

    style Superset fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style Trino fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style Iceberg fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style Redis fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    style PostgreSQL fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style MinIO fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

## Key Features

- **Trino Query Engine**: High-performance distributed SQL query engine supporting complex joins and aggregations
- **Apache Iceberg**: Modern table format with ACID transactions, time travel, and schema evolution
- **Apache Superset**: Modern, enterprise-ready business intelligence platform
- **MinIO**: High-performance S3-compatible object storage
- **PostgreSQL**: Reliable metadata storage for Iceberg catalog and Superset
- **Redis**: Caching and message broker for async query processing
- **Production-Ready**: Includes async queries, alerts, caching, and worker pools

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 8GB of available RAM
- 10GB of free disk space

### 1. Build Superset Image

```bash
# Build the custom Superset image with Trino and BigQuery drivers
docker build -f Dockerfile.superset -t superset-trino:latest .
```

### 2. Start All Services

```bash
# Start the entire stack
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Wait for Services to Initialize

```bash
# Monitor Trino startup
docker-compose logs -f trino

# Check if Trino is ready
curl http://localhost:8080/v1/info
```

### 4. Initialize MinIO Buckets

```bash
# Install MinIO client (one-time setup)
# macOS:
brew install minio/stable/mc
# Linux:
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure MinIO alias
mc alias set myminio http://localhost:9000 admin password

# Create required buckets
mc mb myminio/warehouse || true
mc mb myminio/data || true
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Trino Web UI | http://localhost:8080 | Username: `admin`, Password: (from password.db) |
| Superset | http://localhost:8088 | Username: `admin`, Password: `admin` |
| MinIO Console | http://localhost:9001 | Username: `admin`, Password: `password` |
| MailHog (Email Testing) | http://localhost:8025 | No authentication |
| Trino Proxy (with delay) | http://localhost:8081 | Same as Trino |

## Working with Trino

### Connect via Docker CLI

```bash
# Enter Trino CLI
docker exec -it trino trino

# Connect with specific catalog and schema
docker exec -it trino trino --catalog iceberg --schema default
```

### Connect via Local Trino CLI

```bash
# Install Trino CLI
# macOS:
brew install trino

# Connect to Trino
trino --server localhost:8080 --catalog iceberg --schema default --user admin
```

### Connect via Database Tools

Compatible with DBeaver, DataGrip, and other JDBC clients:

- **Driver**: Trino
- **Host**: localhost
- **Port**: 8080
- **Catalog**: iceberg
- **Schema**: default
- **User**: admin
- **Password**: (check trino/password.db)

## Basic Operations

### Create Schema and Tables

```sql
-- View available catalogs
SHOW CATALOGS;

-- Create a schema (equivalent to BigQuery dataset)
CREATE SCHEMA IF NOT EXISTS demo
WITH (location = 's3://warehouse/demo');

USE iceberg.demo;

-- Create a table with partitioning
CREATE TABLE users (
    user_id BIGINT,
    username VARCHAR,
    email VARCHAR,
    created_at TIMESTAMP(6),
    is_active BOOLEAN
) WITH (
    format = 'PARQUET',
    location = 's3://warehouse/demo/users',
    partitioning = ARRAY['day(created_at)']
);

-- Insert data
INSERT INTO users VALUES
(1, 'alice', 'alice@example.com', CURRENT_TIMESTAMP, true),
(2, 'bob', 'bob@example.com', CURRENT_TIMESTAMP, true),
(3, 'charlie', 'charlie@example.com', CURRENT_TIMESTAMP, false);

-- Query data
SELECT * FROM users;
```

### Complex Multi-Table Joins

```sql
-- Create related tables
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT,
    product_id BIGINT,
    amount DECIMAL(10,2),
    order_date DATE
) WITH (
    format = 'PARQUET',
    location = 's3://warehouse/demo/orders'
);

CREATE TABLE products (
    product_id BIGINT,
    product_name VARCHAR,
    category VARCHAR,
    price DECIMAL(10,2)
) WITH (
    format = 'PARQUET',
    location = 's3://warehouse/demo/products'
);

-- Complex analytical query with window functions
SELECT
    u.username,
    u.email,
    o.order_id,
    p.product_name,
    p.category,
    o.amount,
    o.order_date,
    COUNT(*) OVER (PARTITION BY u.user_id) as user_total_orders,
    SUM(o.amount) OVER (PARTITION BY u.user_id) as user_total_spent
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id
INNER JOIN products p ON o.product_id = p.product_id
WHERE u.is_active = true
ORDER BY o.order_date DESC;
```

## Iceberg Time Travel

```sql
-- View table snapshot history
SELECT * FROM "users$snapshots" ORDER BY committed_at DESC;

-- View table change history
SELECT * FROM "users$history";

-- Query data at a specific timestamp
SELECT * FROM users
FOR TIMESTAMP AS OF TIMESTAMP '2024-01-15 10:00:00';

-- Query using snapshot ID
SELECT * FROM users
FOR VERSION AS OF 1234567890123456789;

-- View table files
SELECT * FROM "users$files";
```

## Table Maintenance

### Compaction (Optimize Small Files)

```sql
-- Compact all files
ALTER TABLE users EXECUTE optimize;

-- Compact with filter
ALTER TABLE users EXECUTE optimize WHERE created_at >= DATE '2024-01-01';
```

### Snapshot and File Cleanup

```sql
-- Expire old snapshots (older than 7 days)
ALTER TABLE users EXECUTE expire_snapshots(retention_threshold => '7d');

-- Remove orphaned files
ALTER TABLE users EXECUTE remove_orphan_files(retention_threshold => '7d');

-- For testing only - aggressive cleanup
SET SESSION iceberg.expire_snapshots_min_retention = '0s';
SET SESSION iceberg.remove_orphan_files_min_retention = '0s';

ALTER TABLE users EXECUTE expire_snapshots(retention_threshold => '0s');
ALTER TABLE users EXECUTE remove_orphan_files(retention_threshold => '0s');
```

## Bulk Data Upload

### Using the Upload Script

Upload large Parquet files efficiently to Iceberg tables:

```bash
# Basic upload
python upload_trino.py data.parquet demo.sales

# Upload with custom compression
python upload_trino.py data.parquet demo.sales --compression zstd --compression-level 3

# Upload with specific batch size
python upload_trino.py data.parquet demo.sales --batch-size 50000

# Upload with dictionary encoding control
python upload_trino.py data.parquet demo.sales --use-dictionary yes

# Upload to external catalog
python upload_trino.py data.parquet demo.sales \
  --jdbc-uri postgresql://iceberg:iceberg@localhost:5432/iceberg_catalog \
  --s3-endpoint http://localhost:9000
```

### Script Features

- Streaming upload with memory-efficient processing
- Automatic compression optimization (snappy, gzip, zstd, lz4)
- Dictionary encoding control
- Progress tracking with speed metrics
- No temporary storage required

## Apache Superset Integration

### Initial Setup

Superset is automatically initialized on first start. Default credentials:

- **Username**: admin
- **Password**: admin

### Connect Trino to Superset

1. Navigate to **Data** → **Databases** → **+ Database**
2. Select **Trino** from the list
3. Enter connection URI:
   ```
   trino://trino@trino:8080/iceberg
   ```
4. Test connection and save

### Features Enabled

- **Async Queries**: Long-running queries execute in background via Celery workers
- **Redis Cache**: Query result caching for improved performance
- **Email Alerts**: Report scheduling with email delivery (via MailHog for testing)
- **Custom Hooks**: SQL logging, quota management, and report hooks

### Superset Components

- **superset**: Main web application (port 8088)
- **superset-worker**: Celery worker for async query execution
- **superset-beat**: Celery beat scheduler for reports and alerts
- **redis**: Message broker and cache backend
- **mailhog**: Email testing server (port 8025)

## Performance Optimization

### Partitioning Strategies

```sql
-- Time-based partitioning (most common)
CREATE TABLE events (
    event_id BIGINT,
    event_type VARCHAR,
    user_id BIGINT,
    event_time TIMESTAMP(6)
) WITH (
    format = 'PARQUET',
    partitioning = ARRAY['day(event_time)']
);

-- Multi-column partitioning
CREATE TABLE sales (
    sale_id BIGINT,
    region VARCHAR,
    sale_date DATE,
    amount DECIMAL(10,2)
) WITH (
    format = 'PARQUET',
    partitioning = ARRAY['region', 'year(sale_date)']
);
```

### Bucketing for High-Cardinality Columns

```sql
-- Optimize JOIN performance with bucketing
CREATE TABLE large_table (
    id BIGINT,
    data VARCHAR
) WITH (
    format = 'PARQUET',
    sorted_by = ARRAY['id'],
    bucketed_by = ARRAY['id'],
    bucket_count = 16
);
```

### Compression Configuration

```sql
-- Use advanced compression
CREATE TABLE compressed_data (
    id BIGINT,
    large_text VARCHAR
) WITH (
    format = 'PARQUET',
    parquet_compression = 'ZSTD'  -- Options: SNAPPY, GZIP, LZ4, ZSTD
);
```

## Monitoring and Diagnostics

### View Running Queries

```sql
-- Check currently executing queries
SELECT
    query_id,
    state,
    query,
    elapsed_time_millis / 1000.0 as elapsed_seconds
FROM system.runtime.queries
WHERE state = 'RUNNING';
```

### View Cluster Status

```sql
-- Check node status
SELECT * FROM system.runtime.nodes;

-- Check task execution
SELECT * FROM system.runtime.tasks
WHERE state = 'RUNNING';
```

### Using Trino Web UI

Navigate to http://localhost:8080 to:

- View query execution plans
- Monitor resource utilization
- Analyze query performance
- Debug slow queries

## Project Structure

```
bigdata-exp/
├── docker-compose.yml              # Main orchestration file
├── Dockerfile.superset             # Custom Superset image
├── requirements.txt                # Python dependencies
├── post-constraints.txt            # Additional package constraints
├── upload_trino.py                 # Parquet upload utility
│
├── trino/                          # Trino configuration
│   ├── config.properties           # Coordinator settings
│   ├── worker-config.properties    # Worker settings
│   ├── core-site.xml               # Hadoop configuration
│   ├── password-authenticator.properties
│   ├── password.db                 # User credentials
│   └── catalog/
│       └── iceberg.properties      # Iceberg catalog config
│
├── pythonpath/                     # Superset configuration
│   ├── superset_config.py          # Web server config
│   ├── superset_worker_config.py   # Worker config
│   ├── superset_config_base.py     # Shared config
│   └── hooks/                      # Custom hooks
│       ├── sqllab_hooks.py         # SQL Lab quota
│       ├── chart_hooks.py          # Chart customizations
│       ├── quota.py                # Resource quotas
│       ├── report_hooks.py         # Report scheduling
│       └── sql_logging.py          # Query logging
│
├── nginx.conf                      # Proxy configuration
├── TRINO_QUICKSTART.md             # Trino quick start guide (中文)
└── superset.md                     # Superset notes (中文)
```

## Common Commands

```bash
# Stop all services
docker-compose down

# Stop and remove all data (CAUTION!)
docker-compose down -v

# Restart specific service
docker-compose restart trino

# View service logs
docker-compose logs -f postgres
docker-compose logs -f superset

# Scale workers (if configured)
docker-compose up -d --scale trino-worker=3

# Execute SQL directly
docker exec -it trino trino --execute "SELECT * FROM system.runtime.nodes"

# Backup PostgreSQL metadata
docker exec pg1616 pg_dump -U iceberg iceberg_catalog > backup.sql

# Restore PostgreSQL metadata
docker exec -i pg1616 psql -U iceberg iceberg_catalog < backup.sql
```

## Production Deployment Checklist

### Security

- [ ] Enable Trino authentication (configured in config.properties)
- [ ] Change default passwords (MinIO, PostgreSQL, Superset)
- [ ] Configure TLS/SSL for all services
- [ ] Set strong `SUPERSET_SECRET_KEY` and `GLOBAL_ASYNC_QUERIES_JWT_SECRET`
- [ ] Review and restrict network access

### Resource Allocation

- [ ] Adjust Trino memory settings based on available RAM
- [ ] Configure appropriate worker count
- [ ] Set PostgreSQL connection pool limits
- [ ] Configure Redis memory limits

### Monitoring

- [ ] Integrate with Prometheus for metrics collection
- [ ] Setup Grafana dashboards for visualization
- [ ] Configure alerting for service failures
- [ ] Enable query auditing and logging

### Backup Strategy

- [ ] Schedule regular PostgreSQL backups (Iceberg catalog)
- [ ] Backup MinIO data periodically
- [ ] Document disaster recovery procedures
- [ ] Test backup restoration process

### Maintenance Schedule

| Operation | Frequency | Command |
|-----------|-----------|---------|
| Table optimization (compact) | Daily/Weekly | `ALTER TABLE ... EXECUTE optimize` |
| Expire old snapshots | Weekly | `EXECUTE expire_snapshots(retention_threshold => '7d')` |
| Remove orphaned files | Weekly | `EXECUTE remove_orphan_files(retention_threshold => '7d')` |
| PostgreSQL vacuum | Weekly | `VACUUM ANALYZE` |
| Review slow queries | Daily | Check Trino Web UI |

## Troubleshooting

### Trino Connection Failures

```bash
# Check if PostgreSQL is running
docker-compose ps pg1616

# View PostgreSQL logs
docker-compose logs pg1616

# Check Trino logs
docker-compose logs trino

# Verify catalog configuration
docker exec -it trino cat /etc/trino/catalog/iceberg.properties
```

### Slow Query Performance

1. Check if data is properly partitioned
2. Run table optimization: `ALTER TABLE ... EXECUTE optimize`
3. Increase worker count
4. Adjust `query.max-memory` in config.properties
5. Review query execution plan in Trino Web UI

### Superset Issues

```bash
# Check Superset logs
docker-compose logs superset

# Check worker logs (for async queries)
docker-compose logs superset-worker

# Check beat scheduler logs (for reports)
docker-compose logs superset-beat

# Verify Redis connectivity
docker exec -it superset redis-cli -h redis ping
```

### MinIO Connection Issues

```bash
# Check MinIO status
docker-compose logs minio

# Verify buckets exist
mc ls myminio

# Test S3 connectivity from Trino
docker exec -it trino trino --execute "SELECT * FROM iceberg.information_schema.schemata"
```

## FAQ

**Q: How does this compare to BigQuery?**

A: This stack provides similar capabilities to BigQuery but runs on your own infrastructure. You get:
- Full data ownership and control
- No egress costs
- ACID transactions via Iceberg
- Complex JOIN support via Trino
- Time travel queries
- Similar SQL syntax

**Q: Can I connect other data sources to Trino?**

A: Yes! Trino supports numerous connectors. Add new connector configurations in `trino/catalog/`:
- PostgreSQL, MySQL, Oracle, SQL Server
- MongoDB, Cassandra, Elasticsearch
- Kafka, Redis
- Cross-database JOINs are supported

**Q: How do I add more Trino workers?**

A: Edit docker-compose.yml and add additional worker services (trino-worker-2, trino-worker-3, etc.) following the trino-worker-1 pattern.

**Q: Is this suitable for production use?**

A: Yes, with proper configuration. Ensure you:
- Enable authentication and encryption
- Configure appropriate resource limits
- Set up monitoring and backups
- Review the Production Deployment Checklist above

**Q: How much data can this handle?**

A: Trino and Iceberg are designed for petabyte-scale workloads. Actual capacity depends on your hardware resources, partitioning strategy, and query patterns.

## Additional Resources

- [Trino Documentation](https://trino.io/docs/current/)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [TRINO_QUICKSTART.md](TRINO_QUICKSTART.md) - Detailed Trino guide (中文)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project configuration is provided as-is for educational and production use. Individual components (Trino, Iceberg, Superset, MinIO) are governed by their respective licenses.

---

**Built with**: Trino 478 • Apache Iceberg • Apache Superset 5.0.0 • MinIO • PostgreSQL 16 • Redis 7

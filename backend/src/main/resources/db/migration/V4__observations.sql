CREATE TABLE external_data_sources (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    base_url VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT
);

CREATE TABLE api_tasks (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT REFERENCES farms(id),
    source_code VARCHAR(40) NOT NULL,
    external_task_id VARCHAR(120),
    task_type VARCHAR(20),
    request_json JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    last_polled_at TIMESTAMPTZ,
    bundle_id VARCHAR(120),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_api_tasks_status ON api_tasks(status);

CREATE TABLE api_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    source_code VARCHAR(40) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    http_status INT,
    request_meta JSONB,
    response_meta JSONB,
    raw_response JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    duration_ms BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sync_logs_source ON api_sync_logs(source_code);
CREATE INDEX idx_sync_logs_created ON api_sync_logs(created_at DESC);

CREATE TABLE satellite_observations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    source_code VARCHAR(40) NOT NULL,
    product VARCHAR(60) NOT NULL,
    layer VARCHAR(80) NOT NULL,
    observed_date DATE NOT NULL,
    value NUMERIC(12,4),
    units VARCHAR(20),
    quality_flag VARCHAR(40),
    raw_ref BIGINT REFERENCES api_sync_logs(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (farm_id, source_code, product, layer, observed_date)
);

CREATE TABLE vegetation_observations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    source_code VARCHAR(40) NOT NULL,
    indicator VARCHAR(40) NOT NULL,
    observed_period VARCHAR(20) NOT NULL,
    value NUMERIC(8,4),
    ts_type VARCHAR(20),
    raw_ref BIGINT REFERENCES api_sync_logs(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE temperature_observations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    source_code VARCHAR(40) NOT NULL,
    observed_date DATE NOT NULL,
    lst_day_c NUMERIC(6,2),
    lst_night_c NUMERIC(6,2),
    raw_ref BIGINT REFERENCES api_sync_logs(id)
);

CREATE TABLE soil_observations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    source_code VARCHAR(40) NOT NULL,
    property VARCHAR(60) NOT NULL,
    depth VARCHAR(30) NOT NULL,
    value NUMERIC(12,4),
    uncertainty JSONB,
    raw_ref BIGINT REFERENCES api_sync_logs(id),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (farm_id, source_code, property, depth)
);

CREATE TABLE weather_observations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    source_code VARCHAR(60) NOT NULL,
    observed_date DATE NOT NULL,
    rainfall_mm NUMERIC(8,2),
    temp_min_c NUMERIC(6,2),
    temp_max_c NUMERIC(6,2),
    humidity_pct NUMERIC(5,2)
);

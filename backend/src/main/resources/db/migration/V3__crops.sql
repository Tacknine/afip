CREATE TABLE crops (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    category VARCHAR(80)
);

CREATE TABLE crop_varieties (
    id BIGSERIAL PRIMARY KEY,
    crop_id BIGINT NOT NULL REFERENCES crops(id),
    name VARCHAR(120) NOT NULL,
    maturity_days INT,
    UNIQUE (crop_id, name)
);

CREATE TABLE planting_records (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    crop_variety_id BIGINT REFERENCES crop_varieties(id),
    planting_date DATE NOT NULL,
    expected_harvest DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crop_growth_stages (
    id BIGSERIAL PRIMARY KEY,
    planting_id BIGINT NOT NULL REFERENCES planting_records(id) ON DELETE CASCADE,
    stage_name VARCHAR(80) NOT NULL,
    observed_at DATE NOT NULL,
    notes TEXT
);

CREATE TABLE harvest_records (
    id BIGSERIAL PRIMARY KEY,
    planting_id BIGINT NOT NULL REFERENCES planting_records(id),
    harvest_date DATE NOT NULL,
    yield_kg NUMERIC(12,2),
    quality_notes TEXT
);

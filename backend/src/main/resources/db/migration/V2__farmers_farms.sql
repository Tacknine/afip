CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE administrative_areas (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    level VARCHAR(20) NOT NULL,
    adm_id VARCHAR(50),
    geom GEOMETRY(MULTIPOLYGON, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_admin_geom ON administrative_areas USING GIST (geom);

CREATE TABLE farmers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    village VARCHAR(120),
    district VARCHAR(120),
    region VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE farms (
    id BIGSERIAL PRIMARY KEY,
    farmer_id BIGINT NOT NULL REFERENCES farmers(id),
    name VARCHAR(200) NOT NULL,
    area_ha NUMERIC(12,4),
    centroid GEOGRAPHY(POINT, 4326),
    admin_area_id BIGINT REFERENCES administrative_areas(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_farms_farmer ON farms(farmer_id);

CREATE TABLE farm_boundaries (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    geom GEOMETRY(POLYGON, 4326) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'MANUAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_farm_boundary_geom ON farm_boundaries USING GIST (geom);
CREATE INDEX idx_farm_boundary_farm ON farm_boundaries(farm_id);

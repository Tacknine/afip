CREATE TABLE risk_assessments (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    risk_category VARCHAR(60) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence NUMERIC(4,2),
    supporting_data JSONB NOT NULL,
    recommended_action TEXT NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recommendations (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    reason TEXT NOT NULL,
    supporting_data JSONB NOT NULL,
    priority VARCHAR(20) NOT NULL,
    confidence NUMERIC(4,2),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE farm_activities (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    activity VARCHAR(100) NOT NULL,
    notes TEXT,
    performed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE model_versions (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(30) NOT NULL,
    trained_at TIMESTAMPTZ,
    metrics JSONB,
    UNIQUE (model_name, version)
);

CREATE TABLE model_predictions (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT NOT NULL REFERENCES farms(id),
    model_version_id BIGINT NOT NULL REFERENCES model_versions(id),
    prediction_type VARCHAR(60) NOT NULL,
    value NUMERIC(12,4),
    confidence NUMERIC(4,2),
    predicted_for DATE,
    inputs JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    channel VARCHAR(20) NOT NULL,
    lang VARCHAR(5) NOT NULL DEFAULT 'sw',
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_user ON notifications(user_id, read_at);

-- Latest cached AI Anomaly Radar scan per persona (Genie deep-research agent).
-- One row per persona; refreshed at most once per day (or on demand).
CREATE TABLE IF NOT EXISTS "anomaly_scan" (
    "persona" TEXT NOT NULL,
    "scan_date" DATE NOT NULL,
    "summary" TEXT,
    "high" INTEGER NOT NULL DEFAULT 0,
    "medium" INTEGER NOT NULL DEFAULT 0,
    "low" INTEGER NOT NULL DEFAULT 0,
    "content" TEXT NOT NULL DEFAULT '',
    "blocks" JSONB,
    "sources" JSONB,
    "steps" INTEGER,
    "engine" TEXT NOT NULL DEFAULT 'genie_agent',
    "conversation_id" TEXT,
    "generated_by" TEXT,
    "generated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "anomaly_scan_pkey" PRIMARY KEY ("persona")
);

-- Same-day cache of the full Member Early-Warning scoring pass (credit-risk PD
-- model on Model Serving). One row (id=1); refreshed daily or on demand.
CREATE TABLE IF NOT EXISTS "early_warning_cache" (
    "id" INTEGER NOT NULL DEFAULT 1,
    "scan_date" DATE NOT NULL,
    "endpoint" TEXT,
    "model_version" TEXT,
    "payload" JSONB,
    "generated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "early_warning_cache_pkey" PRIMARY KEY ("id")
);

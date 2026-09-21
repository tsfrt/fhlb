-- Cached morning briefing per persona + engine (AI Gateway vs Genie agent).
-- Both engines generated on first load each day and cached (once-per-day cadence).
CREATE TABLE IF NOT EXISTS "briefing_cache" (
    "persona" TEXT NOT NULL,
    "engine" TEXT NOT NULL,
    "scan_date" DATE NOT NULL,
    "payload" JSONB NOT NULL,
    "generated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "briefing_cache_pkey" PRIMARY KEY ("persona", "engine")
);

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateTable
CREATE TABLE "annotation" (
    "id" TEXT NOT NULL,
    "persona" TEXT NOT NULL,
    "widget_key" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "annotation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "watchlist_item" (
    "id" TEXT NOT NULL,
    "member_id" TEXT NOT NULL,
    "member_name" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "severity" TEXT NOT NULL DEFAULT 'medium',
    "added_by" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "watchlist_item_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "alert_ack" (
    "id" TEXT NOT NULL,
    "alert_key" TEXT NOT NULL,
    "persona" TEXT NOT NULL,
    "acknowledged_by" TEXT NOT NULL,
    "note" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "alert_ack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "exam_request" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "examiner" TEXT NOT NULL,
    "due_date" TIMESTAMP(3),
    "status" TEXT NOT NULL DEFAULT 'open',
    "created_by" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "exam_request_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "exam_pack_item" (
    "id" TEXT NOT NULL,
    "exam_request_id" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "source_type" TEXT NOT NULL,
    "source_ref" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "exam_pack_item_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_narrative_audit" (
    "id" TEXT NOT NULL,
    "persona" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "endpoint" TEXT NOT NULL,
    "prompt" TEXT NOT NULL,
    "response" TEXT NOT NULL,
    "guardrail_verdict" TEXT NOT NULL,
    "request_id" TEXT,
    "latency_ms" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_narrative_audit_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "anomaly_scan" (
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

-- CreateTable
CREATE TABLE "briefing_cache" (
    "persona" TEXT NOT NULL,
    "engine" TEXT NOT NULL,
    "scan_date" DATE NOT NULL,
    "payload" JSONB NOT NULL,
    "generated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "briefing_cache_pkey" PRIMARY KEY ("persona", "engine")
);

-- CreateTable
CREATE TABLE "saved_view" (
    "id" TEXT NOT NULL,
    "persona" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "owner" TEXT NOT NULL,
    "config" JSONB NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "saved_view_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "annotation_persona_widget_key_idx" ON "annotation"("persona", "widget_key");

-- CreateIndex
CREATE UNIQUE INDEX "watchlist_item_member_id_key" ON "watchlist_item"("member_id");

-- CreateIndex
CREATE UNIQUE INDEX "alert_ack_alert_key_key" ON "alert_ack"("alert_key");

-- CreateIndex
CREATE INDEX "exam_pack_item_exam_request_id_idx" ON "exam_pack_item"("exam_request_id");

-- CreateIndex
CREATE INDEX "ai_narrative_audit_persona_created_at_idx" ON "ai_narrative_audit"("persona", "created_at");

-- AddForeignKey
ALTER TABLE "exam_pack_item" ADD CONSTRAINT "exam_pack_item_exam_request_id_fkey" FOREIGN KEY ("exam_request_id") REFERENCES "exam_request"("id") ON DELETE CASCADE ON UPDATE CASCADE;


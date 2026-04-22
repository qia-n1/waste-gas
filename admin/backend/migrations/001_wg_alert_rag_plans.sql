-- Migration: 001_wg_alert_rag_plans
-- Purpose : 存储 RAG 生成的告警处置方案；管理端写入，所有端共享读取
-- Owner   : admin/backend
-- Created : 2026-04-20

CREATE TABLE IF NOT EXISTS public.wg_alert_rag_plans (
    id                  SERIAL          PRIMARY KEY,
    alert_id            INTEGER         NOT NULL
                        REFERENCES public.wg_alerts(id) ON DELETE CASCADE,
    version             INTEGER         NOT NULL DEFAULT 1,

    -- RAG 输出主体
    title               VARCHAR(120)    NOT NULL,
    suggestion_short    TEXT            NOT NULL,
    sop_steps           JSONB           NOT NULL DEFAULT '[]'::jsonb,
    safety_redline      TEXT,
    standard            VARCHAR(64),
    level               VARCHAR(16)     NOT NULL,
    reason              VARCHAR(120),

    -- 模型上下文（debug / 审计）
    top_feature         VARCHAR(48),
    top_feature_label   VARCHAR(48),
    shap_score          REAL,
    current_vocs        REAL,
    model_name          VARCHAR(64)     DEFAULT 'deepseek-chat',
    confidence          REAL,

    -- 审计
    generated_by        VARCHAR(64)     NOT NULL DEFAULT 'admin-rag',
    generated_at        TIMESTAMPTZ     NOT NULL DEFAULT now(),
    is_current          BOOLEAN         NOT NULL DEFAULT TRUE,

    UNIQUE (alert_id, version)
);

CREATE INDEX IF NOT EXISTS idx_rag_plans_alert_current
    ON public.wg_alert_rag_plans(alert_id) WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_rag_plans_generated_at
    ON public.wg_alert_rag_plans(generated_at DESC);

COMMENT ON TABLE  public.wg_alert_rag_plans IS '告警 RAG 处置方案（管理端生成，所有端共享）';
COMMENT ON COLUMN public.wg_alert_rag_plans.is_current IS '同 alert 多版本时仅一条为 true，便于一线端单条查询';
COMMENT ON COLUMN public.wg_alert_rag_plans.sop_steps IS 'JSONB 数组，每项为字符串步骤';

"""wg_alert_rag_plans 表的 CRUD。

管理端在生成 RAG 处置方案后调用 upsert_plan() 写入；
读取走 get_current_plan() 拿到该告警最新一条 plan（is_current=true）。

历史版本不删除——同 alert 多次重新生成会 version 递增，旧版置 is_current=false，
便于事后审计"上一版方案是不是被覆盖了"。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from services.db import cursor


PLAN_COLUMNS: List[str] = [
    "id",
    "alert_id",
    "version",
    "title",
    "suggestion_short",
    "sop_steps",
    "safety_redline",
    "standard",
    "level",
    "reason",
    "top_feature",
    "top_feature_label",
    "shap_score",
    "current_vocs",
    "model_name",
    "confidence",
    "generated_by",
    "generated_at",
    "is_current",
]


def _row_to_dict(row: Optional[tuple]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {col: row[idx] for idx, col in enumerate(PLAN_COLUMNS)}


def get_current_plan(alert_id: int) -> Optional[Dict[str, Any]]:
    """读最新一版方案；找不到返回 None。"""
    sql = (
        f"SELECT {', '.join(PLAN_COLUMNS)} "
        f"FROM public.wg_alert_rag_plans "
        f"WHERE alert_id = %s AND is_current = TRUE "
        f"LIMIT 1"
    )
    with cursor() as cur:
        cur.execute(sql, (alert_id,))
        return _row_to_dict(cur.fetchone())


def list_plans(alert_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """按 version 倒序返回历史方案。"""
    sql = (
        f"SELECT {', '.join(PLAN_COLUMNS)} "
        f"FROM public.wg_alert_rag_plans "
        f"WHERE alert_id = %s "
        f"ORDER BY version DESC "
        f"LIMIT %s"
    )
    with cursor() as cur:
        cur.execute(sql, (alert_id, limit))
        return [_row_to_dict(r) for r in cur.fetchall()]  # type: ignore[misc]


def upsert_plan(
    alert_id: int,
    rag_card: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    generated_by: str = "admin-rag",
) -> Dict[str, Any]:
    """插入新版本方案，旧版置 is_current=false。

    Args:
        alert_id   : wg_alerts.id
        rag_card   : rag_service.get_warning_diagnose() 的返回值
                     必备：title / suggestion_short / sop_steps / level
                     可选：safety_redline / standard / reason
        context    : 模型上下文（top_feature / shap_score / current_vocs / model_name / confidence）
        generated_by: 'admin-rag' 或登录用户名

    Returns:
        新插入的整行（dict）
    """
    ctx = context or {}

    with cursor() as cur:
        # 1) 计算下一个 version
        cur.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 "
            "FROM public.wg_alert_rag_plans WHERE alert_id = %s",
            (alert_id,),
        )
        next_version = cur.fetchone()[0]

        # 2) 旧版置 is_current=false
        cur.execute(
            "UPDATE public.wg_alert_rag_plans "
            "SET is_current = FALSE "
            "WHERE alert_id = %s AND is_current = TRUE",
            (alert_id,),
        )

        # 3) 插入新版本
        cur.execute(
            f"""
            INSERT INTO public.wg_alert_rag_plans
                (alert_id, version, title, suggestion_short, sop_steps,
                 safety_redline, standard, level, reason,
                 top_feature, top_feature_label, shap_score, current_vocs,
                 model_name, confidence, generated_by, is_current)
            VALUES
                (%s, %s, %s, %s, %s::jsonb,
                 %s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s, %s, TRUE)
            RETURNING {', '.join(PLAN_COLUMNS)}
            """,
            (
                alert_id,
                next_version,
                str(rag_card.get("title", ""))[:120],
                str(rag_card.get("suggestion_short", "")),
                json.dumps(rag_card.get("sop_steps", []), ensure_ascii=False),
                rag_card.get("safety_redline"),
                rag_card.get("standard"),
                str(rag_card.get("level", "warning"))[:16],
                str(rag_card.get("reason") or "")[:120] or None,
                str(ctx.get("top_feature") or "")[:48] or None,
                str(ctx.get("top_feature_label") or "")[:48] or None,
                ctx.get("shap_score"),
                ctx.get("current_vocs"),
                str(ctx.get("model_name") or "deepseek-chat")[:64],
                ctx.get("confidence"),
                str(generated_by)[:64],
            ),
        )
        row = cur.fetchone()

    plan = _row_to_dict(row)
    assert plan is not None
    return plan


def delete_plans_for_alert(alert_id: int) -> int:
    """硬删除某告警下所有方案；返回删除行数。慎用——通常 ON DELETE CASCADE 会自动处理。"""
    with cursor() as cur:
        cur.execute(
            "DELETE FROM public.wg_alert_rag_plans WHERE alert_id = %s",
            (alert_id,),
        )
        return cur.rowcount


def parse_alert_id(alert_id: str) -> Optional[int]:
    """工具函数：把诊断接口收到的 alert_id 转成 int。
    本地 fallback 告警 (LOCAL-FALLBACK-xxx / WATCHDOG-xxx) 不在 wg_alerts 表里，返回 None。
    """
    try:
        return int(alert_id)
    except (TypeError, ValueError):
        return None

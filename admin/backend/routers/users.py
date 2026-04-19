from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from routers.auth import get_current_user


router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


class UserItem(BaseModel):
    id: int
    username: str
    display_name: str
    role_code: str
    role_name: str
    status: str
    created_at: str
    last_login_at: str


class UserCreatePayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str = Field(min_length=2, max_length=32)
    role_code: str
    status: str
    password: str = Field(min_length=6, max_length=32)


class UserUpdatePayload(BaseModel):
    display_name: str = Field(min_length=2, max_length=32)
    role_code: str
    status: str


ROLE_NAME_MAP = {
    "SysAdmin": "超级管理员",
    "EnvAdmin": "环保监测员",
    "Analyst": "数据分析师",
    "Operator": "现场处置工",
}


USERS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "username": "admin_user",
        "display_name": "超级管理员",
        "role_code": "SysAdmin",
        "role_name": ROLE_NAME_MAP["SysAdmin"],
        "status": "enabled",
        "created_at": "2024-01-01 10:00",
        "last_login_at": "2026-04-13 09:30",
    },
    {
        "id": 2,
        "username": "env_monitor",
        "display_name": "环保监测员",
        "role_code": "EnvAdmin",
        "role_name": ROLE_NAME_MAP["EnvAdmin"],
        "status": "enabled",
        "created_at": "2024-02-15 08:00",
        "last_login_at": "2026-04-13 09:00",
    },
    {
        "id": 3,
        "username": "data_analyst_01",
        "display_name": "数据分析师",
        "role_code": "Analyst",
        "role_name": ROLE_NAME_MAP["Analyst"],
        "status": "disabled",
        "created_at": "2025-06-20 11:30",
        "last_login_at": "2026-04-10 16:45",
    },
    {
        "id": 4,
        "username": "worker_05",
        "display_name": "现场处置工",
        "role_code": "Operator",
        "role_name": ROLE_NAME_MAP["Operator"],
        "status": "enabled",
        "created_at": "2026-03-01 14:00",
        "last_login_at": "2026-04-12 17:15",
    },
]


def _find_user(user_id: int) -> Optional[Dict[str, Any]]:
    for item in USERS:
        if item["id"] == user_id:
            return item
    return None


@router.get("")
async def list_users(
    keyword: str = "",
    role_codes: str = Query(default=""),
    status: str = "",
) -> Dict[str, Any]:
    role_set = {item.strip() for item in role_codes.split(",") if item.strip()}
    keyword_lower = keyword.strip().lower()

    items = []
    for user in USERS:
        if role_set and user["role_code"] not in role_set:
            continue
        if status and user["status"] != status:
            continue
        searchable = f"{user['username']} {user['display_name']} {user['role_code']}".lower()
        if keyword_lower and keyword_lower not in searchable:
            continue
        items.append(user)

    return {
        "items": items,
        "total": len(items),
        "roles": [{"code": code, "name": name} for code, name in ROLE_NAME_MAP.items()],
    }


@router.get("/{user_id}")
async def get_user_detail(user_id: int) -> Dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "item": user,
        "permissions": {
            "menus": {
                "SysAdmin": ["大屏", "监测", "预测", "告警", "模型", "用户", "日志", "部署"],
                "EnvAdmin": ["大屏", "监测", "预测", "告警", "闭环", "报表"],
                "Analyst": ["监测历史", "数据治理", "模型评估", "复盘"],
                "Operator": ["职工端联动", "任务回填"],
            }.get(user["role_code"], []),
        },
    }


@router.post("")
async def create_user(payload: UserCreatePayload) -> Dict[str, Any]:
    if any(item["username"] == payload.username for item in USERS):
        raise HTTPException(status_code=409, detail="用户名已存在")

    user_id = max((item["id"] for item in USERS), default=0) + 1
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
    user = {
        "id": user_id,
        "username": payload.username,
        "display_name": payload.display_name,
        "role_code": payload.role_code,
        "role_name": ROLE_NAME_MAP.get(payload.role_code, payload.role_code),
        "status": payload.status,
        "created_at": now_text,
        "last_login_at": "--",
    }
    USERS.insert(0, user)
    return {"item": user}


@router.put("/{user_id}")
async def update_user(user_id: int, payload: UserUpdatePayload) -> Dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user["display_name"] = payload.display_name
    user["role_code"] = payload.role_code
    user["role_name"] = ROLE_NAME_MAP.get(payload.role_code, payload.role_code)
    user["status"] = payload.status
    return {"item": user}


@router.post("/{user_id}/reset-password")
async def reset_password(user_id: int) -> Dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "success": True,
        "message": f"已为 {user['display_name']} 重置密码，初始密码为 Reset@123",
    }


@router.post("/{user_id}/toggle-status")
async def toggle_status(user_id: int) -> Dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user["status"] = "disabled" if user["status"] == "enabled" else "enabled"
    return {"item": user}

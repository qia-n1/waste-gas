"""测试账号 zsq / 12345678：幂等补齐用户、负责区域、设备、排口、读数、告警及 zsq 名下巡检/处置/通知/对话。"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.entities import (
    AiConversation,
    Alert,
    AlertRecord,
    AreaSourcePoint,
    AreaZone,
    DeviceInfo,
    DisposalRecord,
    InspectionRecord,
    NotificationMessage,
    SensorReading,
    UserProfile,
)

ZSQ = 'zsq'
# 与 admin FactoryScene「喷涂生产厂房」及 init_db 区域名一致（涂装产线在该厂房内）
COATING_AREA = '喷涂生产厂房'
COATING_DEVICE_ID = 'DEV-COAT-001'
COATING_METRICS: list[tuple[str, str, str, float, float, float]] = [
    ('coating_flow', '涂装风量', 'm3/h', 1200.0, 980.0, 1120.0),
    ('coating_conc', '涂装浓度', 'mg/m3', 45.0, 36.0, 58.0),
    ('coating_temp', '涂装温度', '℃', 42.0, 35.0, 39.0),
    ('coating_pressure', '涂装压力', 'Pa', 150.0, 110.0, 126.0),
]


async def ensure_zsq_test_data(session: AsyncSession) -> None:
    now = datetime.now().replace(second=0, microsecond=0)

    profile = await session.scalar(select(UserProfile).where(UserProfile.username == ZSQ).limit(1))
    pwd = hash_password('12345678')
    if profile:
        profile.password_hash = pwd
        profile.name = profile.name or '赵双庆'
        profile.email = profile.email or 'zsq@plant.example.com'
        profile.phone = profile.phone or '13900001234'
        profile.department = profile.department or 'EHS 与运行班'
        profile.role = profile.role or '一线运维'
    else:
        session.add(
            UserProfile(
                username=ZSQ,
                password_hash=pwd,
                role='一线运维',
                name='赵双庆',
                email='zsq@plant.example.com',
                phone='13900001234',
                department='EHS 与运行班',
                join_date=date(2024, 6, 1),
            )
        )
    await session.flush()

    await _migrate_zsq_legacy_coating_area(session)

    # 已存在库里的演示告警若仍为「处理中」，升级为「持续跟踪」以匹配 48h 结案规则
    rto_alert = await session.scalar(select(Alert).where(Alert.title == 'RTO 入口温度短时上升').limit(1))
    if rto_alert and rto_alert.status == 'accepted':
        rto_alert.status = 'tracking'
        rto_alert.handled_at = now - timedelta(hours=50)

    zone_specs = [{'name': COATING_AREA, 'device_count': 4, 'online_rate': 99.4, 'alert_count': 2, 'avg_vocs': 22.6}]
    for z in zone_specs:
        exists = await session.scalar(select(AreaZone.id).where(AreaZone.name == z['name']).limit(1))
        if not exists:
            session.add(AreaZone(manager_username=ZSQ, **z))

    for dev in (
        (COATING_DEVICE_ID, '喷涂线总排监测柜', '192.168.1.121', COATING_AREA),
    ):
        did, dname, ip, loc = dev
        if not await session.scalar(select(DeviceInfo.id).where(DeviceInfo.device_id == did).limit(1)):
            session.add(
                DeviceInfo(
                    device_id=did,
                    device_name=dname,
                    status='在线',
                    last_online=now - timedelta(minutes=3),
                    ip_address=ip,
                    firmware_version='v2.1.4',
                    location=loc,
                )
            )

    point_specs = [
        (COATING_AREA, 'coating_flow', 20.0, 30.0, 1120.0, '正常', 'low', 'stable', COATING_DEVICE_ID),
        (COATING_AREA, 'coating_conc', 42.0, 30.0, 58.0, '预警', 'medium', 'up', COATING_DEVICE_ID),
        (COATING_AREA, 'coating_temp', 64.0, 30.0, 39.0, '正常', 'low', 'stable', COATING_DEVICE_ID),
        (COATING_AREA, 'coating_pressure', 84.0, 30.0, 126.0, '告警', 'high', 'up', COATING_DEVICE_ID),
    ]
    for pname, src, x, y, conc, st, lv, tr, did in point_specs:
        exists = await session.scalar(
            select(AreaSourcePoint.id).where(AreaSourcePoint.area_name == pname, AreaSourcePoint.source_name == src).limit(1)
        )
        if not exists:
            session.add(
                AreaSourcePoint(
                    area_name=pname,
                    source_name=src,
                    x=x,
                    y=y,
                    concentration=conc,
                    status=st,
                    level=lv,
                    trend=tr,
                    device_id=did,
                )
            )

    for did, base_v in ((COATING_DEVICE_ID, 24.0),):
        cnt = await session.scalar(select(func.count()).select_from(SensorReading).where(SensorReading.device_id == did))
        if (cnt or 0) >= 24:
            continue
        batch: list[SensorReading] = []
        for i in range(48):
            ts = now - timedelta(hours=47 - i)
            wave = (i % 9) * 2.1 + (i % 4) * 1.3
            batch.append(
                SensorReading(
                    device_id=did,
                    recorded_at=ts,
                    vocs=round(max(6.0, base_v + wave - 8 + (i % 5)), 2),
                    temperature=round(23.0 + (i % 6) * 1.4, 2),
                    humidity=round(40 + (i % 7) * 4.2, 2),
                    pressure=round(100.0 + (i % 5) * 0.35, 2),
                )
            )
        session.add_all(batch)

    alert_blueprints: list[dict] = [
        {
            'title': 'RTO 入口温度短时上升',
            'description': 'RTO 入口烟气温度由 118℃ 升至 132℃，超过班组设定观察阈值 128℃，持续约 6 分钟；炉膛负压与助燃风流量同步波动，疑似阀门开度漂移。',
            'level': 'medium',
            'status': 'tracking',
            'created_at': now - timedelta(hours=18),
            'handled_at': now - timedelta(hours=50),
            'resolved_at': None,
            'device_id': 'DEV-002',
            'location': 'C 区 RTO 岛',
            'alert_type': '温度异常',
            'metric_label': 'RTO 入口温度',
            'current_value': 132.0,
            'unit': '℃',
            'threshold_value': 128.0,
            'records': [
                (now - timedelta(hours=18), '在线监测判定短时越限，已推送运行班', '系统'),
                (now - timedelta(hours=17, minutes=40), '已接单，正在核对阀门开度与热电偶冗余', ZSQ),
                (now - timedelta(hours=50), '提交处置：阀门与热电偶已复核，进入 48 小时持续跟踪', ZSQ),
            ],
        },
        {
            'title': '沸石转轮压差升高预警',
            'description': '转轮前后压差由 820 Pa 升至 1180 Pa，接近清洗维护建议值 1200 Pa；脱附出口 VOCs 同步抬升，存在局部堵塞或结焦风险。',
            'level': 'medium',
            'status': 'unresolved',
            'created_at': now - timedelta(hours=5),
            'resolved_at': None,
            'device_id': 'DEV-002',
            'location': 'C 区 RTO 岛',
            'alert_type': '压差异常',
            'metric_label': '转轮压差',
            'current_value': 1180.0,
            'unit': 'Pa',
            'threshold_value': 1200.0,
            'records': [(now - timedelta(hours=5), '压差超趋势阈值，触发预警', '系统')],
        },
        {
            'title': '喷淋塔循环泵流量偏低',
            'description': '洗涤塔循环泵出口流量计读数 18.6 m³/h，低于设计低限 22 m³/h，塔顶除雾层可能存在轻微堵塞或泵叶轮磨损。',
            'level': 'low',
            'status': 'resolved',
            'created_at': now - timedelta(days=2, hours=4),
            'handled_at': now - timedelta(days=4, hours=5),
            'resolved_at': now - timedelta(days=2, hours=1),
            'device_id': 'DEV-001',
            'location': '废气处理车间 A',
            'alert_type': '流量异常',
            'metric_label': '循环泵出口流量',
            'current_value': 18.6,
            'unit': 'm3/h',
            'threshold_value': 22.0,
            'records': [
                (now - timedelta(days=2, hours=4), '流量计低限报警', '系统'),
                (now - timedelta(days=2, hours=2), '清洗喷头与过滤器后流量恢复至 24.1 m³/h', ZSQ),
                (now - timedelta(days=2, hours=1), '跟踪期满，告警已结案', ZSQ),
            ],
        },
        {
            'title': '活性炭吸附箱出口浓度爬升',
            'description': '二级活性炭箱出口 VOCs 由 12 mg/m³ 升至 38 mg/m³，一级箱出口仍正常，判断一级吸附趋近穿透，需安排更换或再生。',
            'level': 'high',
            'status': 'accepted',
            'created_at': now - timedelta(hours=30),
            'resolved_at': None,
            'device_id': 'DEV-001',
            'location': '废气处理车间 A',
            'alert_type': '浓度超标',
            'metric_label': '出口 VOCs',
            'current_value': 38.0,
            'unit': 'mg/m3',
            'threshold_value': 30.0,
            'records': [
                (now - timedelta(hours=30), '出口浓度超二级管控值', '系统'),
                (now - timedelta(hours=29), '已接单，已取样送检并申请夜间更换炭箱', ZSQ),
            ],
        },
        {
            'title': '在线监测仪通信短时中断',
            'description': '数采与工控链路中断 3 分 12 秒，期间无有效分钟数据上传至监管平台，已记录为设备侧交换机端口闪断。',
            'level': 'low',
            'status': 'resolved',
            'created_at': now - timedelta(days=5, hours=2),
            'handled_at': now - timedelta(days=7, hours=5),
            'resolved_at': now - timedelta(days=5, hours=1),
            'device_id': 'DEV-004',
            'location': 'E 区污水站加盖',
            'alert_type': '通信异常',
            'metric_label': '数据有效率',
            'current_value': 0.0,
            'unit': '%',
            'threshold_value': 95.0,
            'records': [
                (now - timedelta(days=5, hours=2), '链路中断告警', '系统'),
                (now - timedelta(days=5, hours=1, minutes=40), '更换交换机端口并绑定固定速率，链路稳定', ZSQ),
                (now - timedelta(days=5, hours=1), '跟踪期满，告警已结案', ZSQ),
            ],
        },
        {
            'title': '应急切断阀联锁自检异常',
            'description': '月度联锁自检中，罐根切断阀 B 反馈信号与现场行程开关不一致，DCS 显示全关但现场为半开，联锁逻辑已切至安全侧并保持停机建议。',
            'level': 'high',
            'status': 'unresolved',
            'created_at': now - timedelta(hours=8),
            'resolved_at': None,
            'device_id': 'DEV-003',
            'location': 'D 区罐区尾气',
            'alert_type': '联锁异常',
            'metric_label': '阀位回讯一致性',
            'current_value': 0.0,
            'unit': '-',
            'threshold_value': 1.0,
            'records': [(now - timedelta(hours=8), '联锁自检失败，已禁止自动复位', '系统')],
        },
        {
            'title': '厂界 VOCs 小时均值逼近限值',
            'description': '主导上风向时段，厂界下风向点位小时均值 0.38 mg/m³，接近地方管控参考 0.40 mg/m³；同步检查装置与装卸作业台账。',
            'level': 'medium',
            'status': 'accepted',
            'created_at': now - timedelta(hours=40),
            'resolved_at': None,
            'device_id': 'DEV-004',
            'location': '厂界东南角',
            'alert_type': '厂界浓度',
            'metric_label': '厂界 VOCs',
            'current_value': 0.38,
            'unit': 'mg/m3',
            'threshold_value': 0.40,
            'records': [
                (now - timedelta(hours=40), '气象站与厂界站联合触发提醒', '系统'),
                (now - timedelta(hours=39), '已接单，已暂停非必要装卸并加大喷淋频率', ZSQ),
            ],
        },
        {
            'title': '集气罩负压不足',
            'description': '手工工位集气罩静压由 -120 Pa 降至 -78 Pa，罩口风速低于 0.5 m/s 控制要求，存在无组织逸散风险。',
            'level': 'medium',
            'status': 'resolved',
            'created_at': now - timedelta(days=1, hours=6),
            'handled_at': now - timedelta(days=3, hours=7),
            'resolved_at': now - timedelta(days=1, hours=3),
            'device_id': 'DEV-001',
            'location': '废气处理车间 A',
            'alert_type': '负压异常',
            'metric_label': '罩口静压',
            'current_value': -78.0,
            'unit': 'Pa',
            'threshold_value': -100.0,
            'records': [
                (now - timedelta(days=1, hours=6), '罩口风速不足预警', '系统'),
                (now - timedelta(days=1, hours=4), '调整风阀开度并清理软管积灰，负压恢复至 -118 Pa', ZSQ),
                (now - timedelta(days=1, hours=3), '跟踪期满，告警已结案', ZSQ),
            ],
        },
        {
            'title': '脱附风机轴承温升过快',
            'description': '脱附风机驱动端轴承温度 10 分钟内由 56℃ 升至 71℃，振动速度有效值同步上升，已按预案降负荷观察。',
            'level': 'medium',
            'status': 'resolved',
            'created_at': now - timedelta(days=3, hours=10),
            'handled_at': now - timedelta(days=5, hours=11),
            'resolved_at': now - timedelta(days=3, hours=7),
            'device_id': 'DEV-002',
            'location': 'C 区 RTO 岛',
            'alert_type': '设备温升',
            'metric_label': '轴承温度',
            'current_value': 71.0,
            'unit': '℃',
            'threshold_value': 75.0,
            'records': [
                (now - timedelta(days=3, hours=10), '温升速率触发预警', '系统'),
                (now - timedelta(days=3, hours=8), '润滑补充与振动复测正常，择机更换轴承备件', ZSQ),
                (now - timedelta(days=3, hours=7), '跟踪期满，告警已结案', ZSQ),
            ],
        },
        {
            'title': '碱洗段 pH 偏低',
            'description': '碱洗循环槽 pH 6.9，低于运行卡控 8.0，可能影响酸性气体吸收效率，已安排加药并复核流量计标定。',
            'level': 'low',
            'status': 'resolved',
            'created_at': now - timedelta(days=5, hours=2),
            'handled_at': now - timedelta(days=4, hours=6),
            'resolved_at': now - timedelta(days=2, hours=4),
            'device_id': 'DEV-001',
            'location': '废气处理车间 A',
            'alert_type': '吸收异常',
            'metric_label': '碱洗 pH',
            'current_value': 6.9,
            'unit': '-',
            'threshold_value': 8.0,
            'records': [
                (now - timedelta(days=5, hours=2), 'pH 低限报警', '系统'),
                (now - timedelta(days=4, hours=6), '按量投加碱液并搅拌 15 分钟后 pH 恢复至 8.4', ZSQ),
                (now - timedelta(days=2, hours=4), '跟踪期满，告警已结案', ZSQ),
            ],
        },
    ]

    title_to_id: dict[str, int] = {}
    for bp in alert_blueprints:
        title = bp['title']
        tid = await session.scalar(select(Alert.id).where(Alert.title == title).limit(1))
        if tid:
            title_to_id[title] = tid
            continue
        recs: list[tuple[datetime, str, str]] = bp['records']
        fields = {k: v for k, v in bp.items() if k != 'records'}
        alert = Alert(**fields)
        session.add(alert)
        await session.flush()
        title_to_id[title] = alert.id
        for t, content, op in recs:
            session.add(
                AlertRecord(
                    alert_id=alert.id,
                    time=t,
                    content=content[:256],
                    operator=op[:64],
                )
            )

    # —— 在「待接单」告警详情页下预置一组“方案下追问”的对话，方便测试 —— #
    pressure_id = title_to_id.get('涂装压力偏高预警') or await session.scalar(
        select(Alert.id).where(Alert.title == '涂装压力偏高预警').limit(1)
    )
    if pressure_id:
        sid = f'alert-{pressure_id}'
        demo_pairs: list[tuple[str, str, datetime]] = [
            (
                'user',
                '压差升高如何快速判断是取压管堵塞还是转轮本体堵塞？',
                now - timedelta(hours=1, minutes=20),
            ),
            (
                'assistant',
                '先看取压：对比就地 U 型压差计/备用变送器，检查取压管是否积水、冷凝液是否堵塞；若取压恢复后压差仍高，再检查过滤器/转轮通道是否结焦或灰堵，并结合脱附出口 VOCs 是否同步抬升判断是否本体阻塞。',
                now - timedelta(hours=1, minutes=19),
            ),
            (
                'user',
                '现场留痕需要哪些证据？',
                now - timedelta(hours=1, minutes=10),
            ),
            (
                'assistant',
                '建议至少包含：告警截图与趋势、关键参数（压差/温度/风机电流）、取压管/过滤器现场照片、处置前后对比读数、参与人员与时间点。若有清洗/更换作业，还需补充作业票与验收记录。',
                now - timedelta(hours=1, minutes=9),
            ),
            (
                'user',
                '如果 30 分钟后压差仍高于 1100Pa，下一步先做什么？',
                now - timedelta(hours=1, minutes=5),
            ),
            (
                'assistant',
                '建议先执行降负荷并切到保守工况，随后按“取压回路复核 -> 过滤段检查 -> 转轮通道检查”的顺序排障，同时每 10 分钟记录一次压差、脱附温度和出口 VOCs 作为跟踪证据。',
                now - timedelta(hours=1, minutes=4),
            ),
            (
                'user',
                '这条告警需要通知哪些岗位一起到场？',
                now - timedelta(hours=1, minutes=2),
            ),
            (
                'assistant',
                '至少通知运行主操、仪控值班和工艺工程师；若涉及动火/受限空间风险，再同步 EHS 与检维修负责人，避免单岗处置导致证据缺失或误操作。',
                now - timedelta(hours=1, minutes=1),
            ),
        ]
        for role, content, created in demo_pairs:
            exists = await session.scalar(
                select(AiConversation.id)
                .where(
                    AiConversation.username == ZSQ,
                    AiConversation.session_id == sid,
                    AiConversation.role == role,
                    AiConversation.content == content,
                )
                .limit(1)
            )
            if exists:
                continue
            session.add(AiConversation(username=ZSQ, session_id=sid, role=role, content=content, created_at=created))

    # 第二条待接单告警也补一组问答，便于切换不同告警测试方案问答
    interlock_id = title_to_id.get('涂装浓度持续超阈值') or await session.scalar(
        select(Alert.id).where(Alert.title == '涂装浓度持续超阈值').limit(1)
    )
    if interlock_id:
        sid = f'alert-{interlock_id}'
        interlock_pairs: list[tuple[str, str, datetime]] = [
            (
                'user',
                '联锁阀反馈不一致时，第一现场动作应该是什么？',
                now - timedelta(minutes=55),
            ),
            (
                'assistant',
                '先确认联锁已切入安全侧并暂停相关装卸/输送，再现场复核阀位与 DCS 反馈是否一致；未经审批不要强制旁路，先保安全再定位。',
                now - timedelta(minutes=54),
            ),
            (
                'user',
                '需要补采哪些数据，便于后续复盘？',
                now - timedelta(minutes=50),
            ),
            (
                'assistant',
                '建议补采：联锁触发时间线、阀位回讯原始点表、现场阀位照片/视频、相关压力与流量趋势，以及参与人员与操作指令记录。',
                now - timedelta(minutes=49),
            ),
        ]
        for role, content, created in interlock_pairs:
            exists = await session.scalar(
                select(AiConversation.id)
                .where(
                    AiConversation.username == ZSQ,
                    AiConversation.session_id == sid,
                    AiConversation.role == role,
                    AiConversation.content == content,
                )
                .limit(1)
            )
            if exists:
                continue
            session.add(AiConversation(username=ZSQ, session_id=sid, role=role, content=content, created_at=created))

    disposal_specs: list[tuple[str, str, str, str, str, datetime]] = [
            ('涂装温度短时上升', '温度曲线已回稳', '已复核烘道风门和循环风机运行参数，温度恢复在控制带内。', '已提交', '处置闭环', now - timedelta(hours=50)),
            ('涂装压力偏高预警', '排风支路已疏通', '清理过滤段积灰并复测压差，连续 30 分钟下降到目标区间。', '已提交', '处置闭环', now - timedelta(hours=4)),
            ('涂装浓度持续超阈值', '喷涂工位已降负荷', '压减喷涂节拍并加大风量，浓度峰值明显下降。', '已提交', '处置闭环', now - timedelta(hours=8)),
    ]
    for title, result, notes, st, act, created in disposal_specs:
        rshort = result[:64]
        exists_d = await session.scalar(
            select(DisposalRecord.id).where(DisposalRecord.username == ZSQ, DisposalRecord.result == rshort).limit(1)
        )
        if exists_d:
            continue
        aid = title_to_id.get(title) or await session.scalar(select(Alert.id).where(Alert.title == title).limit(1))
        if not aid:
            continue
        session.add(
            DisposalRecord(
                alert_id=aid,
                username=ZSQ,
                result=rshort,
                notes=notes,
                photo_url='',
                status=st,
                action_type=act,
                created_at=created,
            )
        )

    inspections: list[tuple[str, str, datetime]] = [
            (
                COATING_AREA,
                '白班巡检：coating_flow 稳定在 1100~1180 m3/h，coating_conc 峰值较昨日下降，工位排风运行正常。',
                now - timedelta(hours=2),
            ),
            (
                COATING_AREA,
                '检查涂装线循环风机与过滤段：coating_pressure 回落至 124 Pa，暂无突跳点。',
                now - timedelta(hours=9),
            ),
            (
                COATING_AREA,
                '夜班复核：coating_temp 维持在 37~40℃，烘道与排风联动响应正常。',
                now - timedelta(days=1, hours=4),
            ),
    ]
    for area, summary, created in inspections:
        summ = summary[:255]
        exists_i = await session.scalar(
            select(InspectionRecord.id).where(InspectionRecord.username == ZSQ, InspectionRecord.summary == summ).limit(1)
        )
        if exists_i:
            continue
        session.add(InspectionRecord(username=ZSQ, area_name=area, summary=summ, created_at=created))

    notifs: list[tuple[str, str, str, str, bool, datetime, int | None]] = [
            ('沸石转轮清洗窗口提醒', '清洗窗口已锁定为今晚 23:00-次日 05:00，请确认能源隔离与动火票。', '系统', 'low', False, now - timedelta(hours=1), None),
            ('厂界浓度联合提醒', '东南风 3.2m/s，请保持装卸压减措施至明日 08:00。', '告警', 'medium', False, now - timedelta(hours=6), None),
            ('联锁阀排查进度', '仪控班组预计 18:00 前完成回讯更换，请现场监护人到岗签字。', '系统', 'high', False, now - timedelta(hours=3), None),
            ('活性炭更换吊装', '吊装方案已批准，请携带 PPE 清单与对讲机频道表。', '系统', 'medium', True, now - timedelta(hours=20), None),
            ('培训签到', '本周四 14:00 VOCs 在线比对实操培训，会议室 B203。', '系统', 'low', True, now - timedelta(days=1), None),
            ('月度排放执行报告', '请在本月 25 日前完成数据校核与附件上传。', '系统', 'low', True, now - timedelta(days=2), None),
            ('巡检计划', '明日白班增加 D 区罐区二次复核（联锁异常跟进）。', '系统', 'medium', False, now - timedelta(hours=12), None),
            ('备件到货', '切断阀回讯开关型号 RV-220 已入库，货架 A-12。', '系统', 'low', True, now - timedelta(hours=7), None),
            ('气象预警', '傍晚可能有短时雷雨，请检查加盖站配电柜防潮封条。', '系统', 'low', True, now - timedelta(hours=10), None),
            ('比对抽气备案', '监管平台已收到比对计划备案回执。', '系统', 'low', True, now - timedelta(days=3), None),
            ('交接班提示', '夜班已记录转轮压差趋势，请白班关注脱附温度曲线。', '系统', 'low', False, now - timedelta(hours=14), None),
            ('安全观察卡', '上周安全观察卡闭环率 96%，感谢提交。', '系统', 'low', True, now - timedelta(days=4), None),
    ]
    for title, content, cat, level, is_read, created, alert_id in notifs:
        t = title[:128]
        exists_n = await session.scalar(
            select(NotificationMessage.id).where(NotificationMessage.username == ZSQ, NotificationMessage.title == t).limit(1)
        )
        if exists_n:
            continue
        session.add(
            NotificationMessage(
                username=ZSQ,
                title=t,
                content=content,
                category=cat,
                level=level,
                is_read=is_read,
                created_at=created,
                alert_id=alert_id,
            )
        )

    sid = 'field-zsq'
    pairs: list[tuple[str, str, datetime]] = [
            (
                'user',
                'C 区沸石转轮压差升高时，优先检查哪些点位？',
                now - timedelta(hours=11),
            ),
            (
                'assistant',
                '建议优先核对：转轮前后静压取样管是否积水、脱附风机出口温度是否异常抬升、再生风阀实际开度与 DCS 反馈是否一致，并查看近 24h 压差与出口浓度是否同向波动。',
                now - timedelta(hours=11, minutes=1),
            ),
            (
                'user',
                'RTO 入口温度短时上冲，现场如何快速判断是否阀门问题？',
                now - timedelta(hours=19),
            ),
            (
                'assistant',
                '可先比对就地阀位指示与 DCS 反馈，观察助燃风流量与炉膛负压是否同步异常；若温度上升而烟气氧量下降，更指向配风问题；同时核对热电偶冗余通道是否一致。',
                now - timedelta(hours=19, minutes=1),
            ),
            (
                'user',
                '罐区联锁阀回讯不一致，停机前要做哪些确认？',
                now - timedelta(hours=7),
            ),
            (
                'assistant',
                '确认联锁已切安全侧、相关装车作业已停止、油气回收管路压力释放路径畅通，并与仪控共同验证现场阀位与 DCS 显示，禁止强制旁路除非有书面授权与专人监护。',
                now - timedelta(hours=7, minutes=1),
            ),
            (
                'user',
                '厂界 VOCs 逼近限值时，运行侧有哪些可立即执行的措施？',
                now - timedelta(hours=41),
            ),
            (
                'assistant',
                '可立即压减非必要装卸、检查敞开液面加盖密封、提高洗涤/喷淋强度、核查高浓度工序是否错峰，并同步记录气象与源强变化便于后续溯源。',
                now - timedelta(hours=41, minutes=1),
            ),
    ]
    for role, content, created in pairs:
        exists_a = await session.scalar(
            select(AiConversation.id)
            .where(AiConversation.username == ZSQ, AiConversation.session_id == sid, AiConversation.role == role, AiConversation.content == content)
            .limit(1)
        )
        if exists_a:
            continue
        session.add(AiConversation(username=ZSQ, session_id=sid, role=role, content=content, created_at=created))

    await _normalize_zsq_scope(session, now)
    await _align_resolved_alerts_with_disposal(session)
    await session.commit()


async def _migrate_zsq_legacy_coating_area(session: AsyncSession) -> None:
    """历史种子用「涂装车间」作区域名，与 admin 地图「喷涂生产厂房」不一致；幂等迁移并合并重复区域。"""
    await session.execute(
        update(AreaSourcePoint).where(AreaSourcePoint.area_name == '涂装车间').values(area_name=COATING_AREA)
    )
    await session.execute(
        update(DeviceInfo).where(DeviceInfo.location == '涂装车间').values(location=COATING_AREA)
    )
    legacy = await session.scalar(
        select(AreaZone).where(AreaZone.manager_username == ZSQ, AreaZone.name == '涂装车间').limit(1)
    )
    if legacy is None:
        return
    # 区域名全局唯一：若已存在「喷涂生产厂房」（任意负责人），不能对 legacy 再改名，只能合并行
    modern = await session.scalar(select(AreaZone).where(AreaZone.name == COATING_AREA).limit(1))
    if modern is not None and modern.id != legacy.id:
        modern.manager_username = ZSQ
        await session.delete(legacy)
    else:
        legacy.name = COATING_AREA


async def _normalize_zsq_scope(session: AsyncSession, now: datetime) -> None:
    """将 zsq 相关展示数据统一到喷涂生产厂房（内含涂装）上下文。"""
    metric_cycle = COATING_METRICS
    alerts = (await session.scalars(select(Alert).order_by(Alert.created_at.asc()))).all()
    for idx, alert in enumerate(alerts):
        metric_key, metric_label, unit, threshold, base_value, cur_value = metric_cycle[idx % len(metric_cycle)]
        alert.device_id = COATING_DEVICE_ID
        alert.location = COATING_AREA
        alert.alert_type = f'{metric_label}异常'
        alert.metric_label = metric_label
        alert.unit = unit
        alert.threshold_value = threshold
        alert.current_value = cur_value + (idx % 3) * 1.2
        if not alert.title.startswith('涂装车间'):
            alert.title = f'涂装车间-{metric_key}-{idx + 1}'
        if '涂装车间' not in alert.description:
            alert.description = (
                f'涂装车间 {metric_label} 出现波动，当前值 {round(alert.current_value, 2)} {unit}，'
                f'阈值 {round(alert.threshold_value, 2)} {unit}，需持续跟踪并留痕。'
            )

    coating_zone = await session.scalar(
        select(AreaZone).where(AreaZone.manager_username == ZSQ, AreaZone.name == COATING_AREA).limit(1)
    )
    if coating_zone is None:
        coating_zone = AreaZone(
            manager_username=ZSQ,
            name=COATING_AREA,
            device_count=4,
            online_rate=99.4,
            alert_count=2,
            avg_vocs=22.6,
        )
        session.add(coating_zone)
    else:
        coating_zone.device_count = 4
        coating_zone.online_rate = 99.4
        coating_zone.alert_count = 2
        coating_zone.avg_vocs = 22.6

    zones = (await session.scalars(select(AreaZone).where(AreaZone.manager_username == ZSQ))).all()
    for zone in zones:
        if zone.id == coating_zone.id:
            continue
        zone.manager_username = 'admin'

    metric_names = {item[0] for item in COATING_METRICS}
    await session.execute(delete(AreaSourcePoint).where(AreaSourcePoint.source_name.not_in(metric_names)))
    points = (await session.scalars(select(AreaSourcePoint).where(AreaSourcePoint.source_name.in_(metric_names)))).all()
    point_index = {item.source_name: item for item in points}
    layout = {
        'coating_flow': (20.0, 30.0, 1120.0, '正常', 'low', 'stable'),
        'coating_conc': (42.0, 30.0, 58.0, '预警', 'medium', 'up'),
        'coating_temp': (64.0, 30.0, 39.0, '正常', 'low', 'stable'),
        'coating_pressure': (84.0, 30.0, 126.0, '告警', 'high', 'up'),
    }
    for name, (x, y, concentration, status, level, trend) in layout.items():
        if name not in point_index:
            session.add(
                AreaSourcePoint(
                    area_name=COATING_AREA,
                    source_name=name,
                    x=x,
                    y=y,
                    concentration=concentration,
                    status=status,
                    level=level,
                    trend=trend,
                    device_id=COATING_DEVICE_ID,
                )
            )
            continue
        point = point_index[name]
        point.area_name = COATING_AREA
        point.device_id = COATING_DEVICE_ID
        point.x = x
        point.y = y
        point.concentration = concentration
        point.status = status
        point.level = level
        point.trend = trend

    inspections = (await session.scalars(select(InspectionRecord).where(InspectionRecord.username == ZSQ))).all()
    for idx, row in enumerate(inspections):
        row.area_name = COATING_AREA
        metric_key, metric_label, unit, _, _, value = metric_cycle[idx % len(metric_cycle)]
        row.summary = (
            f'涂装车间巡检：{metric_key}（{metric_label}）当前 {round(value, 2)} {unit}，'
            f'记录时间 {now.strftime("%Y-%m-%d %H:%M")}，设备联动正常。'
        )[:255]


async def _align_resolved_alerts_with_disposal(session: AsyncSession) -> None:
    """已结案且有关联处置记录：补全 handled_at，并将结案时间推后至满足「处置起算满 48 小时」。"""
    rows = (await session.scalars(select(Alert).where(Alert.status == 'resolved', Alert.resolved_at.isnot(None)))).all()
    for a in rows:
        first_disp = await session.scalar(
            select(DisposalRecord.created_at)
            .where(DisposalRecord.alert_id == a.id)
            .order_by(DisposalRecord.created_at.asc())
            .limit(1)
        )
        if first_disp is None:
            continue
        if a.handled_at is None:
            a.handled_at = first_disp
        earliest = a.handled_at + timedelta(hours=48)
        if a.resolved_at < earliest:
            a.resolved_at = earliest + timedelta(hours=1)

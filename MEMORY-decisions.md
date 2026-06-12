# MEMORY · 决策/日记块（v1.6 拆分后 · 2026-06-09）
_Last updated: 2026-06-12 08:34_

> **加载时机**：复盘、流年应事、Q-A 终审、promoted 内容  
> **不加载**：纯执行任务（招采/cron 推送）  
> **性质**：日记 + 已决策的结论（**只追加，不修改**）

---

## Promoted From Short-Term Memory（2026-05-25 ~ 2026-05-30）

### 重要决策与结论
- **[2026-05-30] 紫微斗数排盘统一方案**：程序与文墨天机在亮哥命盘完全一致，但在长子/次子命盘存在差异。数学证明：年干=乙时，命宫天干永远不可能为甲（(乙+申)%10=己≠甲）。**决策：以后统一用文墨天机排盘，程序保留作为内部参考工具，不再深究差异原因。**
- **[2026-05-30] 次子年干支确认**：lunar_python验证确认次子年柱=乙未、农历正月29日，程序年干支计算正确。

### 项目关键进展
- **[2026-05-30] 惠城环保数字化转型项目**：当前核心任务为方案确认和立项推进。
- **[2026-05-24] Spider重置任务**：青岛阳光招标爬虫重置成功，清空历史后抓取到2653条新记录。
- **[2026-05-22] Spider重置任务**：抓取到2636条记录，数据正常入库。
- **[2026-05-21] Spider重置异常**：触发抓取时连接超时（192.168.1.2:18080），但后台任务仍在运行，最终返回2640条记录。
- **[2026-05-20] Spider无数据**：爬虫历史记录为空，当日无新商机推送。

### 教训与纠正
- **[2026-05-21] Spider超时处理**：超时不代表任务失败，后台可能仍在运行。验证时应检查最终数据量而非仅看触发结果。

---

## Promoted From Short-Term Memory (2026-06-11 ~ 06-12)

### 工具评估四连击：四次评估全部"不装"，零例外

| 时间 | 评估项 | 决策 | 核心理由 |
|---|---|---|---|
| 2026-06-11 | **Memory-OS**（Hermes 7 层记忆） | ❌ 不装 | 平台不兼容（Hermes 专用） + 重型依赖（Docker × 3） + 营销味重 + 已有方案 80% 覆盖 |
| 2026-06-11 | **华为风 PPT 技能**（image-to-editable-ppt-slide / kai-slide-creator 等） | ❌ 不装 | 需求未触发（无客户正式方案要发） + 现有 ppt-workflow 走学术风 |
| 2026-06-11 | **OpenSquirrel**（Infatoshi/Rust 并排跑多 agent 工具） | ❌ 不装 | 平台不兼容（macOS only） + 主力 OpenClaw 不在支持列表 + 3 个月龄 + 安全风险 |
| 2026-06-12 | **hermes-agentmesh**（视频中提到的 Hermes 多 agent 框架） | ❌ 不装 | 平台不兼容（Hermes 专用） + 仓库用户名乱码疑似 spam + OpenClaw 原生有 sessions_spawn 解决同样问题 + 需求错位（亮哥单用户单 agent） |

### 工具评估铁律（**promoted 到长期记忆**）

**核心判断公式**：一个第三方 Agent 工具，**只要不跟 OpenClaw 强绑定 + 不在亮哥真实工作流里 + 必要性为 0，3 秒判"不装"**。

**详细判定标准**（满足任一即判"不装"）：

1. **平台绑定** — 工具强依赖 Hermes / Claude Code / Cursor / OpenCode 等其他 Agent 框架（亮哥用 OpenClaw，迁移成本 = 换骨架）
2. **非真实场景** — 营销文、视频、YouTube 链接的"agent 工具" 90% 是 demo 性质，亮哥单用户单 agent 模式用不到
3. **必要性 = 0** — OpenClaw 已有等价能力（如 sessions_spawn = 多 agent 协作；MEMORY.md + 分块加载 = 长期记忆；FTS5 全文检索 = 文本检索）
4. **可疑来源** — GitHub 用户名乱码、Stars 异常、域名可疑、营销话术重（"X 周斩获千星"）
5. **需求未触发** — 亮哥没明确说"我要做 XX"，只是看到/听说某工具 → 0 价值

**什么时候值得再看**（反模式）：

- 亮哥**明确表达痛点**（如"我需要做多 agent 协同方案给客户看"）
- 工具**支持 OpenClaw** 或**有 OpenClaw 等价物**
- 工具**活过 1 年 + 1.0 稳定** + **有真实使用案例**（非 demo）
- 亮哥**换主力框架**（如弃 OpenClaw 转 Hermes）→ 那时候才重新评估

### 借鉴的 1 个原则

**L7 Ground Truth**（从 Memory-OS 评估中学到）已落地到 SOUL.md "记忆加载三原则" 第 2 条：**注入即真理**。项目本身不装，原则值得固化。

### 配套挂账

- **2026-09-11 / 2026-12-11** 时点提醒：复盘"3-6 个月后再看"的工具评估（Memory-OS / OpenSquirrel 等）

---

## Promoted From Short-Term Memory (2026-06-09)

<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:12:12 -->
- Conversation Summary: 我已经**手动补完 2 本**（大六壬指南），还差 **3 本**。**3 选项**： [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:12-12]
<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:14:16 -->
- Conversation Summary: **A. 继续手动补完**（段建业盲派+滴天髓阐微+紫微深造）—— 我现在用主对话 1 本 1 本写，预计 30-40 分钟; **B. 一个个 spawn**（不并行，1 个完成后再 spawn 下 1 个）—— 慢但稳定，60+ 分钟; **C. 直接用 IMA 知识库已有资料**（紫微深造讲义/段建业 PDF 早 2026-06-03 已上传 IMA）—— 我做轻量级索引笔记，10 分钟 [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:14-16]
<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:18:20 -->
- Conversation Summary: **A 选项**是大工程但**质量最高**，**C 选项**是**快但轻**。亮哥选哪个？ user: 你又报错了 assistant: 亮哥，**`/reset` 是新错误**——但**错误原因已知**：我并行 spawn 了 4 个子任务，OpenClaw 限流打回，刚才又有 6 次重试失败。 [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:18-20]
<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:22:22 -->
- Conversation Summary: **问题出在**：我**对 spawn 并发数没控制**——**v2 范式最大的教训是"工具-专家 50:50 协作"，但对底层的 OpenClaw 限流机制没做边界测试**。 [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:22-22]
<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:3:5 -->
- Session: 2026-06-05 21:40:51 GMT+8: **Session Key**: agent:main:liangge-main-session; **Session ID**: 68b6c44d-fc5f-41f0-9a8b-5c28683fc44f; **Source**: webchat [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:18-20]
<!-- openclaw-memory-promotion:memory:memory/2026-06-05-2140.md:9:10 -->
- Conversation Summary: user: 怎么又报错了 assistant: 亮哥，**子任务 token 超限报错**——我用 `sessions_spawn` 并行 4 个古籍学习笔记，**OpenClaw 限流把它们全打回去了**（"当前请求量较高，建议升级更高级别套餐"）。 [score=0.820 recalls=0 avg=0.620 source=memory/2026-06-05-2140.md:9-10]

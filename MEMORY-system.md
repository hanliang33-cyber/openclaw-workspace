# MEMORY · 系统/工具块（v1.6 拆分后 · 2026-06-09）
_Last updated: 2026-06-09 12:30_

> **加载时机**：工具配置、cron、API 调用、OpenClaw 运维  
> **不加载**：纯命理推算（那块在 MEMORY-mingli.md）  
> **关键信息**：所有 API 端点、模型 ID、cron 任务清单、OpenClaw 实例

---

## API 路径

- **SenseNova**: `https://token.sensenova.cn/v1`（⚠️不是 api.sensenova.cn）
- **IMA 知识库**: `search_knowledge`（不是 `knowledge_base/search`）
- **命理排盘**: `POST http://192.168.1.2:19130/api/bazi`（禁止手算）
- **软路由SSH**: root/guy1a2s3d，192.168.1.2:22

## 渠道

- 微信: `o9cq80-7C2rHKoWbO8tDTHcQO3BA@im.wechat`
- 飞书: App ID `cli_a906141787b89cc1`，websocket模式

## 模型

- 默认: minimax-cn/MiniMax-M2.7
- 回退: custom-token-sensenova-cn/sensenova-6.7-flash-lite
- 图片: nvidia/moonshotai/kimi-k2.6
- SenseNova: sensenova-6.7-flash-lite
- ⚠️ SenseNova max_tokens 需≥3000，否则 content 为空

## cron 推送

- daily_rss_push（8:30）: 微信 + 飞书
- daily_customer_intel（9:00）: 微信 + 飞书 + Bitable

## OpenClaw 实例

- 主（tHO8）: 13817
- 备用（8kIb）: 28789

---

## cron_daemon 启动小贴士（2026-06-02 实施）

**4 个纯脚本任务已迁出 openclaw cron，由自建 daemon 接管**：
- daily_spider_reset（07:00 每天）
- daily_customer_fetch（08:50 每天）
- daily_customer_intel（09:05 每天）
- session-cleanup（10:00 每周日）

**容器无 systemd、无 cron daemon**，daemon 由 nohup 手动启动，**容器重启后需要重启 daemon**：

```bash
# 1. 删 stale PID（重启后 daemon 进程已死，但 PID 文件可能在）
rm -f /home/node/.openclaw/logs/cron-daemon.pid

# 2. 启动 daemon
nohup python3 /home/node/.openclaw/scripts/cron_daemon.py &
```

**健康检查**：
```bash
# 看 daemon 是否在跑
cat /home/node/.openclaw/logs/cron-daemon.pid && ps -p $(cat /home/node/.openclaw/logs/cron-daemon.pid)

# 看最近一次执行日志
tail -f /home/node/.openclaw/logs/cron/<task_name>.log

# 跑一次指定任务（手动触发）
bash /home/node/.openclaw/scripts/cron-wrapper.sh <task_name> <script_path>
```

**注**：尝试用 OpenClaw hook `gateway:startup` 自动拉起 daemon 失败——OpenClaw 用户级 hook 支持不完整（enable 状态不触发 dispatch）。已删 hook，**接受 manual 启动**。

**daily_ima_sync 暂未迁**：源码 `upload_to_ima.py` 从未实现，5/29 6/1 报告是 LLM 幻觉。**已知每天会失败**，需独立工程修。

---

## IMA 知识库 实战 RAG 总结（2026-06-03）

### 1. 专属文件夹结构

亮哥在 IMA 根目录下建了"**阿 pin 专用**"文件夹，ID 列表见 `/home/node/.openclaw/workspace/skills/ima-skills/folder_map.json`。

**核心 folder_id**：
- 根：`folder_7467721876862004`（"阿 pin 专用"）
- 命理框架：`folder_7467723151929484`
- 每日记录：`folder_7467723198040279`
- 客户工作：`folder_7467723252567643`
- 工具脚本：`folder_7467723294539394`

### 2. 一次性大迁移（2026-06-03 完成）

**23/24 成功上传**到"阿 pin 专用"对应子文件夹。失败 1 个是 `docx_reader.py`（扩展名 .py 不支持）。

**已上传内容**：
- **盲派**：段建业盲派命理.pdf + 杨清娟 245 页案例集 + 盲派框架沉淀
- **紫薇**：紫微深造讲义 + 紫微框架沉淀
- **滴天髓**：滴天髓阐微全文 + 滴天髓框架沉淀
- **六壬**：华龄版大六壬指南 + 大六壬总归 + 大六壬终身论命 + 六壬框架沉淀
- **千里命稿**：原书 + 学习笔记
- **北通命稿**：核心案例集 + 十干断易 + 干支三字连 + 断命金口诀 + 盲派铁僧 + 盲派碎断 + 金不换口诀 + 十神虚透
- **工具脚本**：searcher-workflow + case-library-index

### 3. 每日自动同步（2026-06-03 完成）

**新工具**：`sync-daily-memory.js`（替代原 sync-dreaming.js）
- 每天同步 5 个文件到对应 folder：
  1. `dreaming/deep/{date}.md` → `每日记录/dreaming/`
  2. `dreaming/light/{date}.md` → `每日记录/dreaming/`
  3. `dreaming/rem/{date}.md` → `每日记录/dreaming/`
  4. `memory/{date}.md` → `每日记录/memory/`
  5. `memory/.dreams/session-corpus/{date}.txt` → `每日记录/session-corpus/`

**关键技术点**：
- 用 `spawnSync` 代替 `execSync`（避免参数解析问题）
- 用真 `cred.token` 代替占位符 `'***'`（COS 端需要真 token）
- 用绝对路径代替 `__dirname`（`node -e` 上下文里 `__dirname` 是 `.`）

**已改**：`/home/node/.openclaw/scripts/daily_ima_sync.sh` 现在调用 `sync-daily-memory.js` 而非 `sync-dreaming.js`。

### 4. 实战 RAG 召回工具（2026-06-03 完成）

**3 个工具**：

| 工具 | 用途 |
|---|---|
| `ima-recall.js` | IMA 文件级搜索（用 IMA `search_knowledge` API）|
| `ima-semantic-recall.js` | 语义级本地+IMA 双搜（带 docx 段落解析、多关键词 AND 跨 5 行）|
| `docx_reader.py` | docx 按段落分隔提取（避免单行问题）|

**用法**：
```bash
# 文件级搜索
node ima-recall.js "杨清娟"

# 语义级搜索（多关键词跨行）
node ima-semantic-recall.js "辛金 亥"
node ima-semantic-recall.js "丙辛合"
node ima-semantic-recall.js "站队"  # 框架内术语
node ima-semantic-recall.js "铸印"  # 六壬课体
```

**召回效果实测**：

| 关键词 | 命中文件 |
|---|---|
| 辛金 | 杨清娟 + 段建业 + 大六壬指南 + 大六壬总归 + 千里命稿 + 滴天髓 |
| 辛金 亥 | 4 个文件（含"乙木长生在午死于亥"）|
| 丙辛合 | 5 个文件（含 2 个真命例"丙午辛丑戊寅壬戌"）|
| 站队 | 盲派框架 v1.4（亮哥 2022 真校准）|
| 得位 | 段建业 + 六壬指南 + 三个框架 |
| 铸印 | 大六壬指南 + 总归（真课体"铸印乘轩"）|
| 伤官配印 | 杨清娟 + 北通（真命例"壬寅癸卯金铂金命"）|
| 禄神做功 | 段建业 + 盲派框架 |
| 戊癸合 | 8 处匹配（多源交叉验证）|
| 丁壬合 财 | 段建业真命例"23岁流年丁卯同居" |

**已知限制**：
- IMA 搜索只对**文件名/标题**建索引，不索引正文
- → 用本地 docx 段落搜索补全（已实现）
- 多关键词必须 AND 跨 5 行内（已实现）
- 召回结果不带"高亮"，但本地搜索会输出 L### 行号 + 上下文

### 5. 关键文件路径

```
/home/node/.openclaw/workspace/skills/ima-skills/
├── folder_map.json                       # folder_id 映射表
├── ima-migrate.js                        # 一次性大迁移脚本
├── ima-recall.js                         # 文件级 IMA 搜索
├── ima-semantic-recall.js                # 语义级双搜
├── sync-daily-memory.js                  # 每日同步（替代 sync-dreaming）
└── knowledge-base/scripts/cos-upload.cjs # COS 上传（已修）

/home/node/.openclaw/scripts/daily_ima_sync.sh  # 改用 sync-daily-memory.js
/home/node/.openclaw/workspace/skills/calibration/ima-rag-summary.md  # RAG 总结
```

### 6. 亮哥的目标

**"通过 IMA 知识库的向量化，让阿 pin 可以通过问答召回内容，减轻阿 pin 忘记知识的负担"** —— **现已实现**。

**用法**：阿 pin 忘记某口诀/案例 → `node ima-semantic-recall.js "关键词"` → 召回真口诀+真命例+出处。

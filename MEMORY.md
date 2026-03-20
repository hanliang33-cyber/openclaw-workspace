# 阿pin 的核心记忆

## 身份与角色
- **名称**: 阿pin
- **类型**: AI 助理
- **性格**: 工作时正式靠谱稳重，生活闲聊时有点幽默

## 用户信息
- **亮哥**: 主要用户，不喜欢胡说八道

### 职业信息
- **公司**：青岛大数据科技公司
- **职位**：副总经理
- **负责领域**：企业数字化事业部 经营管理 + 市场部 负责人
- **核心能力**：企业管理、市场营销、大客户销售、数字化转型服务、项目管理
- **2026目标**：新签合同额2000万、外部产值1600万、回款率40%

### 已安装技能
详见 `memory/2026-03-18.md`：
- 核心12件套：find-skills, ontology, writing-humanizer-zh, summarize, gog, proactive-agent-lite, agent-browser-clawdbot, github-cli, github-ops, openclaw-tavily-search, skill-vetter, self-improving-agent
- 飞书相关：feishu-bitable-creator
- 系统自带：weather

## 主题化记忆
详细经验见 `memory/topics/` 目录：
- `feishu.md` - 飞书配置与操作
- `cron.md` - 定时任务配置
- `spider.md` - 爬虫配置
- `business.md` - 业务管理

## 配置文件
- 位置：/home/node/.openclaw/config.json

## 系统限制
- 容器内无法安装 npm 包
- 无法直接查看 OpenClaw 系统配置

## 重要配置
- 飞书APP：cli_a906141787b89cc1
- 用户ID：ou_abc84d67f3a4917fe11eef3f3b824e38

## 学习领域
亮哥发送的PDF学习资料：
- 十五五规划：数字中国建设、算力算法数据供给、数智赋能
- 国央企监管：融资性贸易与虚假贸易穿透式监管、74号文、AI+监管模型

## 2026-03-20 配置更新

### 图片理解配置
- **最终方案**：NVIDIA API `moonshotai/kimi-k2.5`（支持 vision）
  - API: `https://integrate.api.nvidia.com/v1`
  - 走 OpenAI chat completions 格式
  - imageModel 已切换为 `nvidia/moonshotai/kimi-k2.5`
- **已删除**：MiniMax-VL-01（Anthropic兼容端点不支持图片输入，无法使用）

### 渠道配置
- 飞书 + Webchat 双渠道运行
- 图片回复通过 `message` 工具同步发飞书

### Skill清理
- 删除 `openclaw-skill-vetter`（与 `skill-vetter` 重复）

### 配置文件
- 位置：`/home/node/.openclaw/openclaw.json`
- `.env` 包含 MINIMAX_API_KEY + NVIDIA_API_KEY

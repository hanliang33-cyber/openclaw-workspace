# OpenClaw 灾难恢复备份

## 备份日期
2026-03-20

## 内容清单

| 文件 | 说明 |
|------|------|
| `openclaw.json` | 主配置文件（已脱敏，credentials用占位符替代） |
| `credentials.txt.enc` | 加密的密钥文件（需要解密） |
| `cron-jobs.json` | 定时任务配置 |
| `AGENTS.md` | 代理行为配置 |
| `MEMORY.md` | 核心记忆 |
| `SOUL.md` | 灵魂配置 |
| `USER.md` | 用户信息 |
| `TOOLS.md` | 工具配置 |

## 恢复步骤

### 1. 解密密钥
```bash
# 解密 credentials.txt.enc
openssl aes-256-cbc -d -pbkdf2 -in credentials.txt.enc -out credentials.txt -pass pass:apin-backup-2026
```

### 2. 恢复配置文件
```bash
# 恢复 .env
cp credentials.txt ~/.openclaw/.env  # 或手动编辑

# 恢复 openclaw.json（需要手动填入credentials）
cp openclaw.json ~/.openclaw/openclaw.json
# 然后编辑openclaw.json，填入真实的 appSecret 和 token
```

### 3. 恢复 Cron 任务
```bash
cp cron-jobs.json ~/.openclaw/cron/jobs.json
openclaw gateway restart
```

### 4. 恢复记忆文件
```bash
cp AGENTS.md MEMORY.md SOUL.md USER.md TOOLS.md ~/.openclaw/workspace/
```

## 需手动填入的内容（openclaw.json中占位符）
- `channels.feishu.appSecret`
- `gateway.auth.token`
- `.env` 中的 `MINIMAX_API_KEY`、`NVIDIA_API_KEY`

## GitHub 仓库
https://github.com/hanliang33-cyber/openclaw-workspace

# 爬虫配置

## tender-spider 部署
- 位置：/mnt/sata1-4/docker/tender-spider/
- 数据文件：/mnt/sata1-4/docker/tender-spider/data/history.json
- API 地址：http://192.168.1.2:18080

## 青岛阳光招采
- 网站：https://www.qdygcg.com
- API 接口：https://www.qdygcg.com/api/saas-portal/noauth/trans/trade/pageEs
- 关键词：软件、信息化、数字化

## 爬虫数据源
- API地址: http://192.168.1.2:18080
- 数据接口: /api/history
- 本地文件: /mnt/sata1-4/docker/tender-spider/data/history.json
- 注意: 优先使用API，本地文件作为备用

## GitHub 备份
- 仓库：https://github.com/hanliang33-cyber/claw33pin
- 恢复命令：
```bash
cd /home/node/.openclaw
git clone https://hanliang33-cyber:TOKEN@github.com/hanliang33-cyber/claw33pin.git /tmp/backup
cp /tmp/backup/config.json ./
cp /tmp/backup/cron/jobs.json ./cron/
cp /tmp/backup/openclaw.json ./
cp /tmp/backup/workspace/MEMORY.md ./workspace/
cp -r /tmp/backup/workspace/memory/ ./workspace/
```

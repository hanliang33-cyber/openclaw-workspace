# 飞书配置与操作经验

## 权限相关
- 飞书应用需要 `bitable:app` 和 `base:app` 权限才能操作多维表格
- 应用身份权限申请地址：https://open.feishu.cn/app/cli_xxx/auth

## 多维表格操作
- 使用 feishu_bitable_get_meta 解析链接获取 app_token 和 table_id
- 关联字段只能关联同一应用内的表格

## 消息发送
- 需要指定 target (open_id 或 chat_id)
- 用户 ID：ou_abc84d67f3a4917fe11eef3f3b824e38

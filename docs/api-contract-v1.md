# happy4travian API 契约 V1（服务器→联盟→账号→村庄→兵力）

## 认证
- `POST /api/v1/auth/wechat` 登录并绑定用户
- `POST /api/v1/auth/refresh` 刷新令牌

## 服务器
- `GET /api/v1/servers` 列表
- `GET /api/v1/servers/{id}` 详情

## 联盟
- `POST /api/v1/alliances` 创建 `{ server_id, name, tag }`
- `GET /api/v1/alliances/{id}` 详情
- `GET /api/v1/alliances/{id}/members` 成员列表
- `POST /api/v1/alliances/{id}/invite` 邀请 `{ inviter_account_id, invitee_contact }`
- `POST /api/v1/alliances/{id}/members/review` 审核 `{ game_account_id, decision }`

## 游戏账号
- `POST /api/v1/accounts` 创建 `{ server_id, tribe_id, in_game_name }`
- `GET /api/v1/accounts/me` 我的账号列表

## 村庄与兵力
- `GET /api/v1/villages` 查询（支持 `server_id`、`account_id`）
- `POST /api/v1/villages` 创建 `{ server_id, account_id, name, x, y, is_capital }`
- `POST /api/v1/troops/upload` 上传兵力 `{ village_id, troop_type_id, count }`
- `GET /api/v1/troops/summary` 联盟/账号聚合（支持 `server_id`、`alliance_id`、`account_id`）

## 防御
- `POST /api/v1/defense/requests` 创建 `{ alliance_id, requester_account_id, target_x, target_y, arrive_time, needs_json }`
- `POST /api/v1/defense/assign` 认领 `{ defense_request_id, account_id, from_village_id?, troop_type_id?, count? }`
- `GET /api/v1/defense/board` 看板（支持 `server_id`、`alliance_id`）

## 联攻
- `POST /api/v1/attack/plans` 创建 `{ alliance_id, target_x, target_y, start_time, waves_json, notes? }`
- `POST /api/v1/attack/participate` 报名 `{ attack_plan_id, account_id, role, from_village_id?, troop_type_id?, count?, landing_time? }`
- `GET /api/v1/attack/board` 看板（支持 `server_id`、`alliance_id`）

## 资源支援
- `POST /api/v1/resources/push` 创建 `{ alliance_id, requester_village_id, target_village_id, resource_type, amount, arrive_time }`
- `POST /api/v1/resources/claim` 认领 `{ order_id, account_id }`
- `GET /api/v1/resources/board` 看板（支持 `server_id`、`alliance_id`）

## 战报
- `POST /api/v1/reports` 录入 `{ server_id, alliance_id?, reporter_account_id, report_time, text_raw }`
- `GET /api/v1/reports/{id}` 详情
- `GET /api/v1/reports/search` 搜索（支持 `server_id`、`alliance_id`、时间区间）

## 文件与通知
- `POST /api/v1/files` 上传元数据 `{ owner_account_id, alliance_id?, type, oss_key, url }`
- `GET /api/v1/notifications` 我的通知列表
# Happy4Travian 接口总览（当前实现）

## 概述
<!-- 文档说明：所有接口均为 REST 风格，示例均为中文注释 -->
- 基础路径：`/api/v1`
- 响应格式：统一返回 `application/json`
- 成功结构：`{ success: true, data: ..., count?: number, message?: string }`
- 失败结构：`{ success: false, error: string, message?: string }`

## 实体字段
- `User`
<!-- 用户实体：平台用户的基本信息与登录相关字段 -->
  - `id`：主键 ID
  - `nickname`：用户昵称
  - `wechat_openid`：微信 OpenID（第三方登录标识）
  - `email`：邮箱地址
  - `password_hash`：密码哈希值（不存明文）
  - `lang`：偏好语言（如 `zh`/`en`）
  - `status`：账户状态（如启用/停用）
  - `created_at`：账户创建时间
- `Server`
<!-- 服务器实体：游戏服/世界，包含倍速、开服时间与状态 -->
  - `id`：主键 ID
  - `code`：服务器代号（如 `com1`、`ts3`）
  - `region`：区域/分区（如 `com`、`asia`）
  - `speed`：倍速（如 `1x`、`3x`、`5x`）
  - `start_date`：开服日期
  - `status`：服务器状态（如运行中/已归档）
- `Tribe`
<!-- 部落实体：如罗马、条顿、高卢等阵营 -->
  - `id`：主键 ID
  - `code`：部落代码（如 `roman`、`teuton`）
  - `name`：部落名称
- `GameAccount`
<!-- 游戏账号实体：某用户在指定服务器上的游戏身份 -->
  - `id`：主键 ID
  - `user_id`：所属用户 ID
  - `server_id`：所在服务器 ID
  - `tribe_id`：所属部落 ID
  - `in_game_name`：游戏内昵称
- `Village`
<!-- 村庄实体：地图上的据点，含坐标与归属账号 -->
  - `id`：主键 ID
  - `server_id`：所在服务器 ID
  - `game_account_id`：所属游戏账号 ID
  - `name`：村庄名称
  - `x`：地图 X 坐标
  - `y`：地图 Y 坐标
- `TroopType`
<!-- 兵种类型实体：不同部落下的兵种种类定义 -->
  - `id`：主键 ID
  - `tribe_id`：所属部落 ID
  - `code`：兵种代码（内部编码）
  - `name`：兵种名称
- `TroopCount`
<!-- 兵种数量实体：记录村庄内各兵种的数量 -->
  - `id`：主键 ID
  - `village_id`：所属村庄 ID
  - `troop_type_id`：兵种类型 ID
  - `count`：数量（单位：个）
- `Alliance`
<!-- 联盟实体：服务器内的玩家组织与基本信息 -->
  - `id`：主键 ID
  - `server_id`：所在服务器 ID
  - `name`：联盟名称
  - `tag`：联盟标签/缩写
  - `description`：联盟描述
  - `created_by`：创建者 ID
  - `created_at`：创建时间
- `AllianceMember`
<!-- 联盟成员实体：联盟与游戏账号的关联与角色 -->
  - `id`：主键 ID
  - `alliance_id`：所属联盟 ID
  - `game_account_id`：成员的游戏账号 ID
  - `server_id`：所在服务器 ID
  - `role`：角色（如盟主/官员/成员）
  - `join_status`：加入状态（如申请中/已通过/已拒绝）
  - `joined_at`：加入时间

## 系统与健康
<!-- 监控与运行状况探针接口，用于健康检查与数据库连通性测试 -->
- `GET /api/v1/health`：健康检查（JSON 返回）
- `GET /api/v1/healthz`：健康检查别名
- `GET /api/v1/db/ping`：数据库连通性测试
- `GET /api/v1/troops_params`：兵种参数别名（同下方 `troops/params`）

## 服务器
<!-- 服务器资源的增删查接口（创建需提供 code/region/speed 等） -->
- `GET /api/v1/servers`
  - 列出服务器
- `POST /api/v1/servers`
  - 创建服务器
  - 请求体：`{ code: string, region?: string, speed?: string, startDate?: string|null }`

## 部落
<!-- 部落资源的增删查接口（创建需提供 code 与 name） -->
- `GET /api/v1/tribes`
  - 列出部落
- `POST /api/v1/tribes`
  - 创建部落
  - 请求体：`{ code: string, name: string }`

## 游戏账号
<!-- 游戏账号资源的增删查接口（关联用户、服务器与部落） -->
- `GET /api/v1/accounts`
  - 支持筛选：`userId?`, `serverId?`
- `POST /api/v1/accounts`
  - 创建账号
  - 请求体：`{ userId: number, serverId: number, tribeId: number, inGameName: string }`

## 村庄
<!-- 村庄资源的增删查接口（包含名称与坐标 x/y） -->
- `GET /api/v1/villages`
  - 支持筛选：`serverId?`, `gameAccountId?`
- `POST /api/v1/villages`
  - 请求体：`{ serverId: number, gameAccountId: number, name: string, x: number, y: number }`

## 兵种与参数
<!-- 兵种类型、兵种数量上传与汇总，以及兵种参数获取接口 -->
- `GET /api/v1/troop-types`
  - 支持筛选：`tribeId?`
- `POST /api/v1/troop-types`
  - 创建兵种类型
  - 请求体：`{ tribeId: number, code: string, name: string }`
- `POST /api/v1/troops/upload`
  - 上传兵种数量
  - 请求体：`{ villageId: number, counts: { [troopTypeId]: number } }`
- `GET /api/v1/troops/aggregate`
  - 汇总某村庄兵种数量
  - 查询：`villageId`
- `POST /api/v1/troops/parse-upload`
  - 从网页片段解析兵种数量并写入
  - 请求体：`{ villageId: number, html: string }`
- `GET /api/v1/troops/params`
  - 获取兵种参数，支持倍速缩放
  - 查询：`version`（目前固定 `1.46`）、`speed`（如 `1x|2x|3x|5x|10x`）、`debug?=1`

## 联盟与成员
<!-- 联盟创建、更新、删除与成员管理相关接口 -->
- `GET /api/v1/alliances`
  - 支持筛选：`serverId?`, `name?`
- `GET /api/v1/alliances/{aid}`
  - 获取联盟详情
- `POST /api/v1/alliances`
  - 创建联盟
  - 请求体：`{ serverId: number, name: string, tag: string, description?: string|null, createdBy: number }`
- `PUT /api/v1/alliances/{aid}`
  - 更新联盟：`name?`, `tag?`, `description?`
- `DELETE /api/v1/alliances/{aid}`
  - 删除联盟
- `GET /api/v1/alliances/{aid}/members`
  - 列出联盟成员
- `POST /api/v1/alliances/{aid}/members`
  - 添加成员
  - 请求体：`{ gameAccountId: number, role?: string }`
- `PUT /api/v1/alliances/{aid}/members/{mid}`
  - 更新成员：`role?`, `joinStatus?`
- `DELETE /api/v1/alliances/{aid}/members/{mid}`
  - 删除成员

## 开发辅助
<!-- 开发与演示数据相关接口（幂等的种子与迁移） -->
- `POST /api/v1/dev/seed`
  - 灌入基础演示数据（表幂等创建）
- `POST /api/v1/dev/migrate`
  - 运行缺失列的迁移（幂等）
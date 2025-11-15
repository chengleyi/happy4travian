## 目标范围
- 实体：玩家（GameAccount）、联盟（Alliance/AllianceMember）、种族（Tribe）、部队（TroopType/TroopCount，兵种参数静态化）、村庄（Village）
- 输出：接口功能清单、数据结构、实施步骤与每一步目的、前端对接点

## 现状回顾（代码基线）
- 服务器：`GET/POST /api/v1/servers`（backend_py/app.py:99-142）
- 种族：`GET/POST /api/v1/tribes`（backend_py/app.py:143-161）
- 玩家：`GET/POST /api/v1/accounts`（backend_py/app.py:163-194）
- 村庄：`GET/POST /api/v1/villages`（backend_py/app.py:195-226）
- 部队计数：`POST /api/v1/troops/upload`、`GET /api/v1/troops/aggregate`（backend_py/app.py:228-245）

## 兵种参数来源与静态化
- 来源链接（Kirilloid，各种族）：
  - 罗马：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=1&s_lvl=1&t_lvl=1&unit=1`
  - 日耳曼：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=2&s_lvl=1&t_lvl=1&unit=1`
  - 高卢：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=3&s_lvl=1&t_lvl=1&unit=1`
  - 匈奴：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=4&s_lvl=1&t_lvl=1&unit=1`
  - 埃及：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=5&s_lvl=1&t_lvl=1&unit=1`
  - 自然：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=8&s_lvl=1&t_lvl=1&unit=1`
  - 野蛮：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=6&s_lvl=1&t_lvl=1&unit=1`
  - 纳塔尔：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=7&s_lvl=1&t_lvl=1&unit=1`
  - 阿瓦里斯：`http://travian.kirilloid.ru/troops.php#s=1.46&tribe=9&s_lvl=1&t_lvl=1&unit=1`
- 处理策略：将兵种参数静态化为字典数据（随版本极少变化），在部署时一次性写入 `troop_types` 表；服务启动也可进行幂等校验与补充。
- 字段建议：`id, tribeId, code, name, category, speed, carry, attack, defInf, defCav, upkeep`

## 数据模型（新增/扩展）
### Alliance（联盟）
- `id, serverId, name, tag?, description?, leaderAccountId?, memberCount, createdAt`
### AllianceMember（联盟成员）
- `id, allianceId, gameAccountId, role('leader|officer|member'), status('active|invited|left'), joinedAt`
### TroopType（兵种定义，静态化）
- `id, tribeId, code, name, category, speed, carry, attack, defInf, defCav, upkeep`
### GameAccount（扩展）
- 新增 `allianceId?` 以便快捷筛选；与成员表保持一致性
### TroopCount（可选扩展）
- 新增 `snapshotAt` 支持历史趋势

## 接口规格
### Players（GameAccount）
- `GET /api/v1/accounts?userId&serverId&allianceId`
- `GET /api/v1/accounts/{id}`
- `POST /api/v1/accounts` `{userId, serverId, tribeId, inGameName, allianceId?}`
- `PUT /api/v1/accounts/{id}`、`DELETE /api/v1/accounts/{id}`

### Alliances（联盟）
- `GET /api/v1/alliances?serverId&name`
- `GET /api/v1/alliances/{id}`
- `POST /api/v1/alliances` `{serverId, name, tag?, description?}`
- `PUT /api/v1/alliances/{id}`、`DELETE /api/v1/alliances/{id}`
- 成员：`GET /api/v1/alliances/{id}/members`、`POST` `{gameAccountId, role?}`、`PUT/DELETE /members/{memberId}`

### Tribes（种族）
- 保持 `GET/POST /api/v1/tribes`，新增 `GET /api/v1/tribes/{id}`、`GET /api/v1/tribes/{id}/troop-types`

### Villages（村庄）
- 保持 `GET/POST /api/v1/villages?serverId&gameAccountId`，新增 `GET/PUT/DELETE /api/v1/villages/{id}`

### Troops（部队）
- 保持 `POST /api/v1/troops/upload` 与 `GET /api/v1/troops/aggregate?villageId`
- 新增：
  - `GET /api/v1/troop-types?tribeId`（前端表头与校验）
  - `POST /api/v1/troops/parse-upload` `{villageId, source:'travian', html}` → 解析为 `{troopTypeId: count}` 后复用现有上传逻辑
  - `GET /api/v1/troops/history?villageId&from&to`（启用快照时）

## 前端对接与截图映射
- 创建联盟：下拉 `GET /servers`、提交 `POST /alliances`，回跳详情或成员页
- 村庄概览：表格 `GET /villages?gameAccountId=...`、右侧图表 `GET /troops/aggregate?villageId=...`
- 更新村庄部队：粘贴框 `POST /troops/parse-upload`（Travian HTML 解析）

## 实施步骤与目的
1. 建表与模型补齐（alliances、alliance_members、troop_types）
   - 目的：确立联盟与兵种字典；与现有 `TroopCount` 外键一致
2. 静态化兵种：从 Kirilloid 抽取各族兵种参数，生成字典并写入 `troop_types`
   - 目的：统一兵种映射与前端表头，避免魔法数字
3. 扩展 GameAccount（`allianceId?`）并建立一致性钩子
   - 目的：便捷查询与成员同步
4. 联盟接口（CRUD + Members）
   - 目的：支撑“创建联盟”页面和成员维护
5. 村庄/玩家接口完善（详情、更新、删除）
   - 目的：完成 CRUD，支撑后续编排
6. 部队解析上传接口
   - 目的：贴 HTML 一键更新部队，复用现有 `upload`/`aggregate`
7. 校验与错误处理（字段、外键、权限占位）
   - 目的：保证数据质量，便于未来接入登录
8. 文档与单测（契约、解析器、聚合）
   - 目的：稳定对接，防止回归

## 校验与测试
- 单测：外键约束、接口 200/400/404、解析容错
- 集成：前端以 `BASE_URL` 调用核心 CRUD 与解析上传

若确认采用静态化兵种方案，我将按以上顺序开始实现（从建表与兵种字典静态化入手），并在落地过程中保持与现有返回结构的一致性。
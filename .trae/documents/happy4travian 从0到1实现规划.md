## 项目概述

* 名称：`happy4travian`
* 目标：提供联盟协作工具（管理、兵力与村庄汇报、防御与联攻、资源支援、战报归档）。
* 合规原则：不做未经授权的自动化抓取，依赖玩家自主录入。

## 关键反馈修正

* 按你的要求，联盟与成员拆分为两个数据实体：`alliances` 与 `alliance_members`。
* 移除 `villages.alliance_id`，以 `owner_user_id → alliance_members` 关系确定村庄归属，避免冗余与不一致。

## 产品范围（V1）

* 联盟管理：创建、邀请、审核；角色与权限（leader/officer/member）。
* 账号体系：微信小程序登录（`code2Session`），后续可加邮箱与第三方绑定。
* 村庄概览：坐标、人口、首都标记；联盟维度聚合（按成员村庄）。
* 兵力上传：村庄×兵种的最近值与快照，联盟汇总统计。
* 防御需求：目标/抵达时间/兵种需求；成员认领与进度。
* 联攻计划：目标与波次；参与者分工与提醒。
* 资源 Push：短缺申请、认领与执行状态。
* 战报管理：文本/图片录入，基础解析与关联到事件。

## 技术选型

* 后端：Java（Spring Boot 3 + Spring Security + JPA/Hibernate 或 MyBatis）。
* 数据库：MySQL（阿里云 RDS），按世界服分区/索引。
* 缓存：Redis；文件：阿里云 OSS。
* 前端：`uni-app`（小程序与 H5 同源代码）；通知渠道后续扩展到 Discord/WhatsApp。
* 部署：ECS + Docker + Nginx + HTTPS；监控：日志 +（可选）Prometheus/Grafana。

## 系统架构

* 模块化单体（V1）：`iam`、`alliances`、`villages`、`troops`、`defense`、`attack`、`resources`、`reports`、`notify`、`integration`（V1仅微信）。
* API：REST（`/api/v1`）、JSON、JWT；多世界服通过 `world_id` 贯穿。

## 数据模型（ER 文字描述，按拆分要求）

* `users`：`id`、`nickname`、`wechat_openid?`、`email?`、`password_hash?`、`lang`、`status`、`created_at`
* `worlds`：`id`、`code`、`region`、`speed`、`start_date`、`status`
* `alliances`（联盟）：`id`、`world_id`、`name`、`tag`、`description`、`created_by`、`created_at`
* `alliance_members`（成员）：`id`、`alliance_id`、`user_id`、`role`（leader/officer/member） 、`join_status`（pending/approved/rejected） 、`joined_at`
* `invitations`：`id`、`alliance_id`、`inviter_id`、`invitee_contact`、`status`、`token`、`expires_at`
* `villages`：`id`、`world_id`、`owner_user_id`、`name`、`x`、`y`、`population`、`is_capital`、`created_at`
* `troop_types`：`id`、`tribe`、`code`、`name`
* `troop_counts`：`id`、`village_id`、`troop_type_id`、`count`、`updated_at`
* `defense_requests`：`id`、`alliance_id`、`requester_id`、`target_x`、`target_y`、`arrive_time`、`needs_json`、`status`
* `defense_assignments`：`id`、`defense_request_id`、`user_id`、`from_village_id?`、`troop_type_id?`、`count?`、`status`
* `attack_plans`：`id`、`alliance_id`、`target_x`、`target_y`、`target_village_id?`、`start_time`、`waves_json`、`notes`、`status`
* `attack_participants`：`id`、`attack_plan_id`、`user_id`、`from_village_id?`、`role`、`troop_type_id?`、`count?`、`landing_time?`
* `resource_push_orders`：`id`、`alliance_id`、`requester_village_id`、`target_village_id`、`resource_type`、`amount`、`arrive_time`、`status`
* `battle_reports`：`id`、`world_id`、`alliance_id?`、`report_source`、`text_raw`、`parsed_json`、`reporter_id`、`report_time`
* `files`：`id`、`owner_id`、`alliance_id?`、`type`、`oss_key`、`url`、`created_at`
* `notifications`、`audit_logs`：用于提醒与审计。
* 关系关键点：通过 `alliance_members` 进行联盟关联；村庄归属由 `owner_user_id` → 该 `user_id` 在某 `alliance_id` 的成员关系确定；不在村庄表写联盟字段。

## 核心流程

* 微信登录：`code → openid → user` 建立/绑定 → JWT。
* 加盟与审核：邀请或申请 → 审核通过后露出联盟视图与权限。
* 兵力上传与汇总：按村庄×兵种录入 → 联盟面板聚合（经成员关系）。
* 防御与联攻：需求/计划 → 成员认领 → 倒计时提醒 → 状态推进。
* 资源 Push：短缺申请 → 认领执行 → 完成统计。
* 战报：录入与解析 → 关联事件。

## API 示例

* 认证：`POST /api/v1/auth/wechat`、`POST /api/v1/auth/refresh`
* 联盟与成员：`POST /api/v1/alliances`、`GET /api/v1/alliances/{id}`、`POST /api/v1/alliances/{id}/invite`、`POST /api/v1/alliances/{id}/members/review`、`GET /api/v1/alliances/{id}/members`
* 村庄与兵力：`GET /api/v1/villages`、`POST /api/v1/villages`、`POST /api/v1/troops/upload`、`GET /api/v1/troops/summary`
* 防御/联攻/资源/战报：与前版一致。

## 前端与迁移

* `uni-app` 统一代码，小程序优先；后续编译为 H5，仅在组件层做少量适配。
* 小程序页面：登录、联盟主页、成员审核、村庄列表、兵力上传、总览、 防御看板、联攻看板、资源看板、战报。

## 部署与运维

* ECS + Docker + Nginx + HTTPS；RDS（MySQL）、OSS；环境变量管理与日志监控。

## 里程碑

* M0：骨架与登录 — 1 周
* M1：联盟与成员（拆分版）、村庄与兵力上传 — 1\~2 周
* M2：防御需求与联攻计划 — 2 周
* M3：资源 Push 与战报 — 1\~2 周
* M4：H5 迁移与运维 — 1 周
* M5：Discord/WhatsApp 集成 — 2 周

## 计划文档（获批后创建）

* `docs/product-spec-v1.md`、`docs/er-model.md`（体现联盟与成员拆分）、`docs/api-contract-v1.md`、`docs/travian-basics.md`。

## 下一步

* 确认就按“联盟与成员拆分”的 ER 模型推进；我将据此搭建项目骨架与表结构，并落地首版 API 与页面。
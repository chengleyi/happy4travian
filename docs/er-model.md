# happy4travian ER 模型（按“微信用户→服务器→联盟→游戏账号→种族→村子→兵力”）

## 实体清单

- users：平台用户（含微信登录绑定）
- servers：服务器元数据
- tribes：部落（高卢、埃及、日耳曼、匈奴、罗马）
- alliances：联盟（按服务器）
- game_accounts：游戏账号（归属用户与服务器，绑定部落）
- alliance_members：联盟成员（成员对象为 game_account）
- villages：村庄（归属 game_account，绑定服务器）
- troop_types：兵种（按部落定义）
- troop_counts：兵力（村庄×兵种的数量记录）
- defense_requests：防御需求（联盟维度）
- defense_assignments：防御分配（认领与执行）
- attack_plans：联攻计划（目标与波次）
- attack_participants：联攻参与者（分工与到达时间）
- resource_push_orders：资源支援订单
- battle_reports：战报（文本/图片解析）
- invitations：联盟邀请（面向用户，接受时绑定到具体 game_account）
- files：文件对象（图片/附件，存储在 OSS）
- notifications：通知（渠道路由）
- audit_logs：审计日志

## 关系说明

- users 1..* game_accounts（一个用户可在多个服务器拥有多个游戏账号）
- servers 1..* alliances
- alliances 1..* alliance_members（成员为 game_account）
- game_accounts 1..* villages
- tribes 1..* game_accounts（每个游戏账号属于一个部落）
- villages 1..* troop_counts
- defense_requests 1..* defense_assignments
- attack_plans 1..* attack_participants

## 字段概要

- users：id，nickname，wechat_openid?，email?，password_hash?，lang，status，created_at
- servers：id，code，region，speed，start_date，status
- tribes：id，code，name
- alliances：id，server_id，name，tag，description，created_by，created_at
- game_accounts：id，user_id，server_id，tribe_id，in_game_name，status，created_at
- alliance_members：id，alliance_id，game_account_id，role，join_status，joined_at
- invitations：id，alliance_id，inviter_account_id，invitee_user_id?，token，status，expires_at
- villages：id，server_id，game_account_id，name，x，y，population，is_capital，created_at
- troop_types：id，tribe_id，code，name
- troop_counts：id，village_id，troop_type_id，count，updated_at
- defense_requests：id，alliance_id，requester_account_id，target_x，target_y，arrive_time，needs_json，status
- defense_assignments：id，defense_request_id，account_id，from_village_id?，troop_type_id?，count?，status
- attack_plans：id，alliance_id，target_x，target_y，target_village_id?，start_time，waves_json，notes，status
- attack_participants：id，attack_plan_id，account_id，from_village_id?，role，troop_type_id?，count?，landing_time?
- resource_push_orders：id，alliance_id，requester_village_id，target_village_id，resource_type，amount，arrive_time，status
- battle_reports：id，server_id，alliance_id?，report_source，text_raw，parsed_json，reporter_account_id，report_time
- files：id，owner_account_id，alliance_id?，type，oss_key，url，created_at
- notifications：id，user_id，type，channel，payload_json，delivered_at?，status
- audit_logs：id，actor_account_id，action，entity_type，entity_id，created_at

## 设计动机

- 联盟成员以 game_account 为主体，按服务器维度严格隔离。
- 村庄归属到 game_account，并显式携带 server_id，保障一致性与查询效率。
- 兵种以部落区分，通过 troop_types 与 tribes 绑定，保障后续不同兵种参数的扩展。
# 小程序产品需求文档（PRD）v1.1 — 2025-11-18（基于仓库实勘）

**概述**

* 背景：后端为 Flask+MySQL 的 REST 服务（`/api/v1`），目前无认证与权限；前端已有微信小程序 Demo 页通过 `wx.request` 直调后端。

* 目标：在现有接口能力上交付可用的浏览与基础操作型小程序，优先围绕 Travian 相关的数据实体（服务器、部落、账号、村庄、联盟、兵种/兵力）构建可用流程。

* 范围：MVP 不引入登录与权限；聚焦只读与有限写入的安全动作（联盟创建/成员维护、兵力上传与汇总）。

* 成功标准：核心页面 100% 可用；接口错误率≤1%；关键列表首屏<1.5s；端到端冒烟通过。

**项目现状与约束**

* 后端入口与蓝图：`backend_py/app.py`、`backend_py/factory.py`；路由分散在 `backend_py/routes/*`。

* 已有接口：系统健康、服务器/部落/账号/村庄的 GET/POST；联盟 CRUD 与成员 CRUD；兵种类型维护与兵力上传/解析/汇总。

* 未实现接口：文档中的认证、战报、资源、通知等不在代码中。

* 小程序目录：`frontend/miniprogram/pages/index/*`，当前为 API 测试面板；`utils/request.js` 将 `BASE_URL` 硬编码为公网 IP。

**信息架构与导航**

* 底部 Tab：`总览`、`服务器`、`联盟`、`村庄`、`兵力`、`我的`。

* 页面与入口：

  * 总览：关键实体数量与最近变更，跳转各模块列表。

  * 服务器：`GET /servers` 列表与新增；详情含关联部落/账号概览。

  * 联盟：`GET/POST/PUT/DELETE /alliances` 列表与详情；成员维护 `GET/POST/PUT/DELETE /alliances/{id}/members{,/mid}`。

  * 村庄：`GET /villages` 列表（支持 `serverId`/`gameAccountId`），详情含坐标与所属账号。

  * 兵力：`POST /troops/upload`、`POST /troops/parse-upload` 上传与解析；`GET /troops/aggregate?villageId` 汇总；`GET/POST /troop-types` 类型维护。

  * 我的：本地设置与关于；不含登录与用户资料编辑（后端未提供）。

**核心功能项（接口映射）**

* 系统健康：总览页首次加载调用 `GET /healthz`，异常兜底与重试。

* 服务器管理：查询与新增；新增校验重复与字段合法性。

* 联盟与成员：创建、编辑、删除；成员增删改查与角色/状态维护；操作二次确认。

* 村庄浏览：按服务器或账号过滤；详情坐标与关联跳转。

* 兵力上传与汇总：支持文件或文本解析上传；查看按村庄的汇总结果与图表展示。

* 兵种类型维护：按部落维护兵种字典；校验唯一性与关联约束。

* 设置与环境：在“我的”页管理 `BASE_URL` 环境（开发/预生产/生产），替代硬编码。

**数据模型（依据** **`backend_py/models.py`）**

* User：`id, nickname, wechat_openid?, email?, password_hash?, lang?, status, created_at`（MVP 不用）。

* Server：`id, code, region?, speed?, start_date?, status?`。

* Tribe：`id, code, name`。

* GameAccount：`id, user_id, server_id, tribe_id, in_game_name`。

* Village：`id, server_id, game_account_id, name, x, y`。

* Alliance：`id, server_id, name, tag, description?, created_by, created_at?`；AllianceMember：`id, alliance_id, game_account_id, server_id, role, join_status, joined_at?`。

* TroopType：`id, tribe_id, code, name`；TroopCount：`id, village_id, troop_type_id, count`。

**接口清单（MVP 使用）**

* 系统：`GET /api/v1/health`、`GET /api/v1/healthz`、`GET /api/v1/db/ping`。

* 服务器：`GET /api/v1/servers`、`POST /api/v1/servers`。

* 部落：`GET /api/v1/tribes`、`POST /api/v1/tribes`（用于兵种类型绑定）。

* 账号与村庄：`GET /api/v1/accounts`、`POST /api/v1/accounts`；`GET /api/v1/villages`、`POST /api/v1/villages`。

* 联盟：`GET/POST/PUT/DELETE /api/v1/alliances{,/id}`；成员 `GET/POST/PUT/DELETE /api/v1/alliances/{id}/members{,/mid}`。

* 兵力：`POST /api/v1/troops/upload`、`POST /api/v1/troops/parse-upload`、`GET /api/v1/troops/aggregate?villageId`；兵种类型 `GET/POST /api/v1/troop-types`。

**交互与体验**

* 统一空态、加载、错误与重试；列表支持下拉刷新与分页占位（后端暂不分页，前端做“按需加载”和最大返回数量限制）。

* 操作确认与结果提示；详情返回保持滚动位置与筛选条件。

* 多语言后置（先中文），字号与对比度遵循微信规范。

**性能与技术要求**

* 白屏<1.5s，接口超时 10s 并重试一次；组件级骨架屏与首屏优先加载。

* 环境管理：提供 `BASE_URL` 配置页并本地缓存；默认从 `https://happy4travian.com/api/v1` 读取。

* 缓存与限流：列表缓存 5–10 分钟；上传解析限制文件大小；汇总接口做防抖。

* 可观测性：前端错误上报、请求耗时与失败率埋点。

**权限与安全**

* 现状：后端无鉴权，所有接口开放。

* PRD 要求（MVP）：仅对“写入”动作（联盟创建/成员维护、兵力上传）做明显风险提示与本地确认，避免误操作。

* 迭代目标（M1+）：引入登录与角色权限（JWT/Session），接口侧校验与速率限制；HTTPS 强制、敏感信息不落日志。

**埋点与指标**

* 页面访问与跳转率；服务器/联盟/村庄列表的操作率；兵力上传与汇总完成率；错误与超时率；总览页点击分布。

**验收标准**

* 总览：健康检查成功与异常兜底；卡片数据正确。

* 服务器：查询与新增成功；重复/非法输入有提示。

* 联盟：CRUD 与成员维护完整；回到列表后状态可见；误删可取消。

* 村庄：按过滤条件查询结果正确；详情坐标展示与关联跳转正常。

* 兵力：上传/解析/汇总流程可用；异常文件有提示；类型维护校验生效。

* 设置：`BASE_URL` 切换立即生效且持久化；重启后仍有效。

**里程碑计划**

* M0（本周）：PRD冻结、原型与UI组件规范、接口契约对齐与差异清单。

* M1（+2周）：完成“服务器、联盟、村庄、兵力”页面与流程；联调与冒烟测试通过。

* M2（+1周）：错误处理与性能优化、埋点与报表；灰度上线。

* M3（可选）：登录与权限落地；分页与搜索后端支持；消息与通知能力。

**风险与依赖**

* 无鉴权导致写操作风险；后端缺分页与严格校验；硬编码 `BASE_URL` 易误用。

* 规避：前端环境配置与写操作确认；限制写接口入口；分页与校验列入后端迭代；CORS 域名对齐。

**开放问题**

* 是否需要在 MVP 就引入登录/权限？

* 兵力上传格式标准化与最大文件大小限定值？

* 是否需要“账号”与“用户”的更细粒度页面，或合并为“游戏账号”？


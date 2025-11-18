# 云端部署与接口全量测试报告（2025-11-18）

## 概览
- 范围：后端 Flask API 云端部署、所有接口的正向与异常测试、中文字符集问题根因修复与验证
- 结论：服务稳定运行，JSON 体解析与中文写入读取均正常；接口全量 E2E 覆盖通过，异常返回结构统一、参数校验生效
- 基址：`http://47.99.88.168:8080/api/v1`

## 关键修复
- 通用 JSON 解析工具：新增 `get_json()`，容错 `request.get_json()`、`utf-8/utf-8-sig`、`form-urlencoded`
  - 引入位置：`backend_py/utils/req.py`
  - 替换路由：`servers/tribes/users/accounts/villages/troops/alliances` 全部 POST 入口改用 `get_json()`
- BOM 文件读取兼容：`seed_basic_data.py` 读取 JSON 增加 `utf-8-sig` 回退
  - `backend_py/tools/seed_basic_data.py:121-135`
- 响应一致性与异常结构：`alliances` 用统一的 `ok/error` 返回；`not_found/bad_request` 覆盖所有路由
  - `backend_py/routes/alliances.py:81-147,173-232`
- 查询参数校验增强：`serverId/userId/gameAccountId` 类型错误返回 `bad_request`
  - `backend_py/routes/accounts.py:15-26`
  - `backend_py/routes/villages.py:15-26`
  - `backend_py/routes/alliances.py:18-25`
- Python 版本与依赖修复：
  - 服务器侧升级路径：优先 micromamba（Python 3.11）；不可执行则回退 IUS Python 3.11；同时兼容旧 venv 路径
  - `ops/systemd/happy4travian.service:9`（ExecStart 指向新环境 gunicorn）
  - `.github/workflows/deploy.yml:126-180,262-280`（安装依赖、重启服务、本地与外部冒烟、服务器侧 E2E）
- 日期解析兼容旧 Python：`servers` 路由对 `startDate` 使用 `strptime('%Y-%m-%d')` 回退
  - `backend_py/routes/servers.py:31-57`

## 中文“??”问题根因与彻底修复
- 数据库/列字符集统一：`utf8mb4/utf8mb4_unicode_ci` 覆盖所有可能中文字段
  - 迁移逻辑：`backend_py/tools/migrations.py:66-110`
  - 字段示例：`users.nickname`、`tribes.name`、`game_accounts.in_game_name`、`villages.name`、`alliances.name/tag/description`、`troop_types.name`（`backend_py/models.py:11,32,40,47,62-64,83`）
- 连接层强制 `utf8mb4`：`charset=utf8mb4` 与 `SET NAMES utf8mb4`
  - `backend_py/db.py:23-25`
- 响应不转义中文：`ensure_ascii=False`
  - `backend_py/utils/resp.py:11`
- 诊断接口：
  - `GET /api/v1/dev/charset` 返回关键列 `charset/collation`，确认 `utf8mb4_unicode_ci` 生效（`backend_py/routes/dev.py:31-59`）
  - 旧数据“??”需重写；新写入已正常显示中文

## 部署与流水线改动
- 重启与等待端口：在本地冒烟前 `systemctl restart` 并等待 `8080` 监听，失败打印 `journalctl`
- E2E 自动执行：
  - 服务器侧 Python requests 脚本：`backend_py/tools/e2e_requests.py`
  - 路由内置 E2E：`POST /api/v1/dev/e2e-run`（requests 不可用时回退 urllib）`backend_py/routes/dev.py:64-240`
- 依赖安装路径：
  - micromamba `h4t` 环境安装 `requests`
  - IUS Python 3.11 venv 安装 `requests`
  - 旧 venv 路径也安装 `requests`

## 全量 E2E 覆盖与结果
- 健康与系统：
  - `GET /health`、`/healthz`、`/db/ping` 均 200
  - `POST /dev/migrate` 返回 `migrate_done`
  - `GET /dev/charset` 关键列 `utf8mb4_unicode_ci`
- 基础资源（中文字段验证）：
  - `POST /users` 成功，返回中文昵称
  - `POST /servers` 成功，返回 `code/region/speed/startDate/status`
  - `POST /tribes`（短码 `PRMXXXXXXXX`）成功，返回中文名称
  - `POST /accounts` 成功，`inGameName` 中文写入正确
  - `POST /villages` 成功，`name` 中文写入正确
- 兵种与兵力：
  - `POST /troop-types` 两条成功；`GET /troop-types?tribeId=...` 返回列表
  - `POST /troops/upload` 成功；`GET /troops/aggregate` 成功；`POST /troops/parse-upload` 成功
  - `GET /troops/params?version=1.46&speed=3x` 成功，返回完整 `tribes.units` 数组（含 `off/def_i/def_c/speed/cost/rs_time/...`）
- 联盟与成员：
  - `POST /alliances` 成功（中文 `name/tag/description`）
  - `GET /alliances/{id}` 成功；`GET /alliances?serverId=...` 成功
  - 成员：`POST /alliances/{id}/members` 成功；`GET /alliances/{id}/members` 成功；`PUT /alliances/{id}/members/{mid}` 成功；`DELETE /alliances/{id}/members/{mid}` 成功
- 列表与筛选：
  - `GET /servers`、`/users`、`/tribes`、`/accounts?serverId=...`、`/villages?serverId=...`、`/alliances?serverId=...` 均 200
- 异常校验：
  - `GET /alliances?serverId=abc` → `bad_request/serverId_invalid`
  - `GET /alliances/999999` → `not_found`
  - `GET /troops/params?version=0` → `not_found`
  - `POST /servers {}` → `bad_request/code_required`
  - `POST /alliances {"serverId":sid}` → `bad_request/missing_fields`

## 风险与注意事项
- 历史“??”数据需以 UTF-8 请求体重写或更新（接口已支持中文）
- 服务器运行环境可能存在旧 venv 路径残留；流水线已在各环境安装 `requests` 并重启服务，避免 dev 路由阻断服务启动

## 建议的后续工作
- 保持服务器侧 E2E为非阻断，部署后自动执行并输出报告
- 前端提交中文统一 `Content-Type: application/json; charset=utf-8`
- 如需进一步自动化，可将 `/api/v1/dev/e2e-run` 的断言结果写入 CI 步骤输出以便审阅

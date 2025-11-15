## 检查结论
- 运行目录是 `/opt/happy4travian/backend_py`，systemd 使用 `--chdir /opt/happy4travian/backend_py`。
- 服务器上的 `app.py` 未包含 `quote_plus`，说明此前部署未覆盖运行目录文件。
- 当前工作流已改为将 `backend_py/*`、`app.py`、`requirements.txt` 上传至 `/opt/happy4travian/backend_py/`；部署阶段也会 `ls` 和 `grep quote_plus` 校验。
- 你把环境密码改回了原始值；若运行目录仍旧版代码，则会导致 DB 连接失败并出现 500。

## 修复方案
1. 部署前置校验（流水线里已添加）：
   - 打印 `/opt/happy4travian/backend_py` 列表，确认有 `app.py`。
   - `grep -n "quote_plus" /opt/happy4travian/backend_py/app.py`，确保新代码生效。
2. 文件上传目标统一到运行目录：
   - `Upload Python backend`、`Ensure app.py`、`Ensure requirements` 的 `target` 都指向 `/opt/happy4travian/backend_py/`。
3. 服务重启与探针：
   - 重启后，本机探针 `health/db` 输出。
   - 外部探针检查 `health/db/tribes/accounts/villages`。
4. 环境变量回退策略：
   - 若 `quote_plus` 校验失败（仍旧版），临时把密码改为 URL 编码（`Lakua%40123`）保障服务；待新版上线后恢复原始密码。

## 执行步骤（由我来操作）
- 重新触发 `deploy` 工作流（已保证 push 触发）。
- 部署完成后：
  - 校验服务器运行目录是否为新 `app.py`（工作流日志含 `grep quote_plus`）。
  - 如日志显示未匹配，先临时把密码改为百分号编码保服务在线，再强制覆盖文件并再次触发部署。
- 完成外网验证闭环：
  - `GET /api/v1/health`、`/api/v1/db/ping` → 200 且 `db=ok`
  - `GET /api/v1/servers/tribes/accounts/villages` → 200
  - `POST 创建 + GET 列表` 验证写入正常。

## 验证与交付
- 提供工作流日志中的运行目录校验与外部探针结果。
- 提供最终接口验证输出（状态码与返回体）。
- 确认后恢复原始密码 `Lakua@123` 并再次验证 `db/ping=ok`。

请确认以上计划，我立即执行。
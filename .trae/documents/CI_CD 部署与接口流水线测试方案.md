## 目标
- 完成后端容器化与可部署文件
- 建立推送即跑的流水线，包含构建、启动测试环境、接口冒烟测试

## 将新增/更新的文件
- `backend_py/Dockerfile`：后端镜像构建（基于 Python 3.11 + gunicorn）
- `docker-compose.ci.yml`：CI 场景启动 MySQL 与后端
- `.github/workflows/ci.yml`：GitHub Actions 流水线（如用 GitLab，可提供 `.gitlab-ci.yml` 等价版本）
- `tests/api/test_core.py`：接口冒烟测试（pytest + requests）
- 可选生产参考：`ops/k8s/*`（若需 K8s），或完善 `ops/systemd/*` 与 `ops/nginx/*`

## 容器化（Dockerfile 核心）
- 复制 `backend_py/requirements.txt` 安装依赖
- 复制后端源码，设置 `WORKDIR /app`
- 入口命令：`gunicorn --chdir /app -w 2 -b 0.0.0.0:8080 app:app`
  - 说明：当前入口仍为 `backend_py/app.py`，已改为工厂模式：`app = create_app()`（backend_py/app.py:1-3）
- 通过环境变量传入数据库连接（`SPRING_DATASOURCE_URL/USERNAME/PASSWORD`）

## 测试环境（docker-compose.ci.yml）
- `mysql`：使用官方镜像，设置 root 密码与数据库名 `happy4travian`
- `backend`：依赖 `mysql`，映射端口 `8080`
- 初始化 SQL：将 `docs/schema.sql` 挂载到 MySQL 初始化目录（或在 CI 步骤中导入）

## 流水线流程（ci.yml）
- 触发：`push` 与 `pull_request`
- 作业：
  1. `build`：构建后端镜像（缓存）
  2. `up`：启动 `docker-compose.ci.yml`
  3. `wait-db`：健康检查并导入 `docs/schema.sql`
  4. `smoke-tests`：运行 `pytest` 进行接口冒烟测试
  5. `artifact`：输出日志与测试报告
- 并在失败时保留容器日志便于定位

## 冒烟测试范围（tests/api/test_core.py）
- 健康检查：`GET /api/v1/health`、`/db/ping`
- 服务器：`POST /servers` 后 `GET /servers` 校验创建
- 种族：`POST /tribes` 后 `GET /tribes`
- 玩家：`POST /accounts`、`GET /accounts?serverId=...`
- 村庄：`POST /villages`、`GET /villages?gameAccountId=...`
- 联盟：`POST /alliances`、`GET /alliances`、成员增删改查
- 兵种字典：`GET /troop-types?tribeId=...`（先插入若干静态兵种）
- 部队：`POST /troops/upload` 幂等更新校验；`GET /troops/aggregate`
- 解析上传：`POST /troops/parse-upload` 返回 `parsed` 并入库

## 环境变量与端口
- `SPRING_DATASOURCE_URL`: `jdbc:mysql://mysql:3306/happy4travian`
- `SPRING_DATASOURCE_USERNAME`: `root`
- `SPRING_DATASOURCE_PASSWORD`: `${{ secrets.MYSQL_ROOT_PASSWORD }}`（CI 中以 secret 注入）
- 后端端口：`8080`

## 数据准备
- 通过 SQL 导入：`docs/schema.sql`
- 测试前预置基础 `tribes` 与部分 `troop_types`（静态化插入）

## 验证与产物
- 流水线输出：pytest 报告、容器日志
- 失败时：保留 `backend` 与 `mysql` 的 logs 作为 artifact

## 生产部署选项
- 继续沿用现有 `Nginx + gunicorn`（ops/nginx/happy4travian.conf；ops/systemd/happy4travian.service）
- 或提供 K8s 清单（Service/Deployment/ConfigMap/Secret）

## 计划执行顺序
1. 编写 `Dockerfile` 与 `docker-compose.ci.yml`
2. 编写 `ci.yml`（Actions），配置 secrets
3. 添加 `tests/api/test_core.py` 并补充静态兵种初始化步骤
4. 首次在本地/CI跑通，完善日志与失败回收策略

确认后，我将创建上述文件并提交，实现推送即跑的接口流水线测试。
## 重命名范围
- 根目录与仓库名：`tr_happy → happy4travian`
- 应用名与模块名：前端与后端的项目/服务名统一为 `happy4travian`
- 包名/组名：后端使用 `com.happy4travian`（artifactId: `happy4travian-api`）
- 配置与文档：更新所有包含旧名的配置与文档标题
- Docker/CI（如有）：镜像与流水线名对齐为 `happy4travian`

## 具体步骤
1. 重命名根目录为 `happy4travian`，确保开发环境路径与 IDE 映射更新
2. 前端（uni-app）
   - 更新 `manifest.json` 的 `name`
   - 更新 `package.json` 的 `name`
   - 统一基础路由前缀与标题为 `happy4travian`
3. 后端（Java Spring Boot）
   - 建/改模块名为 `happy4travian-api`
   - 包路径统一为 `com.happy4travian`
   - 配置 `spring.application.name=happy4travian`
4. 文档与术语
   - 更新 `docs/er-model.md` 标题与正文：主链改为 `微信用户→服务器→联盟→游戏账号→种族→村子→兵力`
   - 全文术语统一使用“服务器”，不出现“世界服”
5. 环境与部署
   - 若有 Docker/CI，统一镜像名/服务名为 `happy4travian`
   - Nginx/域名（后续）按 `happy4travian` 命名

## 近期里程碑（获得批准后立即实施）
- 生成 MySQL 建表 SQL（`servers/alliances/game_accounts/villages/troops` 等表与外键约束）
- 后端骨架：Spring Boot 3 + JWT + REST（认证/联盟/成员/村庄/兵力基础接口）
- 前端骨架：uni-app 小程序页面框架（登录、联盟、成员、村庄、兵力上传）
- 微信登录流程打通（`code2Session` → 绑定 `users` → 发 JWT）

## 风险与校验
- 在 Windows 环境完成目录更名后，确保 IDE、终端与任何脚手架脚本路径一致
- 检查所有配置与文档的旧名引用，保持一致性
- 不引入任何敏感信息到仓库（密钥走环境变量）
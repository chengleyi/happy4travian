## 范围与版本
- 目标网站：Kirilloid troops 页面（作为项目的权威数据源）
- 游戏版本：Travian T4.6、1x（s=1.46；铁匠/军工等级=1）
- 覆盖种族：1..9（罗马、日耳曼、高卢、匈奴、埃及、野蛮、纳塔尔、自然、阿瓦里斯）

## 产出文件
- `static/troop_types_T46_1x.json`：完整静态字典（version/speed/source/generatedAt/tribes/units）
- `sql/troop_types_T46_1x.sql`：幂等导入脚本，写入 `troop_types(tribe_id, code, name)`；属性参数可保存在 JSON 或扩展表
- `scripts/fetch_troops_t46.py`：只读抓取脚本，支持重跑生成 JSON/SQL

## 字段结构
- 单位字段：`code`、`name`、`category(infantry|cavalry|siege|special)`、`attack`、`defInf`、`defCav`、`speed`、`carry`、`upkeep`
- 命名约定：`code = <tribeCode>.unit<序号>`，序号按页面单位顺序；`tribeCode` 对应：`roman|teuton|gaul|huns|egypt|barbarian|natars|nature|avarice`

## 实施步骤
1. 抓取器实现：为每个 `tribeId` 拉取 `s=1.46&tribe=<id>&s_lvl=1&t_lvl=1`；设定 UA/超时/重试
2. 解析与映射：用 `BeautifulSoup` 定位单位表格，提取数值并映射类别与稳定 `code`
3. 规范化与校验：单位数量、字段长度与数值类型校验；缺失值处理策略
4. 静态化生成：写入 JSON 与幂等 SQL；在仓库中保存为项目资产
5. 预览与对照：提供 1–2 个族的 JSON 片段与 3–5 个单位的参数对照，确认准确性

## 验证
- 抽样核对页面参数与 JSON 一致性
- 调用现有接口 `GET /api/v1/troop-types?tribeId` 对比单位数量与名称（若已导入）

我将据此开始抓取并生成本地静态文件，先交付 JSON 预览，随后补齐完整数据与 SQL 脚本。
## 数据范围
- 版本与速度：Travian T4.6、1x（s=1.46；铁匠/军工=1）
- 种族：1..9（罗马、日耳曼、高卢、匈奴、埃及、野蛮、纳塔尔、自然、阿瓦里斯）
- 字段：name、category（infantry|cavalry|siege|special）、attack、defInf、defCav、speed、carry、upkeep

## 产物与位置
- `scripts/fetch_troops_t46.py`：抓取与解析脚本（requests+BeautifulSoup，UA/超时/重试）
- `static/troop_types_T46_1x.json`：完整静态字典（含 version/speed/source/generatedAt/tribes/units）
- `sql/troop_types_T46_1x.sql`：幂等导入脚本（`INSERT ... ON DUPLICATE KEY UPDATE` 写入 `troop_types(tribe_id, code, name)`；参数可留 JSON 或扩展表）

## JSON 结构
- 顶层：`{ version:"T4.6", speed:"1x", source:"kirilloid", generatedAt, tribes:[] }`
- `tribes[]`：`{ tribeId, tribeCode, tribeName, units:[] }`
- `units[]`：`{ code:<tribeCode>.unit<序号>, name, category, attack, defInf, defCav, speed, carry, upkeep }`

## 实施步骤
1. 抓取器实现：按 `s=1.46&tribe=<id>&s_lvl=1&t_lvl=1` 逐族拉取，设 UA/超时/重试
2. 解析与映射：定位单位表格，提取数值并归类，生成稳定 `code`
3. 校验规范：单位数量、数值类型与字段长度；缺失值容错
4. 静态化生成：写入 JSON；生成幂等 SQL
5. 预览与对照：提供 1–2 个族的 JSON 片段与 3–5 个单位参数对照确认

## 验证
- 抽样比对页面参数与 JSON（attack/defInf/defCav/speed/carry/upkeep）
- （可选）导入后通过 `GET /api/v1/troop-types?tribeId` 比对数量与名称

## 交付节奏
- 先交 `static/troop_types_T46_1x.json` 预览片段→你确认→再交完整 JSON、SQL、脚本并说明使用方法
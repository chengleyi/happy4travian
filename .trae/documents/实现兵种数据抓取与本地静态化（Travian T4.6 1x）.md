## 目标
- 抓取 Kirilloid 的 T4.6 1x 兵种页面（tribe=1..9），解析并结构化为统一 JSON；同时生成幂等 SQL 导入脚本。
- 输出可长期使用的本地静态文件，供后端接口与前端表头/计算使用。

## 将新增的文件
- `scripts/fetch_troops_t46.py`：抓取与解析脚本（requests+BeautifulSoup，UA/超时/重试）
- `static/troop_types_T46_1x.json`：完整静态字典（version/speed/source/generatedAt/tribes/units）
- `sql/troop_types_T46_1x.sql`：幂等字典导入（`INSERT ... ON DUPLICATE KEY UPDATE`）
- 可选：`scripts/README.md`（运行与更新说明）

## JSON 结构
- 顶层：`{ version:"T4.6", speed:"1x", source:"kirilloid", generatedAt, tribes:[] }`
- `tribes[]`：`{ tribeId, tribeCode, tribeName, units:[] }`
- `units[]`：`{ code, name, category(infantry|cavalry|siege|special), attack, defInf, defCav, speed, carry, upkeep }`
- 命名约定：`code = <tribeCode>.unit<序号>`；`tribeCode` 映射：`roman|teuton|gaul|huns|egypt|barbarian|natars|nature|avarice`

## 抓取与解析细节
1. URL 组成：`.../troops.php?s=1.46&tribe=<id>&s_lvl=1&t_lvl=1`
2. 请求策略：统一 UA、超时 10s、最多重试 3 次
3. 解析：定位单位表格，按列抽取 name 与数值；序号保持页面顺序；类别依据单位类型映射
4. 校验：每族单位数量、数值类型与范围、字段长度（`code/name` ≤ 32）

## 静态化与导入
- 写入 `static/troop_types_T46_1x.json`（一次性抓取生成）
- 生成 `sql/troop_types_T46_1x.sql`（仅字典层面），如需参数入库可追加 `troop_attrs` 或 `attributes_json`

## 验证
- 抽样对比页面与 JSON 参数（attack/defInf/defCav/speed/carry/upkeep）
- （可选）导入后调用 `GET /api/v1/troop-types?tribeId` 比数量与名称

## 执行顺序
1. 编写抓取脚本与解析逻辑
2. 运行生成 JSON；生成 SQL
3. 提交 JSON 预览片段给你确认（1–2 个族的前 2 个单位）
4. 完整静态文件与导入脚本交付
## 抓取目标
- 版本与速度：T4.6、1x（s=1.46）。
- 来源页面：Kirilloid troops 页，按 tribe=1..9 逐族抓取（罗马、日耳曼、高卢、匈奴、埃及、野蛮、纳塔尔、自然、阿瓦里斯）。
- 参数范围：name、category、attack、defInf、defCav、speed、carry、upkeep（铁匠/军工厂等级=1）。

## 本地结构化产物
- `static/troop_types_T46_1x.json`：统一、可读、可长期使用的静态字典。
- `sql/troop_types_T46_1x.sql`：幂等导入脚本（ON DUPLICATE KEY UPDATE）。
- `scripts/fetch_troops_t46.py`：一次性抓取脚本（请求与解析）。

## JSON 结构设计
- 顶层：`{ version: "T4.6", speed: "1x", source: "kirilloid", generatedAt: ISO8601, tribes: [] }`
- `tribes[n]`：`{ tribeId, tribeCode, tribeName, units: [] }`
- `units[n]`：
  - `code`：稳定唯一（如 `roman.unit1`），不依赖文案
  - `name`、`category`：`infantry|cavalry|siege|special`
  - `attack`、`defInf`、`defCav`、`speed`、`carry`、`upkeep`
- 示例片段：
```json
{
  "version": "T4.6",
  "speed": "1x",
  "source": "kirilloid",
  "generatedAt": "2025-11-16T12:00:00Z",
  "tribes": [
    {
      "tribeId": 1,
      "tribeCode": "roman",
      "tribeName": "罗马",
      "units": [
        {"code":"roman.unit1","name":"军团兵","category":"infantry","attack":40,"defInf":35,"defCav":50,"speed":6,"carry":50,"upkeep":1},
        {"code":"roman.unit2","name":"禁卫兵","category":"infantry","attack":30,"defInf":65,"defCav":35,"speed":5,"carry":20,"upkeep":1}
      ]
    }
  ]
}
```
（注：示例数值仅用于结构演示，实际以抓取数据为准）

## 抓取与解析方案
- 抓取：`requests` 拉取各族 URL（含 s=1.46、等级=1），超时与重试策略；统一 UA。
- 解析：`BeautifulSoup` 定位单位表格，按顺序映射 `unit1..unit10` 与类别；数值转换为整数。
- 映射：`tribeId -> tribeCode` 对照表：
  - 1 roman、2 teuton、3 gaul、4 huns、5 egypt、6 barbarian、7 natars、8 nature、9 avarice
- 校验：
  - 每族单位数量与预期一致（如罗马 10）
  - 关键参数非空且为数值；`code/name` 长度 ≤ 32

## SQL/导入
- `troop_types(tribe_id, code, name)`：唯一键 `(tribe_id, code)`；
- 可选 `troop_attrs(troop_type_id, attack, def_inf, def_cav, speed, carry, upkeep)` 或直接 `attributes_json`；
- 导入脚本采用幂等逻辑，重复运行不产生冲突。

## 交付与预览
- 先抓取并生成本地 `static/troop_types_T46_1x.json`，提供给你预览。
- 同步产出 `sql/troop_types_T46_1x.sql` 与抓取脚本；
- 附 3–5 个单位的页面值对照表，确认一致。

## 后续接入（可选）
- 后端启动时检测空表并加载该 JSON；
- `GET /api/v1/tribes/{id}/troop-types` 返回静态字典；
- CI 增加字典一致性校验。

—— 如果确认以上方案，我将开始抓取并在项目中生成 JSON 与 SQL/脚本文件，随后把 JSON 预览发给你确认。
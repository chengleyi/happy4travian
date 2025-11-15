## 范围与版本
- 目标网站：Kirilloid troops 页面（你正在做的周边工具数据源）
- 游戏版本：Travian T4.6、1x（s=1.46，铁匠/军工厂等级=1）
- 覆盖种族：1..9（罗马、日耳曼、高卢、匈奴、埃及、野蛮、纳塔尔、自然、阿瓦里斯）

## 输出与结构
- `static/troop_types_T46_1x.json`
  - 顶层：`version`=`"T4.6"`、`speed`=`"1x"`、`source`=`"kirilloid"`、`generatedAt`、`tribes`
  - `tribes[]`：`{ tribeId, tribeCode, tribeName, units: [] }`
  - `units[]`：`{ code, name, category, attack, defInf, defCav, speed, carry, upkeep }`
  - `code` 采用稳定命名：`<tribeCode>.unit<序号>`（不依赖文案避免变动）
- `sql/troop_types_T46_1x.sql`
  - 幂等：`INSERT ... ON DUPLICATE KEY UPDATE` 写入 `troop_types(tribe_id, code, name)`
  - 属性参数暂以 JSON 文件供前端与计算使用；如需入库，追加 `troop_attrs`（或在 `troop_types` 增加 `attributes_json`）的迁移脚本
- `scripts/fetch_troops_t46.py`
  - 只读抓取脚本：`requests+BeautifulSoup`，UA、超时与重试、解析表格并映射类别

## 实施步骤
1. 抓取器实现
   - 逐族拉取 `s=1.46&tribe=<id>&s_lvl=1&t_lvl=1` 页面
   - 解析单位表格；统一数值类型；构建 `code/name/category` 与参数字段
2. 规范化与校验
   - 每族单位数量检查；`code/name` 长度与字符集校验；数值非空
   - 类别映射：步兵/骑兵/攻城/特殊（根据单位类型）
3. 静态化生成
   - 写入 `static/troop_types_T46_1x.json`（含元信息）
   - 生成 `sql/troop_types_T46_1x.sql`（仅字典层面），属性参数保存在 JSON（后续可入库）
4. 预览与对照
   - 提供 JSON 片段预览（1–2 个族、前 2 个单位）与 3–5 个单位的页面参数对照表
5. 接入建议（可选下一步）
   - 后端启动时检测空字典并加载 JSON；
   - 增加 `GET /api/v1/tribes/{id}/troop-types` 返回静态字典；
   - CI 增加字典一致性校验

## 验证
- 抽样对照页面与 JSON 的 `attack/defInf/defCav/speed/carry/upkeep` 参数
- 对每族单位数量与顺序进行一致性检查

## 交付顺序
- 抓取与解析 → 生成 JSON 与 SQL → 提供 JSON 预览 → 你确认后再完成入库对接（如需）
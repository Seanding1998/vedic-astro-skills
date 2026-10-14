# Clean-room 原生排盘入口

本文件说明 `scripts/vedic_native_calculator.py` 的使用范围。它是新增的出生信息直算路径，不替代现有的 JHora markdown/PDF 解析链。

## 当前能力边界与上游接入状态

这份 skill 已经有原生排盘代码：给出出生日期、当地时间、经纬度和时区后，可以计算 D1 与 SAV/BAV，并输出机器可校验的 JSON 和南印度式 D1 图形盘面。

当前本地实现的能力边界如下：

| 项目 | 当前状态 | 使用限制 |
| --- | --- | --- |
| D1、Lagna、九曜、宫位、Nakshatra/pada | 已实现 | Swiss Ephemeris；True Citra（缺少该模式时回退 Lahiri）；Whole-sign 宫位；Mean Node |
| SAV/BAV | 已实现 | 通过 PyJHora API 计算，并校验 SAV=337、BAV 行常量和列和；必须使用 `--require-ashtakavarga` 并通过校验 |
| D9/D10/D4/D5 | 尝试计算 | 依赖 PyJHora；当前本地回归测试没有覆盖这些分盘，不能仅凭字段存在就视为已验证 |
| Shadbala、完整 MD/AD/PD Dasha | 未实现 | 需要另有经过核验的数据源；不能用本脚本补造精确结论 |
| 图形盘面 | 已实现 | 生成南印度式 D1 SVG，并由 Markdown 摘要引用；暂不生成北印度式盘或分盘图 |

用户提供的 [CNWU16 上游](https://github.com/CNWU16/vedic-astro-skills)另有独立 `vedic-calculator` skill，文档声明包含 D1–D60 分盘、完整 MD/AD/PD、Shadbala 和 SAV/BAV。它采用自己的 `structured_data.md` 数据契约；本 skill 的 `chart_sanity_check.py` 目前只读取本地 JSON 或 JHora Markdown，不能把上游 Markdown 直接当成本地计算器 JSON 使用。上游安装与本地运行核验结果、兼容性和建议见仓库根目录的 `排盘能力调研与接入评估.md`。

当前原生入口会同时生成可视化 D1 SVG。大运与 Shadbala 尚不属于此版本已验证能力：PyJHora 4.8.6 在此环境中因 Swiss Ephemeris 返回值形状和缺失 `.se1` 星历文件而未能稳定计算 Vimshottari；上游 Shadbala 则含有针对 JHora 对照数据的自定义修正，尚无独立样本验证。因此不输出这些精确数值，也不把上游文档中的能力视为本地验证结果。

## 什么时候使用

用户直接提供以下信息时，可以优先尝试原生排盘：

- 出生日期：`YYYY-MM-DD`
- 当地钟表时间：`HH:MM`
- 出生地经纬度：`lat/lon`
- IANA 时区：例如 `Asia/Shanghai`、`Asia/Taipei`、`Asia/Kolkata`

## 安装

在项目根目录安装锁定的运行时依赖：

```bash
python -m pip install -r requirements-native-calculator.txt
```

`PyJHora==4.8.6` 的发布元数据遗漏了若干导入时依赖；不要只安装 `PyJHora`，必须使用这份 requirements 文件。

示例：

```bash
python "scripts/vedic_native_calculator.py" \
  --date 1998-01-01 \
  --time 12:30 \
  --lat 31.2304 \
  --lon 121.4737 \
  --tz "Asia/Shanghai" \
  --place "Shanghai" \
  --output structured_data_native.md \
  --json-output structured_data_native.json \
  --chart-svg-output vedic_chart_d1.svg \
  --require-ashtakavarga
```

生成 JSON 后，可以继续用现有校验脚本检查：

```bash
python "scripts/chart_sanity_check.py" structured_data_native.json
```

## 已实现能力

原生脚本当前实现这些可独立校验的基础字段：

- Swiss Ephemeris sidereal D1：Lagna、Sun、Moon、Mars、Mercury、Jupiter、Venus、Saturn、Rahu、Ketu
- Whole-sign houses：从 Lagna 星座起 1 宫
- Nakshatra 与 pada：按黄经直接推导
- Rahu/Ketu：Mean Node Rahu，Ketu 固定为 Rahu + 180 度
- 12 宫宫主与宫主落宫
- 7K 主用 Chara Karakas 与 8K 参考
- Parashari Graha Drishti：宫位照射，不使用西占 orb 相位
- AL/UL：按 Arudha 规则计算
- SAV/BAV：原生 D1 按 True Citra + Mean Node 计算星座落点，再输入 PyJHora Ashtakavarga API；强制校验 SAV=337、BAV 行常量和 BAV→SAV 列和
- D9/D10/D4/D5：如果本机安装 PyJHora，则尝试通过 PyJHora 分盘 API 计算

## 硬约束

- `--require-ashtakavarga` 失败时，不允许继续使用 SAV/BAV 数值结论。
- 如果用户已有 JHora markdown/PDF，仍优先保留原有 `jhora_markdown_bridge.py` + `chart_sanity_check.py` 路径，因为它已针对紧凑 `3x3` Ashtakavarga 表做过精确解析。
- 原生脚本生成 Markdown 摘要、结构化 JSON 和南印度式 D1 SVG；需要机器校验时使用 `structured_data_native.json`。
- Shadbala 暂不由原生脚本计算。需要 Shadbala 时，继续从 JHora PDF/markdown 提取，或等待后续独立公式实现。
- Full MD/AD/PD Vimsottari 暂不由原生脚本计算。月级、日级窗口判断不能用本脚本补造 dasha 精度。

## Clean-room 边界

本入口只复用公开领域规格和公开库 API：Swiss Ephemeris、PyJHora、IANA timezone。不得把其他仓库的 `engine.py`、`ashtakavarga_pyjhora.py`、`dasha_pyjhora.py`、`shadbala_pyjhora.py` 或 `formatter.py` 函数体搬进本仓库。

可以借鉴的是目标 contract：字段要可校验，SAV 总和必须等于 337，BAV 行常量必须匹配，Rahu/Ketu 必须对冲，不能用近似或手写数据制造精确结论。

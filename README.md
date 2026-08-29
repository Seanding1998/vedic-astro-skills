# Vedic Astro Skills

[![Native calculator validation](https://github.com/Seanding1998/vedic-astro-skills/actions/workflows/native-calculator.yml/badge.svg?branch=main)](https://github.com/Seanding1998/vedic-astro-skills/actions/workflows/native-calculator.yml)

面向中文吠陀占星（Jyotish）分析的 skill 与可验证数据工具。项目以 `SKILL.md` 为智能体入口，按完整命盘、事业、婚姻、时间与场域等问题主动路由到相应参考框架。

除了解析 Jagannatha Hora（JHora）导出，本仓库还提供基于出生信息的原生 D1 与 SAV/BAV 计算路径。所有精确数值结论都应先经过机器校验，而不是由模型手工读表或心算。

## 能力概览

| 能力 | 状态 | 数据来源 / 校验 |
| --- | --- | --- |
| JHora markdown/PDF 导入 | 已支持 | `jhora_markdown_bridge.py` 与 `chart_sanity_check.py` |
| 紧凑 Ashtakavarga 表解析 | 已支持 | 支持 JHora `3x3` 边框格式 |
| 原生 D1 排盘 | 已支持 | Swiss Ephemeris、TRUE_CITRA、Mean Node |
| SAV/BAV 原生计算 | 已支持 | 原生 D1 星座落点 + PyJHora Ashtakavarga 矩阵 |
| SAV/BAV 守恒校验 | 已支持 | SAV=337、BAV 行常量、BAV 到 SAV 列和 |
| Nakshatra / pada | 已支持 | 由绝对黄经推导 |
| 宫主、Chara Karaka、Graha Drishti、AL/UL | 已支持 | 原生 D1 数据 |
| D9/D10/D4/D5 | 尝试输出 | 依赖 PyJHora，当前不作为 CI 的通过条件 |
| Shadbala 修正层 | 未实现 | 继续从 JHora 导出取得 |
| 完整 MD/AD/PD Vimsottari | 未实现 | 不用于月级或日级窗口结论 |

## 两条数据路径

### 1. 已有 JHora 导出

如果已有 JHora markdown、PDF 解析文本或结构化 JSON，优先走已有导入和校验链：

```bash
python scripts/chart_sanity_check.py <chart-input.json-or-jhora.md>
```

JHora 紧凑 Ashtakavarga 表可被结构化为 SAV/BAV 数据，并自动检查：

- SAV 12 星座总和是否为 `337`
- Sun 至 Saturn 的 BAV 逐行常量
- 每个星座的 BAV 列和是否等于 SAV

### 2. 只有出生信息

当具备出生日期、当地钟表时间、经纬度及 IANA 时区时，可直接生成原生结构化命盘。必须提供经纬度和时区，不能只用城市名猜测。

安装运行时依赖：

```bash
python -m pip install -r requirements-native-calculator.txt
```

运行示例：

```bash
python scripts/vedic_native_calculator.py \
  --date 2002-12-11 \
  --time 20:47 \
  --lat 25.4333 \
  --lon 119.0 \
  --tz Asia/Shanghai \
  --place Quanzhou \
  --require-ashtakavarga \
  --output structured_data_native.md \
  --json-output structured_data_native.json
```

随后使用共享校验器复核生成的 JSON：

```bash
python scripts/chart_sanity_check.py structured_data_native.json
```

`--require-ashtakavarga` 会在 SAV/BAV 无法产生时直接失败。只有 SAV 总和、BAV 行常量和 BAV 到 SAV 列和均通过时，才应在分析中采用 SAV/BAV 数值结论。

## 原生 SAV/BAV 的实现边界

原生计算器将 Swiss Ephemeris 计算出的 D1 星座落点输入 PyJHora 的公开 Ashtakavarga API。这样避免了让两个排盘层重复调用同一进程中的 Swiss Ephemeris 全局状态，同时仍使用 PyJHora 的 BAV/SAV 规则矩阵。

固定约定：

- Ayanamsa：`TRUE_CITRA`
- 节点：Mean Node Rahu，Ketu 固定为 Rahu + 180 度
- 宫位：从 Lagna 起的 Whole-sign houses
- SAV/BAV：必须完成三项算术一致性检查

GitHub Actions 会在计算器、校验器、测试或运行时依赖发生变化时自动运行原生 SAV/BAV 回归。

## 用作 Skill

支持本地 skill 的智能体环境中，以根目录的 `SKILL.md` 作为入口。它会根据用户问题选择最相关的 reference：

| 用户意图 | 主要参考 |
| --- | --- |
| 完整命盘、总览 | `references/总盘.md` |
| 事业、工作、赚钱 | `references/事业.md` |
| 婚姻、感情、关系 | `references/婚姻.md` |
| 迁移、城市比较、时间与地点 | `references/窗口与场域.md` |
| 术语与验证框架 | `references/术语框架.md` |
| 出生信息直算 | `references/calculator.md` |

用户提供完整出生信息但没有 JHora 导出时，入口路由会先选择 `references/calculator.md`，完成机器可校验的数据生成后，再进入总盘或专题分析。

## 项目结构

```text
.
├── SKILL.md                              # 智能体总入口和路由规则
├── references/
│   ├── calculator.md                     # 原生计算器使用与边界
│   ├── 总盘.md
│   ├── 事业.md
│   ├── 婚姻.md
│   ├── 术语框架.md
│   └── 窗口与场域.md
├── scripts/
│   ├── vedic_native_calculator.py        # 原生 D1 + SAV/BAV
│   ├── chart_sanity_check.py             # 共享数据校验器
│   ├── jhora_markdown_bridge.py          # JHora markdown 结构化导入
│   └── build_report_html.py              # 报告 HTML 打包
├── tests/
│   └── test_native_calculator.py          # SAV/BAV 回归测试
├── requirements-native-calculator.txt
└── CHANGELOG.md
```

## 开发与验证

在已安装依赖的环境中运行：

```bash
python -m py_compile scripts/vedic_native_calculator.py scripts/chart_sanity_check.py scripts/jhora_markdown_bridge.py
python -m unittest discover -s tests -p "test_native_calculator.py" -v
```

当前 CI 回归覆盖：

- 9/9 行星完整性
- Rahu/Ketu 对冲
- SAV 总分 `337`
- BAV 逐行常量
- BAV 与 SAV 的逐列守恒
- 原生 Nakshatra / pada 字段与共享校验器的兼容性
- CLI 生成 JSON 后的二次校验

## Clean-room 原则

本仓库的原生计算路径只基于公开占星规则及公开库 API 实现。它不复制其他仓库的计算器函数体。可复核的目标是数据 contract：固定输入约定、明确输出字段、可重复执行，以及 SAV/BAV 的算术一致性。

## 注意事项

- 出生时间精度会直接影响 Lagna、宫位和分盘；来源不稳时，应降低结论置信度。
- 经度、纬度、当地时间和 IANA 时区属于计算输入，不能用模糊地点描述替代。
- 本工具用于结构化占星研究与分析辅助，不应替代医疗、法律、投资或其他高风险专业建议。
- 历史变更见 [CHANGELOG.md](CHANGELOG.md)。

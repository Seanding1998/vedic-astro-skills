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

## 相对原始分支的改进

本仓库 fork 自 [CNWU16/vedic-astro-skills](https://github.com/CNWU16/vedic-astro-skills)。原项目持续提供覆盖多平台与多模块的完整能力；本分支的目标不同：将吠陀命盘分析收束为一个可直接挂载、可按主题路由、可追溯数值来源的中文 skill。

| 维度 | 原始分支的分发形态 | 本分支的改进重点 |
| --- | --- | --- |
| Skill 入口 | 面向不同宿主维护多套分发目录 | 根目录只有一个 `SKILL.md` 入口；规则和相对资源均可直接被标准文件型 skill loader 读取 |
| 路由方式 | 计算、专题与平台适配以模块组织 | 以用户问题为中心：完整命盘、事业、婚姻、时间与场域、出生信息直算分别进入最小必要 reference |
| 数据优先级 | 可从多种计算与输出模块取得结果 | 明确为“原始资料 / 原生直算 → 结构化 JSON → 共享校验 → 解释”的单向链，数值不能跳过校验直接进入结论 |
| JHora Ashtakavarga | JHora 可作为计算与导出来源 | 将紧凑 `3x3` 表格当作一等输入，精确提取 SAV/BAV，并强制检查 SAV=337、BAV 行常量、BAV 到 SAV 列和 |
| 无 JHora 时 | 需要选择相应计算模块 | 出生日期、当地时间、经纬度和 IANA 时区齐全时，直接走原生 D1 + PyJHora Ashtakavarga 矩阵，输出与导入路径相同的可校验 JSON |
| 质量门槛 | 模块级能力由各宿主环境调用 | 对原生计算器建立可重复 CI：依赖安装、语法编译、SAV/BAV 回归和共享校验器二次验证一起执行 |
| 中文研判交付 | 提供通用框架与跨平台能力 | 将分层推断、证据双重支撑、出生时间不稳降级、验证闸门和专题交付下限固化在统一入口 |

这些改进的重点不是增加术语或展示更多表格，而是减少代理在实际对话中的自由发挥空间：同一类输入会进入同一条数据链；不完整或不一致的数据会降级；SAV/BAV 数值必须先通过算术守恒检查。

## 标准 Skill 路由

这是一个按通用文件型 skill contract 编排的 skill：

- 根目录 `SKILL.md` 是唯一入口，负责触发范围、强约束和主动路由。
- `references/` 存放按问题域拆分的规则；入口只读取当前问题所需的文件，不把全部专题一次性塞入上下文。
- `scripts/` 只负责可执行的数据提取、原生计算、校验与报告包装；脚本输出不会绕开 `SKILL.md` 的证据和降级规则。
- 入口禁止把 reference 菜单抛给用户。它根据问题重心主动选择路径，并在最终回答中只呈现结论、数据依据和必要的限制。

实际路由如下：

```text
已有 JHora markdown / PDF 解析文本
  -> jhora_markdown_bridge.py 或 chart_sanity_check.py
  -> SAV/BAV 与基础盘面校验
  -> 总盘 / 事业 / 婚姻 / 时间与场域专题

出生日期 + 当地时间 + 经纬度 + IANA 时区
  -> vedic_native_calculator.py --require-ashtakavarga
  -> structured_data_native.json
  -> chart_sanity_check.py
  -> 按用户问题进入相应专题 reference

资料缺失、OCR 不可辨认或校验失败
  -> 明确标记缺口
  -> 降低结论置信度
  -> 不用未验证的 SAV/BAV 或精确时间结论补造答案
```

这种编排的优势是可移植与可控：支持标准 `SKILL.md` / `references/` 约定的宿主只需要加载一个入口文件；代理在一次对话中只取得相关知识和必要工具，不会因平台分发目录或无关专题而扩大上下文、混淆路由。

## 注意事项

- 出生时间精度会直接影响 Lagna、宫位和分盘；来源不稳时，应降低结论置信度。
- 经度、纬度、当地时间和 IANA 时区属于计算输入，不能用模糊地点描述替代。
- 本工具用于结构化占星研究与分析辅助，不应替代医疗、法律、投资或其他高风险专业建议。
- 历史变更见 [CHANGELOG.md](CHANGELOG.md)。

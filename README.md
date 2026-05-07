# 🔱 Vedic Astro Skills v5.2

> AI驱动的吠陀占星分析系统。五个专精Skill协同工作，从星盘数据提取到完整人生审计。
>
> AI-powered Vedic astrology analysis system. Five specialized skills working together — from chart data extraction to complete life audit.

**兼容 Antigravity 和 Claude Code。**

---

## ✨ V5.2 核心特性

- 🔄 **通用提取架构** — Reader不再绑定特定软件，支持任意来源的星盘（JH/Parashara's Light/截图/手工文本）
- 🧮 **16条数学校验** — 包括SAV/BAV常量、Ra-Ke对冲、燃烧检测、行星战争、Sandhi/Gandanta、盈月亏月等
- 🎯 **需求驱动的数据契约** — 三级数据清单（🔴关键/🟡重要/🟢可选），缺口自动分析
- 🛡️ **正反双审(Double Blind Audit)** — 所有Q&A强制列出支持和制约数据，防止AI偏见
- 🕐 **时间校准引擎** — 通过5个人生事件逆推出生时间，精度±5分钟
- 📊 **D9身份继承矩阵** — 五维交叉分析（身份继承/内核品质/安全分级/变现阻力/果实投射）

---

## 🏛️ 五Skill架构

```
用户星盘 (PDF/截图/文本)
    │
    ▼
┌─────────────┐
│ vedic-reader │ ← 数据门（提取 + 16条校验 + 生时矫正）
└──────┬──────┘
       │ structured_data.md
       ▼
┌─────────────┐     ┌────────────────┐
│  vedic-core  │────▶│ vedic-rectifier │ ← 时间校准（可选）
│ P1-P12审计   │     │ 5事件逆推±5min  │
│ 宫位诊断     │     └────────────────┘
│ 十大板块总结  │
└──────┬──────┘
       │ p2a~p5b + appendix
       ├──────────────┐
       ▼              ▼
┌──────────────┐ ┌───────────┐
│ vedic-career │ │ vedic-love │
│ 职业蓝图4Phase│ │ 恋爱时机3Step│
└──────────────┘ └───────────┘
```

| Skill | 功能 | 触发词 |
|-------|------|--------|
| 📖 **reader** | 星盘数据提取 + 16条数学校验 + 分盘可信度评估 | "读盘""星盘""印占""占星""看盘" |
| 🔬 **core** | P1-P12行星审计 + D9交叉 + 宫位诊断 + 十大板块 | "开始分析""帮我分析""星盘审计" |
| 💼 **career** | 4Phase职业蓝图（生态位→格局→D9→全维合成） | "分析事业""职业分析""10宫分析" |
| 💘 **love** | 3Step恋爱时机（体质→Dasha窗口→性质定性） | "分析感情""恋爱运势""桃花时机" |
| 📐 **rectifier** | 5事件时间校准，精度±5分钟 | "校准时间""时间矫正""出生时间不准" |

---

## ⚡ 使用指南

### 🟢 推荐流程

> **Step 1** → 发送星盘PDF/截图，说 **"读盘"**
>
> AI运行 `vedic-reader`：自适应提取 → 16条校验 → 盘面初验 → 输出 structured_data.md
>
> **Step 2** → 说 **"开始分析"**
>
> AI运行 `vedic-core`：P1-P12审计 → D9交叉 → 宫位诊断 → 十大板块 → 输出8个报告文件
>
> **Step 3** → 说 **"分析事业"** 或 **"分析感情"**
>
> AI运行 `vedic-career` 或 `vedic-love`，继承core审计数据进行深度专项分析

```
星盘PDF → reader(提取+校验) → core(审计+报告) → career/love(专项)
```

### 🟡 快速模式

直接说"分析事业"或"分析感情"也可以。career/love会检测structured_data是否存在：
- 存在 → 直接使用，深度模式
- 不存在 → 提示先运行reader

### 输入要求

- 星盘PDF（任何吠陀占星软件导出均可）
- 或星盘截图（南印/北印盘均可识别）
- 或直接粘贴文本格式的行星数据
- Python + PyMuPDF (`pip install pymupdf`) 用于PDF文本提取

---

## 📁 项目结构

```
vedic-astro-skills/
├── README.md
├── LICENSE
├── antigravity/skills/          # Antigravity 版本
│   ├── vedic-reader/
│   │   ├── SKILL.md             # 读盘引擎 (470行)
│   │   └── resources/
│   │       ├── data_contract.md # 数据契约 (204行)
│   │       └── validation_rules.md # 16条校验规则 (172行)
│   ├── vedic-core/
│   │   ├── SKILL.md             # 核心分析引擎 (451行)
│   │   ├── resources/
│   │   │   ├── p1_p12.md        # P1-P12参数定义
│   │   │   ├── house_framework.md # 宫位诊断框架
│   │   │   ├── yogas.md         # 格局判定规则
│   │   │   ├── qa_rules.md      # Q&A正反双审规则
│   │   │   └── report_rules.md  # 报告打包规则
│   │   └── scripts/
│   │       └── report_builder.py # HTML报告生成器
│   ├── vedic-career/
│   │   └── SKILL.md             # 职业分析引擎 (258行)
│   ├── vedic-love/
│   │   └── SKILL.md             # 恋爱时机引擎 (234行)
│   └── vedic-rectifier/
│       ├── SKILL.md             # 时间校准引擎 (263行)
│       ├── resources/
│       │   └── event_house_map.md # 事件-宫位映射
│       └── scripts/
│           └── time_scan.py     # Lagna/D9扫描计算器
└── claude-code/skills/          # Claude Code 版本 (同上)
```

**总计：15个文件 | 3,435行 | 115.7KB**

---

## 🔧 安装

### Antigravity

```bash
# 复制全部5个skill
cp -r antigravity/skills/vedic-* ~/.gemini/antigravity/skills/
```

### Claude Code

```bash
cp -r claude-code/skills/vedic-* [your-claude-code-skills-path]/
```

---

## 📋 版本历史

| 版本 | 日期 | 改动 |
|------|------|------|
| **v5.2** | 2026-05-08 | Reader通用提取架构 + 引导开场白 + 触发词扩展 |
| v5.1 | 2026-05-07 | Chehil对比合入（燃烧/行星战争/Dig Bala） + 结构优化 |
| v5.0 | 2026-05-06 | 五Skill架构确立 + Rectifier + 正反双审 |
| v4.x | 2026-05-05 | D9身份继承矩阵 + Badhaka/Maraka审计 |
| v3.x | 2026-05-04 | Q&A规则外置 + 报告打包脚本 |

---

## 🧪 技术体系

- **流派**: KN Rao体系 (Parashari)，Jaimini辅助
- **Ayanamsa**: Lahiri (默认)
- **分盘**: D1/D9/D10/D4/D5 (精度依赖出生时间)
- **校验**: 16条数学校验（SAV=337、BAV行常量、Ra-Ke对冲、燃烧检测等）
- **反偏见**: 正反双审机制 — 禁止只挑用户想听的数据

## License

MIT

# 🔱 Vedic Astro Skills v5.0

> AI驱动的吠陀占星分析系统。五个专精Skill协同工作，从星盘数据提取到完整人生审计。
>
> AI-powered Vedic astrology analysis system. Five specialized skills working together — from chart data extraction to complete life audit.

**兼容 Antigravity 和 Claude Code。**

> 💡 **v5.0 是本仓库的开源稳定版本。** 我们的开源初心不变——所有核心功能完整可用。后续前瞻版本将在独立仓库持续迭代。

---

## ✨ v5.0 核心特性

- 🔄 **三阶段执行引擎** — Reader分3个独立阶段执行，每阶段独立思考链，杜绝超长思考崩溃
- 🧩 **16条数学校验** — SAV/BAV常量、Ra-Ke对冲、燃烧检测、行星战争、Sandhi/Gandanta、盈月亏月
- 🎯 **需求驱动的数据契约** — 三级清单（🔴关键/🟡重要/🟢可选），缺口自动分析
- 🛡️ **正反双审** — 所有Q&A强制列出支持和制约数据，防止AI偏见
- ⏱️ **时间精度联动** — 出生时间精度不足时自动禁用高敏感分盘，推荐校准
- 📝 **信号驱动验前事** — 弹性3-5条，SOP多维评估 + P1/P5工具箱
- 🕰️ **时间校准引擎** — 5个人生事件逆推出生时间，精度±5分钟，且不强制改时间
- 💍 **婚姻三阶段模型** — L7关系确立 → 9宫法律确认 → 11宫社会公开，替代单点预测
- 📊 **智能报告打包** — 动态文件发现，按前缀自动分组，支持任意分段输出

---

## 🏛️ 五Skill架构

```
用户星盘 (PDF/截图/文本)
    │
    ▼
┌─────────────┐
│ vedic-reader │ ← 数据门（提取 + 16条校验 + 验前事）
│ 三阶段执行引擎│    阶段1: 提取+校验 → 阶段2: 预分析 → 阶段3: 验前事
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
| 📖 **reader** | 星盘数据提取 + 16条数学校验 + 三阶段执行 | "读盘""星盘""印占""占星""看盘" |
| 🔬 **core** | P1-P12行星审计 + D9交叉 + 宫位诊断 + 十大板块 | "开始分析""帮我分析""星盘审计" |
| 💼 **career** | 4Phase职业蓝图（生态位→格局→D9→全维合成） | "分析事业""职业分析""10宫分析" |
| 💘 **love** | 3Step恋爱时机（体质→Dasha窗口→性质定性） | "分析感情""恋爱运势""桃花时机" |
| 📐 **rectifier** | 5事件时间校准，精度±5分钟 | "校准时间""时间矫正""出生时间不准" |

---

## ⚡ 使用指南

### 🟢 推荐流程

> **Step 1** → 发送星盘PDF/截图，说 **"读盘"**
>
> AI运行 `vedic-reader`：三阶段提取（数据→预分析→验前事）→ 输出 structured_data.md
>
> **Step 2** → 说 **"开始分析"**
>
> AI运行 `vedic-core`：P1-P12审计 → D9交叉 → 宫位诊断 → 十大板块 → 输出报告文件
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

### 输入方式（按推荐程度排序）

1. 📝 **文字粘贴**（最推荐）— 从占星软件复制表格直接粘贴，零误差
2. 📄 **PDF上传** — 任何吠陀占星软件导出均可
3. 📸 **截图** — 南印/北印盘均可识别（推荐南印度 Regular）

---

## 📁 项目结构

```
vedic-astro-skills/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── antigravity/skills/          # Antigravity 版本
│   ├── vedic-reader/
│   │   ├── SKILL.md             # 读盘引擎 (1117行)
│   │   └── resources/
│   │       ├── data_contract.md  # 数据契约 (219行)
│   │       └── validation_rules.md # 16条校验规则 (180行)
│   ├── vedic-core/
│   │   ├── SKILL.md             # 核心分析引擎 (875行)
│   │   ├── resources/
│   │   │   ├── p1_p12.md        # P1-P12参数定义 (335行)
│   │   │   ├── house_framework.md # 宫位诊断框架 (211行)
│   │   │   ├── yogas.md         # 格局判定规则 (169行)
│   │   │   ├── qa_rules.md      # Q&A正反双审规则 (188行)
│   │   │   └── report_rules.md  # 报告打包规则 (37行)
│   │   └── scripts/
│   │       └── report_builder.py # HTML报告生成器 (517行)
│   ├── vedic-career/
│   │   └── SKILL.md             # 职业分析引擎 (328行)
│   ├── vedic-love/
│   │   └── SKILL.md             # 恋爱时机引擎 (281行)
│   └── vedic-rectifier/
│       ├── SKILL.md             # 时间校准引擎 (373行)
│       ├── resources/
│       │   └── event_house_map.md # 事件-宫位映射 (129行)
│       └── scripts/
│           └── time_scan.py     # Lagna/D9扫描计算器 (222行)
└── claude-code/skills/          # Claude Code 版本 (同上)
```

**总计：15个文件 | 5,181行 | 195.6KB**

---

## 📋 版本历史

| 版本 | 日期 | 改动 |
|------|------|------|
| **v5.0** | 2026-05-22 | **开源最终版** 三阶段执行引擎 + 性能优化 + 动态报告打包 |
| v4.9 | 2026-05-14 | 验前事定版: SOP多维评估 + SAV映射铁规 |
| v4.8 | 2026-05-13 | 分盘提取工程化: 三轨交叉验证 + 无条件截屏门控 |
| v4.7 | 2026-05-12 | 话术重构: 时间验证定位 + 砍R2 |
| v4.5 | 2026-05-11 | Mini-core: 行星快照 + SOP多维评估 + 工具箱体系 |
| v4.0 | 2026-05-10 | 双通道OCR + 验前事重写 + 时间精度联动 + Rectifier纠偏 |
| v3.0 | 2026-05-06 | 五Skill架构确立 + Rectifier + 正反双审 |

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 🧪 技术体系

- **流派**: KN Rao体系 (Parashari)，Jaimini辅助
- **Ayanamsa**: Lahiri (默认)
- **分盘**: D1/D9/D10/D4/D5 (精度依赖出生时间)
- **校验**: 16条数学校验（SAV=337、BAV行常量、Ra-Ke对冲、燃烧检测等）
- **反偏见**: 正反双审机制 — 禁止只挑用户想听的数据
- **执行引擎**: 三阶段独立思考链（提取→预分析→验前事）

## ☕ Support / 赞赏

If this project helps you, consider buying me a coffee:

如果这个项目对你有帮助，欢迎赞赏支持：

<p align="center">
  <img src="assets/wechat.jpg" width="200" alt="WeChat Pay">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/alipay.jpg" width="200" alt="Alipay">
</p>

<p align="center">
  <sub>WeChat Pay（微信支付） &nbsp;|&nbsp; Alipay（支付宝）</sub>
</p>

---

## License

MIT

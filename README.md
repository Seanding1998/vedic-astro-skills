<p align="center">
  <h1 align="center">🔱 Vedic Astro Skills v6.1</h1>
  <p align="center">
    <strong>AI驱动的吠陀占星分析系统 | AI-Powered Vedic Astrology Analysis System</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/version-v6.1-blue" alt="Version">
    <img src="https://img.shields.io/badge/python-3.8~3.13-green" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-orange" alt="License">
    <img src="https://img.shields.io/badge/skills-6-purple" alt="Skills">
  </p>
</p>

---

> **六个专精 Skill 协同工作，从原生排盘到完整人生审计。**
>
> Six specialized skills working together — from native chart calculation to complete life audit.

**兼容 Antigravity 和 Claude Code。** Compatible with Antigravity and Claude Code.

---

## 📖 目录 / Table of Contents

- [安装 / Installation](#-安装--installation)
- [六Skill架构 / Architecture](#-六skill架构--architecture)
- [快速开始 / Quick Start](#-快速开始--quick-start)
- [各Skill说明 / Skill Details](#-各skill说明--skill-details)
- [项目结构 / Project Structure](#-项目结构--project-structure)
- [技术体系 / Technical Stack](#-技术体系--technical-stack)
- [版本历史 / Version History](#-版本历史--version-history)
- [赞赏 / Support](#-赞赏--support)

---

## 📦 安装 / Installation

### Step 1: 安装 Skill 文件 / Install skill files

<details>
<summary><b>Claude Code / Codex</b></summary>

```bash
# 从 GitHub 安装全部 6 个 skill（缺一不可）
# Install all 6 skills from GitHub (all required)

# 方式1：clone 后手动复制
git clone https://github.com/CNWU16/vedic-astro-skills.git
cp -r vedic-astro-skills/claude-code/skills/vedic-* ~/.codex/skills/
# 或 cp -r vedic-astro-skills/claude-code/skills/vedic-* /Users/$USER/mcc/.codex/skills/

# 方式2：逐个安装（确保 6 个全装）
# --path antigravity/skills/vedic-reader \
# --path antigravity/skills/vedic-calculator \   ← 不要漏掉！
# --path antigravity/skills/vedic-core \
# --path antigravity/skills/vedic-career \
# --path antigravity/skills/vedic-love \
# --path antigravity/skills/vedic-rectifier
```

</details>

<details>
<summary><b>Antigravity</b></summary>

将 `antigravity/skills/` 下的 6 个文件夹复制到你的 Antigravity skills 目录：

Copy all 6 folders from `antigravity/skills/` to your Antigravity skills directory:

```
vedic-reader/
vedic-calculator/    ← 计算基座，必装！/ Required foundation!
vedic-core/
vedic-career/
vedic-love/
vedic-rectifier/
```

</details>

> ⚠️ **必须安装全部 6 个 skill。** vedic-calculator 是计算基座，其他 5 个 skill 都依赖它。漏装 calculator 会导致数据精度严重下降。
>
> **All 6 skills must be installed.** vedic-calculator is the computational foundation. Missing it will severely degrade data accuracy.

### Step 2: 安装 Python 依赖 / Install Python dependencies

| 要求 Requirement | 说明 Details |
|:---|:---|
| **Python** | 3.8 ~ 3.13 （3.14 暂不支持 / not yet supported） |
| **安装 Install** | 运行 `setup_env.py`（见下方 / see below） |

```bash
# 推荐：使用自动安装脚本（处理依赖冲突 + 自动验证）
# Recommended: Use the auto-setup script (handles dependency conflicts + auto-validates)
python vedic-calculator/scripts/setup_env.py

# ⚠️ 不要直接 pip install -r requirements.txt（dashaflow 依赖冲突）
# ⚠️ Do NOT use pip install -r requirements.txt (dependency conflict with dashaflow)
```

> 💡 AI 首次运行时会自动检测环境并运行 `setup_env.py`。但 **请确保系统已安装 Python 3.8~3.13**。
>
> The AI agent will auto-detect and run `setup_env.py` on first use. But **make sure Python 3.8~3.13 is installed on your system**.

---

## 🏛️ 六Skill架构 / Architecture

```
用户星盘 (PDF/截图/文本)          用户出生信息 (日期+时间+地点)
Chart file (PDF/image/text)      Birth info (date+time+place)
    │                                    │
    ▼                                    ▼
┌──────────────┐                ┌───────────────────┐
│ vedic-reader │                │ vedic-calculator   │
│ 提取 + 校验   │                │ 原生排盘引擎        │
│ Extract+Verify│                │ Native calc engine │
└──────┬───────┘                └────────┬──────────┘
       │                                 │
       │     structured_data.md          │
       └────────────┬────────────────────┘
                    ▼
             ┌─────────────┐      ┌────────────────┐
             │ vedic-core   │─────▶│ vedic-rectifier │
             │ P1-P12 审计   │      │ 时间校准 ±5min   │
             │ 宫位诊断      │      │ Time rectify     │
             │ 十大板块总结   │      └────────────────┘
             └──────┬──────┘
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
   ┌──────────────┐    ┌───────────┐
   │ vedic-career  │    │ vedic-love │
   │ 职业蓝图 4Phase│    │ 恋爱时机 3Step│
   │ Career blueprint│  │ Love timing │
   └──────────────┘    └───────────┘
```

| Skill | 功能 Function | 触发词 Trigger |
|:------|:------|:------|
| 🧮 **calculator** | 原生排盘引擎，给出生时间直接计算 / Native chart engine | "直接排盘" "计算星盘" "快速排盘" |
| 📖 **reader** | 从 PDF/截图提取星盘数据 + 16条校验 / Extract from PDF/image | "读盘" "星盘" "印占" "占星" "看盘" |
| 🔬 **core** | P1-P12行星审计 + 宫位诊断 + 十大板块 / Planet audit + life summary | "开始分析" "帮我分析" "星盘审计" |
| 💼 **career** | 4Phase职业蓝图 / Career blueprint | "分析事业" "职业分析" |
| 💘 **love** | 3Step恋爱时机分析 / Love timing analysis | "分析感情" "恋爱运势" "桃花时机" |
| 📐 **rectifier** | 5事件逆推出生时间 ±5min / Birth time rectification | "校准时间" "时间矫正" |

---

## ⚡ 快速开始 / Quick Start

> 💡 **只需说"读盘"或"占星"即可启动。** reader 是统一入口，会根据你提供的内容自动选择最佳路径。
>
> Just say "读盘" or "占星" to start. Reader is the unified entry point and auto-routes based on your input.

### 用法示例 / Usage

```
场景1：只有出生时间
用户: 帮我排盘，1990年3月15日 14:30 北京
 AI: → reader 检测到出生信息 → 自动调用 calculator 排盘
    → 输出 structured_data.md

场景2：有 JHora PDF
用户: [发送PDF] 读盘
 AI: → reader 从 PDF 提取数据 + 16条校验
    → 输出 structured_data.md

场景3：什么都没带
用户: 激活占星
 AI: → reader 弹出引导菜单，让你选择输入方式

后续（任何场景都一样）：
用户: 开始分析      → vedic-core 完整审计
用户: 分析事业      → vedic-career 职业蓝图
用户: 分析感情      → vedic-love 恋爱时机
```

### reader 内部路由 / Internal Routing

```
用户输入
  │
  ├─ 提供了出生时间 ──→ 自动调用 vedic-calculator ──→ structured_data.md
  ├─ 提供了 PDF/截图 ──→ reader 三阶段提取+校验 ──→ structured_data.md
  └─ 什么都没提供   ──→ 弹出引导菜单
```

> ⚠️ 不需要手动选择 skill。**说"占星"就行**——reader 会自动判断。
>
> You don't need to manually choose a skill. Just say "占星" — reader handles routing automatically.

> 💡 **关于 PDF 补充：** calculator 排盘完成后会提示：
> - **a) 直接进入分析**（推荐）— calc 精度 >97%，排序与 JHora 一致，可直接用
> - **b) 发送 JHora PDF 补充** — 可选，用 PDF 中更精确的 Shadbala 值替换
>
> 不补充也完全不影响分析质量。
>
> **About PDF supplement:** After calculator finishes, it offers an optional step to supplement with JHora PDF for marginally more precise Shadbala values. This is entirely optional — calc accuracy is >97%.

---

## 📋 各Skill说明 / Skill Details

### 🧮 vedic-calculator — 精确排盘引擎 / Precision Chart Engine

**v6.1 升级。** engine.py v0.5 — 基于 PyJHora 精确天文算法，fail-fast 架构。

*Updated in v6.1.* engine.py v0.5 — Built on PyJHora's precise astronomical algorithms, fail-fast architecture.

**计算架构 / Calculation Architecture:**

| 模块 Module | 算法来源 Algorithm Source | 说明 Notes |
|:---|:---|:---|
| 行星位置 Positions | pysweph (Swiss Ephemeris) | 天文核心，精度 < 0.01° |
| SAV / BAV | PyJHora 原生 | 12/12 星座完美匹配 JHora |
| Vimsottari Dasha | PyJHora 原生 (`dasha_pyjhora.py`) | ≤2 天偏差（含 1 个 0 天完美匹配）|
| 分盘 Divisional | PyJHora 原生 | 15 张分盘 (D1~D60) |
| Shadbala 六力 | PyJHora + **9 项 bug 修正** (`shadbala_pyjhora.py`) | 修正 Sthana/Kaala/Dig 等子项 |
| Dignity / Jaimini | dashaflow | 查表逻辑，无需修正 |
| Bhava Bala / Lagnas | PyJHora 原生 | 宫位力量 + 特殊 Lagna |

> ⚠️ **为什么 Shadbala 需要修正？** PyJHora 的 SAV/Dasha/分盘模块是正确的，但 Shadbala 的 3 个子项（Sthana/Kaala/Dig）有算法 bug（如 Hora chart method 硬编码错误、Dig Bala 基准点错误等）。`shadbala_pyjhora.py` 在 PyJHora 基础上修正了 9 个子项，使 7 星 rupas 与 JHora 桌面版偏差 < 0.1。
>
> **Why does Shadbala need fixes?** PyJHora's SAV/Dasha/divisional modules are correct, but Shadbala has algorithm bugs in 3 sub-components. `shadbala_pyjhora.py` applies 9 targeted fixes on top of PyJHora's internal functions.

**计算项 / Outputs:**
- 行星位置（经度、星座、Nakshatra）/ Planet positions
- Vimsottari Dasha（大运 + 小运，≤2天精度）/ Dasha periods (≤2 day accuracy)
- Chara Karakas（8K）/ Jaimini Karakas
- 15 张分盘 (D1~D60) / 15 divisional charts
- Shadbala 六力（含 9 项修正 + Ishta/Kashta Phala）/ Six strengths (9 fixes)
- SAV / BAV 吉凶值 / Ashtakavarga
- 尊贵度（Compound Relationship）/ Dignity
- 相位、宫主表 / Aspects, house lords

**精度验证 / Accuracy (tested against JHora, 2 charts):**

| 项目 Item | 结果 Result |
|:---|:---|
| 行星位置 Positions | ✅ 100% 一致 |
| Karakas | ✅ 8/8 |
| D9 Navamsa | ✅ 10/10 |
| Dasha Antardasha | ✅ 9/9 ≤2 天偏差（含 0 天完美匹配）|
| Shadbala Rupas | ✅ 7/7 偏差 < 0.1 rupas (总误差 0.52) |
| SAV 总计 | ✅ 337 (5 星盘验证，3 次重复一致) |

---

### 📖 vedic-reader — 读盘引擎 / Chart Reader

从 PDF/截图/文本中提取星盘数据。三阶段执行引擎，16条数学校验。

Extracts chart data from PDF/image/text. Three-phase execution engine with 16 mathematical validations.

---

### 🔬 vedic-core — 核心分析引擎 / Core Analysis

P1-P12行星逐一审计 → D9交叉验证 → 宫位诊断 → 十大板块人生总结。正反双审防偏见。

Planet-by-planet audit → D9 cross-validation → House diagnosis → Ten life domains. Double-blind audit against bias.

---

### 💼 vedic-career — 职业蓝图 / Career Blueprint

4Phase 分析：生态位 → 格局 → D9确认 → 全维合成。覆盖 D1/D9/D10 三盘。

4-Phase analysis: Ecological niche → Yogas → D9 confirmation → Full synthesis across D1/D9/D10.

---

### 💘 vedic-love — 恋爱时机 / Love Timing

3Step 分析：体质评估 → Dasha窗口 → 性质定性。婚姻三阶段模型（L7确立 → 9宫法律 → 11宫公开）。

3-Step analysis: Constitutional assessment → Dasha windows → Qualitative definition. Three-phase marriage model.

---

### 📐 vedic-rectifier — 时间校准 / Time Rectification

5个人生重大事件逆推出生时间，精度 ±5分钟。不强制改时间——用户确认后才更新。

5 major life events to reverse-engineer birth time to ±5 min accuracy. Never forces a time change.

---

## 📁 项目结构 / Project Structure

```
vedic-astro-skills/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── antigravity/skills/              # Antigravity 版本
│   ├── vedic-calculator/
│   │   ├── SKILL.md                 # 排盘引擎指令
│   │   ├── requirements.txt         # Python 依赖
│   │   └── scripts/
│   │       ├── engine.py            # 主计算引擎 v0.5 (fail-fast)
│   │       ├── setup_env.py         # 环境自动搭建 (10依赖+SAV校验)
│   │       ├── formatter.py         # structured_data 输出
│   │       ├── transit.py           # 过运计算
│   │       ├── dasha_pyjhora.py     # Dasha 精确包装 (≤2天)
│   │       ├── shadbala_pyjhora.py  # Shadbala 修正层 (9项fix)
│   │       ├── divisional_pyjhora.py
│   │       ├── ashtakavarga_pyjhora.py
│   │       ├── extras_pyjhora.py
│   │       └── ephe/                # 星历数据 .se1 (bundled)
│   ├── vedic-reader/
│   │   ├── SKILL.md                 # 读盘引擎
│   │   └── resources/
│   ├── vedic-core/
│   │   ├── SKILL.md                 # 核心分析引擎
│   │   ├── resources/               # 参数/规则/框架
│   │   └── scripts/
│   │       └── report_builder.py    # HTML 报告生成
│   ├── vedic-career/
│   │   └── SKILL.md                 # 职业分析
│   ├── vedic-love/
│   │   └── SKILL.md                 # 恋爱分析
│   └── vedic-rectifier/
│       ├── SKILL.md                 # 时间校准
│       ├── requirements.txt
│       ├── resources/
│       └── scripts/
│           └── time_scan.py         # Lagna/D9 扫描器
└── claude-code/skills/              # Claude Code 版本 (同上)
```

---

## 🧪 技术体系 / Technical Stack

| 项目 Item | 说明 Details |
|:---|:---|
| **流派 School** | KN Rao 体系 (Parashari)，Jaimini 辅助 |
| **Ayanamsa** | TRUE_CITRA / Lahiri |
| **天文核心 Ephemeris** | Swiss Ephemeris via pysweph |
| **精确算法 Algorithms** | PyJHora 4.8.6 (SAV/Dasha/分盘) + 9项Shadbala修正 |
| **分盘 Divisions** | 15 张分盘 D1~D60 (PyJHora) |
| **容错策略 Error Handling** | Fail-fast（不给错误结果）+ `setup_env.py` 自动修复 |
| **校验 Validation** | 16条数学校验（SAV=337、BAV行和常量、Ra-Ke对冲等）|
| **反偏见 Anti-bias** | 正反双审 — 禁止只挑用户想听的数据 |
| **执行引擎 Execution** | 三阶段独立思考链（防超长思考崩溃）|
| **跨平台 Cross-platform** | Windows / macOS / Linux，Python 3.8~3.13 |

---

## 📋 版本历史 / Version History

| 版本 | 日期 | 亮点 |
|:---|:---|:---|
| **v6.1** | 2026-06-08 | 🎯 **PyJHora 精确引擎** — Dasha ≤2天 + Shadbala 9项fix + fail-fast + 无fallback |
| v6.0 | 2026-06-07 | 🧮 vedic-calculator 上线 — 原生排盘引擎 + 移植性改造 + 全系统接入 |
| v5.0 | 2026-05-22 | 三阶段执行引擎 + 动态报告打包 |
| v4.0 | 2026-05-10 | 双通道OCR + 时间精度联动 + Rectifier |
| v3.0 | 2026-05-06 | 五Skill架构确立 + 正反双审 |

详见 / See [CHANGELOG.md](CHANGELOG.md)

---

## ☕ 赞赏 / Support

如果这个项目对你有帮助，欢迎赞赏支持：

If this project helps you, consider buying me a coffee:

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

# Clean-room 原生排盘入口

本文件说明 `scripts/vedic_native_calculator.py` 的使用范围。它是新增的出生信息直算路径，不替代现有的 JHora markdown/PDF 解析链。

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
- 原生脚本生成的 markdown 是检查用摘要；需要机器校验时使用 `structured_data_native.json`。
- Shadbala 暂不由原生脚本计算。需要 Shadbala 时，继续从 JHora PDF/markdown 提取，或等待后续独立公式实现。
- Full MD/AD/PD Vimsottari 暂不由原生脚本计算。月级、日级窗口判断不能用本脚本补造 dasha 精度。

## Clean-room 边界

本入口只复用公开领域规格和公开库 API：Swiss Ephemeris、PyJHora、IANA timezone。不得把其他仓库的 `engine.py`、`ashtakavarga_pyjhora.py`、`dasha_pyjhora.py`、`shadbala_pyjhora.py` 或 `formatter.py` 函数体搬进本仓库。

可以借鉴的是目标 contract：字段要可校验，SAV 总和必须等于 337，BAV 行常量必须匹配，Rahu/Ketu 必须对冲，不能用近似或手写数据制造精确结论。

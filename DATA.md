# 数据说明

> **注意**：`data/` 目录**不进入 Git 仓库**。

## 目录结构

```
data/
├── external/           # 软链接 → 共享币安原始数据目录
│   └── spot/kline/interval=1s/symbol=BTCUSDT/...
└── raw/                # 原始数据（从 external 复制/解压到本地）
    └── *.csv
```

共享原始数据通过软链接挂载：

```
data/external -> <共享存储>/quant-fund/raw/crypto/binance
```

---

## 原始数据

### 来源

**共享数据目录**：`data/external/spot/kline/`

数据由独立服务统一拉取并存放于共享存储，`data/external` 为指向该存储的软链接。**不需要在本项目内重复拉取**。

### 数据组织方式

| 维度 | 说明 |
|------|------|
| 市场 | Binance Spot（现货） |
| K线周期 | 1秒（`1s`） |
| 交易对 | BTCUSDT、ETHUSDT、SOLUSDT、XRPUSDT |
| 存储格式 | 每日一个 ZIP 压缩包 |
| 文件命名 | `<SYMBOL>-1s-<YYYY-MM-DD>.zip` |
| 日期范围 | 约 2023-01-01 至今 |
| 每日条数 | 约 86,400 条（每秒一条） |
| 校验文件 | 每个 ZIP 附带 `.CHECKSUM` |

### CSV 字段说明

解压后 CSV 为 Binance 标准 K 线格式（12 列，无表头）：

| 列号 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0 | `open_time` | int64 | 开盘时间，毫秒时间戳 |
| 1 | `open` | float | 开盘价 |
| 2 | `high` | float | 最高价 |
| 3 | `low` | float | 最低价 |
| 4 | `close` | float | 收盘价 |
| 5 | `volume` | float | 成交量 |
| 6 | `close_time` | int64 | 收盘时间，毫秒时间戳 |
| 7 | `quote_volume` | float | 成交额 |
| 8 | `trade_count` | int | 成交笔数 |
| 9 | `taker_buy_base_volume` | float | 主动买入成交量 |
| 10 | `taker_buy_quote_volume` | float | 主动买入成交额 |
| 11 | `ignore` | int | 忽略字段 |

### 使用方式

将需要的日期数据从共享目录解压到本地：

```bash
mkdir -p data/raw

# 示例：复制并解压 BTC 某一天的数据
cp data/external/spot/kline/interval=1s/symbol=BTCUSDT/date=2026-02-02/BTCUSDT-1s-2026-02-02.zip data/raw/
unzip -o data/raw/BTCUSDT-1s-2026-02-02.zip -d data/raw/
```

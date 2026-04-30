#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import argparse
from typing import Any

import pandas as pd
import akshare as ak

TEMPLATE_MD = """# 当前持仓状态
请在此表格中更新您的最新持仓数据（份额、净值、可用资金等）。

| 标的代码 | 名称           | 当前持有份额 | 最新净值 | 可用资金 |
| -------- | -------------- | ------------ | -------- | -------- |
| 513630   | 港股通红利ETF  | 10000        | 1.050    | 50000    |
| 515180   | 易方达红利ETF  | 10000        | 1.200    | 0        |
| 513500   | 标普500ETF     | 10000        | 1.500    | 0        |
| 159929   | 医药ETF        | 5000         | 1.100    | 0        |

注：本脚本会自动解析 Markdown 表格，请保持表头名称一致。
"""

# ================= 配置参数 =================
TARGET_RATIO: dict[str, float] = {
    '513630': 0.3, # 港股低波红利
    '515180': 0.3, # 易方达红利
    '513500': 0.4  # 标普500
}
MOMENTUM_POOL: list[str] = ['159929', '159530', '513630', '513010', '513500', '159941']
INDEX_POOL: dict[str, str] = {
    'sh000001': '上证指数',
    'sh000300': '沪深300'
}
EXTREME_VALUATION_THRESHOLD: float = -0.06
MOMENTUM_INVEST_AMOUNT: int = 30000
EXTREME_INVEST_AMOUNT: int = 120000

MD_FILE: str = 'current_portfolio.md'
LOG_FILE: str = 'position_changes_log.md'
STATE_FILE: str = '.last_portfolio_state.json'
# ============================================

def fetch_momentum_data(quiet: bool = False) -> list[dict[str, Any]]:
    if not quiet:
        print("\n[*] 正在扫描动量 ETF 候选池...")
    today = datetime.datetime.now()
    # 扩大获取范围以确保能拿到至少20个交易日
    start_date = (today - datetime.timedelta(days=60)).strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")

    stats: list[dict[str, Any]] = []
    for code in MOMENTUM_POOL:
        try:
            df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
            if len(df) >= 20:
                recent_close = float(df['收盘'].iloc[-1])
                old_close = float(df['收盘'].iloc[-20])
                ret = (recent_close - old_close) / old_close
                stats.append({'code': code, 'return': ret})
        except Exception as e:
            print(f"[!] 获取 ETF {code} 历史数据失败: {e}", flush=True)

    stats = sorted(stats, key=lambda x: x['return'], reverse=True)
    return stats

def fetch_index_radar(quiet: bool = False) -> list[dict[str, Any]]:
    if not quiet:
        print("[*] 正在扫描均值回归雷达 (MA120)...")
    stats: list[dict[str, Any]] = []
    for code, name in INDEX_POOL.items():
        try:
            df = ak.stock_zh_index_daily_em(symbol=code)
            if len(df) >= 120:
                df['ma120'] = df['close'].rolling(window=120).mean()
                latest_close = float(df['close'].iloc[-1])
                ma120 = float(df['ma120'].iloc[-1])
                dist = (latest_close - ma120) / ma120
                trigger = dist < EXTREME_VALUATION_THRESHOLD
                stats.append({
                    'code': code,
                    'name': name,
                    'dist': dist,
                    'trigger': trigger,
                    'close': latest_close,
                    'ma120': ma120
                })
        except Exception as e:
            print(f"[!] 获取指数 {code} 历史数据失败: {e}", flush=True)
    return stats

def parse_md_table(filepath: str) -> pd.DataFrame | None:
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    table_lines: list[str] = []
    in_table = False
    for line in lines:
        if '|' in line and '标的代码' in line:
            in_table = True
            table_lines.append(line.strip())
            continue
        if in_table:
            # 遇到空行或不再是带有 | 的行为表格结束
            if not line.strip() or not line.strip().startswith('|'):
                if '|' not in line:
                    break
            if '|' in line:
                table_lines.append(line.strip())

    if not table_lines:
        return None

    cleaned: list[list[str]] = []
    for line in table_lines:
        line = line.strip()
        if line.startswith('|'): line = line[1:]
        if line.endswith('|'): line = line[:-1]
        cleaned.append([c.strip() for c in line.split('|')])

    header = cleaned[0]
    data = cleaned[2:] # 跳过分割线 (---|---)
    df = pd.DataFrame(data, columns=header)
    return df

def check_state_changes(current_df: pd.DataFrame) -> None:
    current_state: dict[str, float] = {}
    for _, row in current_df.iterrows():
        code = str(row.get('标的代码', '')).strip()
        try:
            shares = float(row.get('当前持有份额', 0))
        except (ValueError, TypeError):
            shares = 0.0

        if code:
            current_state[code] = shares

    last_state: dict[str, float] = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            last_state = json.load(f)

    changes: list[str] = []
    all_codes = set(current_state.keys()).union(set(last_state.keys()))
    for code in all_codes:
        curr = current_state.get(code, 0)
        last = last_state.get(code, 0)
        diff = curr - last
        if diff != 0:
            verb = "增加" if diff > 0 else "减少"
            changes.append(f"{code} 份额{verb} {abs(diff):.2f} 份")

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_state, f)

    if changes:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n### {timestamp}\n")
            for c in changes:
                f.write(f"- {c}\n")
        print(f"\n[*] 检测到仓位变动，已将状态变动差异履历写入 ({LOG_FILE})：")
        for c in changes:
            print(f"  -> {c}")
    else:
         print("\n[*] 较上次状态快照核对完毕，持平无变化。")

def analyze_portfolio(df: pd.DataFrame, momentum_top_code: str | None, indices_status: list[dict[str, Any]]) -> None:
    print("\n" + "="*50)
    print("【深 度 持 仓 分 析 与 辅 助 决 策】")
    print("="*50)

    total_target_value: float = 0
    actual_values: dict[str, float] = {}
    for _, row in df.iterrows():
        code = str(row.get('标的代码', '')).strip()
        if code in TARGET_RATIO:
            try:
                shares = float(row.get('当前持有份额', 0))
                nav = float(row.get('最新净值', 0))
                val = shares * nav
                actual_values[code] = val
                total_target_value += val
            except (ValueError, TypeError):
                pass

    print("\n[1. 仓位偏离度纠偏分析]")
    rebalance_needed = False
    action_items: list[str] = []

    if total_target_value > 0:
        for code, target_pct in TARGET_RATIO.items():
            actual_val = actual_values.get(code, 0)
            actual_pct = actual_val / total_target_value if total_target_value else 0
            diff = actual_pct - target_pct

            print(f" - {code}: 目标权重 {target_pct*100:.1f}% | 实际 {actual_pct*100:.1f}% | 偏差 {diff*100:+.1f}%")
            if abs(diff) > 0.05:
                rebalance_needed = True
                if diff > 0:
                    action_items.append(f"标的 {code} 仓位结构已超标，建议近期挂起该标的定投，将主粮资金倾斜分流至其他底仓。")
                else:
                    action_items.append(f"标的 {code} 仓位结构不足偏低，建议在下次定投触发时执行单边倾斜补仓！")

        if not rebalance_needed:
            print(" -> 评级结论：底仓架构配比极其健康稳定，无需再平衡。")
            action_items.append("现行底仓阵型比例稳固，无需发起纠偏再平衡指令。")
    else:
         print(f" -> 未在 Markdown 持仓表中嗅探到目标底仓({'/'.join(TARGET_RATIO.keys())})的市值数据流，偏差矩阵拒绝计算。")

    print("\n[2. 风险阈值与宏观预警信号感知]")
    triggered_indices = [idx['name'] for idx in indices_status if idx['trigger']]
    if triggered_indices:
        print(f" -> [高危预警]：大盘波动跌穿阈值极限！重点预警：{', '.join(triggered_indices)} 近期跌落超 MA120 线 6% ！盘面已正式滑入机构派发的高胜率左侧深水大击球区！")
    else:
        print(" -> [平流层提示]：核心宽基指数网带健康平滑，全线均未击穿系统设定的崩溃抄底防线。在此背景下建议恪守绝对纪律跑完标准动量定投，严禁任何主观操作带来的单次超限违规重仓。")

    print("\n[3. M78-Alpha : 最终行动执行序列清单]")
    idx = 1
    if momentum_top_code:
        print(f" {idx}. 执行挂单：立刻买入总额 {MOMENTUM_INVEST_AMOUNT} 元代号 {momentum_top_code} (这是本月轮动捕获到的绝对动量冠军标的)；")
        idx += 1

    for action in action_items:
         print(f" {idx}. {action}")
         idx += 1

    for id_stat in indices_status:
         if id_stat['trigger']:
             print(f" {idx}. -> 强行介入：由于触发左侧破净极端信号指令，本系统特别许可并建议对 {id_stat['name']} 关联宽基标的一把推入 {EXTREME_INVEST_AMOUNT} 元，做断头侧抄底防守；")
             idx += 1

    if not triggered_indices:
         print(f" {idx}. -> 巡检闭环：各中枢 MA120 未发极端信号，请继续持有流动大营预置重仓现金流。")
    print("="*50 + "\n")

def stage_pre_check() -> None:
    # 检测并初始化 MD_FILE
    is_new = False
    if not os.path.exists(MD_FILE):
        with open(MD_FILE, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE_MD)
        is_new = True

    print("\n【阶段 1：首轮启动 - 宏观全景态势报告】")
    momentum_stats = fetch_momentum_data()
    top_1_code = None
    if momentum_stats:
        print(f"\n[动量雷达侦测] 上个阶段涨跌幅排位榜前三甲：")
        for i, s in enumerate(momentum_stats[:3]):
            print(f" Top {i+1}: 代号 {s['code']} 滚动录得 {s['return']*100:.2f}% 收益率")
        top_1_code = momentum_stats[0]['code']
        print(f" -> 首检判决项：针对本自然月度 {MOMENTUM_INVEST_AMOUNT} 元的动量专项定额定投发力点，唯一锁定到 【{top_1_code}】")

    indices_stats = fetch_index_radar()
    if indices_stats:
        print(f"\n[估值塌陷雷达侦测]：")
        for s in indices_stats:
            gap = s['dist'] - EXTREME_VALUATION_THRESHOLD
            if gap > 0:
                print(f" - 大盘 {s['name']} 指数：未跌入信号区，距极端回撤抄底线索差距还有 {gap*100:.2f}% (水位计读数相对 MA120 为 {s['dist']*100:+.2f}%)")
            else:
                print(f" - 大盘 {s['name']} 指数：🔴 系统击穿！已沉没到 MA120 超卖区域极端信号！(水位计读数相对 MA120 为 {s['dist']*100:+.2f}%)，警报发酵。")

    print("\n[配置环境检查]：")
    print(f" -> 关联的底层持仓面板文件 `{MD_FILE}` 就绪。")
    if is_new:
        print("\n=== 初始化持仓模版内容如下 ===")
        print(TEMPLATE_MD)
        print("==============================\n")
        print("[环境安装提示]：系统已由于初次运行为您建立好了默认的 current_portfolio.md 持仓面板。\n请打开该文件并填装您的真实仓位信息；如果您选择不填写，系统计算引擎将以此默认值作为基础投入数据流直接执行测算。")

def stage_analyze() -> None:
    print("\n【阶段 2：Markdown 快照比查与深度解析】")
    df = parse_md_table(MD_FILE)
    if df is None or df.empty:
        print(f"[!] 错误终止：根本就无法识别目录树里包含 {MD_FILE} 在内的物理表格数据。")
        print("[注解引导]：由于缺少基础材料，请回看主程序代码中的注释范本创建一个标准的 Markdown 多维表。")
        return

    check_state_changes(df)

    # 静默在内存中复刻环境
    momentum_stats = fetch_momentum_data(quiet=True)
    top_1_code = momentum_stats[0]['code'] if momentum_stats else None
    indices_stats = fetch_index_radar(quiet=True)

    # 把参数推上手术台
    analyze_portfolio(df, top_1_code, indices_stats)

def main() -> None:
    parser = argparse.ArgumentParser(description="ETF M78-Alpha Agent Local Engine")
    parser.add_argument('--stage', choices=['pre-check', 'analyze', 'all'], default='all', help='指定要运行在流水线中的具体执行阶段')
    args = parser.parse_args()

    print("="*50)
    print("      ETF M78-Alpha 决策中心代理底层核心驱动")
    print("="*50)

    if args.stage in ['pre-check', 'all']:
        stage_pre_check()

    if args.stage in ['analyze', 'all']:
        stage_analyze()

if __name__ == "__main__":
    main()

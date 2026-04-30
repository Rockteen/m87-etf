"""Tests for ETF M78-Alpha decision engine."""

import io
import json
import os
import tempfile
from unittest import mock

import pandas as pd
import pytest

import sk_etf_m78 as engine


# ---------------------------------------------------------------------------
# parse_md_table / _extract_table_text
# ---------------------------------------------------------------------------

VALID_TABLE = """# Some header text

| 标的代码 | 名称           | 当前持有份额 | 最新净值 | 可用资金 |
| -------- | -------------- | ------------ | -------- | -------- |
| 513630   | 港股通红利ETF  | 10000        | 1.050    | 50000    |
| 515180   | 易方达红利ETF  | 10000        | 1.200    | 0        |

Some footer text.
"""


def test_extract_table_text_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(VALID_TABLE)
        tmp = f.name
    try:
        text = engine._extract_table_text(tmp)
        assert text is not None
        assert '标的代码' in text
        assert '513630' in text
        assert 'Some footer text' not in text
    finally:
        os.unlink(tmp)


def test_extract_table_text_missing_file():
    assert engine._extract_table_text('/nonexistent/path.md') is None


def test_parse_md_table_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(VALID_TABLE)
        tmp = f.name
    try:
        df = engine.parse_md_table(tmp)
        assert df is not None
        assert len(df) == 2
        assert '标的代码' in df.columns
        assert df.iloc[0]['标的代码'] == '513630'
        assert df.iloc[1]['标的代码'] == '515180'
    finally:
        os.unlink(tmp)


def test_parse_md_table_no_table():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write('Just some text, no table here.')
        tmp = f.name
    try:
        df = engine.parse_md_table(tmp)
        assert df is None
    finally:
        os.unlink(tmp)


def test_parse_md_table_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write('')
        tmp = f.name
    try:
        df = engine.parse_md_table(tmp)
        assert df is None
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# analyze_portfolio
# ---------------------------------------------------------------------------

def _make_portfolio_df(rows: list[dict]) -> pd.DataFrame:
    """Helper: build a DataFrame matching the Markdown table schema."""
    return pd.DataFrame(rows)


def test_analyze_portfolio_balanced(monkeypatch, capsys):
    """When actual weights match targets, no rebalance action is triggered."""
    # Override config for deterministic test
    monkeypatch.setattr(engine, 'TARGET_RATIO', {'513630': 0.5, '515180': 0.5})
    monkeypatch.setattr(engine, 'MOMENTUM_INVEST_AMOUNT', 30000)
    monkeypatch.setattr(engine, 'EXTREME_INVEST_AMOUNT', 120000)

    df = _make_portfolio_df([
        {'标的代码': '513630', '名称': '港股通红利', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
        {'标的代码': '515180', '名称': '易方达红利', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
    ])
    indices: list[dict] = []  # no index triggers
    engine.analyze_portfolio(df, '513630', indices)

    captured = capsys.readouterr().out
    assert '无需再平衡' in captured


def test_analyze_portfolio_needs_rebalance(monkeypatch, capsys):
    """When one fund is overweight, a rebalance warning is emitted."""
    monkeypatch.setattr(engine, 'TARGET_RATIO', {'513630': 0.5, '515180': 0.5})
    monkeypatch.setattr(engine, 'MOMENTUM_INVEST_AMOUNT', 30000)
    monkeypatch.setattr(engine, 'EXTREME_INVEST_AMOUNT', 120000)

    # 513630 is 4x the value of 515180 → heavy imbalance
    df = _make_portfolio_df([
        {'标的代码': '513630', '名称': '港股通红利', '当前持有份额': '40000', '最新净值': '1.0', '可用资金': '0'},
        {'标的代码': '515180', '名称': '易方达红利', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
    ])
    engine.analyze_portfolio(df, None, [])

    captured = capsys.readouterr().out
    assert '仓位结构已超标' in captured


def test_analyze_portfolio_no_target_funds(monkeypatch, capsys):
    """When no target fund codes are present, should show error message."""
    monkeypatch.setattr(engine, 'TARGET_RATIO', {'513630': 0.5, '515180': 0.5})
    monkeypatch.setattr(engine, 'MOMENTUM_INVEST_AMOUNT', 30000)
    monkeypatch.setattr(engine, 'EXTREME_INVEST_AMOUNT', 120000)

    df = _make_portfolio_df([
        {'标的代码': '159929', '名称': '医药ETF', '当前持有份额': '5000', '最新净值': '1.0', '可用资金': '0'},
    ])
    engine.analyze_portfolio(df, None, [])

    captured = capsys.readouterr().out
    assert '偏差矩阵拒绝计算' in captured


def test_analyze_portfolio_extreme_trigger(monkeypatch, capsys):
    """When an index triggers the extreme valuation threshold, action is printed."""
    monkeypatch.setattr(engine, 'TARGET_RATIO', {'513630': 1.0})
    monkeypatch.setattr(engine, 'EXTREME_INVEST_AMOUNT', 120000)

    df = _make_portfolio_df([
        {'标的代码': '513630', '名称': '港股通红利', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
    ])
    indices = [{'name': '沪深300', 'trigger': True, 'code': 'sh000300', 'dist': -0.08}]
    engine.analyze_portfolio(df, None, indices)

    captured = capsys.readouterr().out
    assert '强行介入' in captured
    assert '120000' in captured


# ---------------------------------------------------------------------------
# _load_config
# ---------------------------------------------------------------------------

def test_load_config_defaults(monkeypatch):
    """Without a config file present, defaults should be used."""
    monkeypatch.setattr(engine, '_CONFIG_FILE', '/nonexistent_config.yaml')
    cfg = engine._load_config()
    assert cfg == {}
    assert engine.TARGET_RATIO == engine._DEFAULT_TARGET_RATIO


def test_load_config_with_yaml(monkeypatch, tmp_path):
    """When config.yaml exists, values are read from it."""
    config_path = tmp_path / 'config.yaml'
    config_path.write_text("""
target_ratio:
  "000001": 1.0
momentum_invest_amount: 99999
""", encoding='utf-8')
    monkeypatch.setattr(engine, '_CONFIG_FILE', str(config_path))
    monkeypatch.setattr(engine, '_HAS_YAML', True)

    cfg = engine._load_config()
    assert cfg['target_ratio'] == {'000001': 1.0}
    assert cfg['momentum_invest_amount'] == 99999


# ---------------------------------------------------------------------------
# check_state_changes
# ---------------------------------------------------------------------------

def test_check_state_changes_no_previous_state(monkeypatch, capsys, tmp_path):
    """First run: no previous state file → all rows are counted as additions."""
    state_file = tmp_path / '.test_state.json'
    log_file = tmp_path / 'test_log.md'
    monkeypatch.setattr(engine, 'STATE_FILE', str(state_file))
    monkeypatch.setattr(engine, 'LOG_FILE', str(log_file))

    df = _make_portfolio_df([
        {'标的代码': '513630', '名称': 'X', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
    ])
    engine.check_state_changes(df)

    captured = capsys.readouterr().out
    assert '检测到仓位变动' in captured
    assert os.path.exists(str(state_file))


def test_check_state_changes_unchanged(monkeypatch, capsys, tmp_path):
    """When the state hasn't changed, no changes are reported."""
    state_file = tmp_path / '.test_state.json'
    log_file = tmp_path / 'test_log.md'
    # Pre-seed state
    state_file.write_text(json.dumps({'513630': 10000.0}), encoding='utf-8')
    monkeypatch.setattr(engine, 'STATE_FILE', str(state_file))
    monkeypatch.setattr(engine, 'LOG_FILE', str(log_file))

    df = _make_portfolio_df([
        {'标的代码': '513630', '名称': 'X', '当前持有份额': '10000', '最新净值': '1.0', '可用资金': '0'},
    ])
    engine.check_state_changes(df)

    captured = capsys.readouterr().out
    assert '持平无变化' in captured


# ---------------------------------------------------------------------------
# _retry decorator
# ---------------------------------------------------------------------------

def test_retry_success_first_attempt():
    call_count = 0

    @engine._retry(max_retries=2, base_delay=0.0)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        return 'ok'

    result = flaky_func()
    assert result == 'ok'
    assert call_count == 1


def test_retry_eventual_success():
    call_count = 0

    @engine._retry(max_retries=2, base_delay=0.0)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError('transient error')
        return 'ok'

    result = flaky_func()
    assert result == 'ok'
    assert call_count == 3


def test_retry_exhausted():
    call_count = 0

    @engine._retry(max_retries=1, base_delay=0.0)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise RuntimeError('persistent error')

    with pytest.raises(RuntimeError):
        always_fails()
    assert call_count == 2  # initial + 1 retry


# ---------------------------------------------------------------------------
# _session_cache
# ---------------------------------------------------------------------------

def test_session_cache_caches_results():
    call_count = 0

    @engine._session_cache
    def expensive(arg):
        nonlocal call_count
        call_count += 1
        return arg * 2

    assert expensive(5) == 10
    assert expensive(5) == 10  # cached
    assert call_count == 1
    assert expensive(10) == 20  # different arg, not cached
    assert call_count == 2

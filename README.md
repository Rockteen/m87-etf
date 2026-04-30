# ETF M78-Alpha (Agent Skill)

ETF M78-Alpha 是一个面向 AI Agent 的量化投资决策辅助技能，基于"奥特之父"策略体系：
右侧动量定投 + 左侧极端估值抄底 + 底仓比例再平衡。

---

## 一键安装 (One-Liner)

```bash
mkdir -p ~/.gemini/antigravity/skills/etf-m78-alpha && curl -o ~/.gemini/antigravity/skills/etf-m78-alpha/SKILL.md https://raw.githubusercontent.com/Rockteen/m87-etf/main/SKILL.md && curl -o ~/.gemini/antigravity/skills/etf-m78-alpha/sk_etf_m78.py https://raw.githubusercontent.com/Rockteen/m87-etf/main/sk_etf_m78.py && curl -o ~/.gemini/antigravity/skills/etf-m78-alpha/config.yaml https://raw.githubusercontent.com/Rockteen/m87-etf/main/config.yaml && pip install pandas akshare pyyaml
```

若使用其他 Agent 平台（如 Claude Code），请将 `~/.gemini/antigravity/skills/` 替换为对应技能目录。

### 安装内容

1. **SKILL.md** — Agent 执行行为规范
2. **sk_etf_m78.py** — Python 计算引擎
3. **config.yaml** — 策略参数配置文件
4. 自动安装依赖: `pandas`, `akshare`, `pyyaml`

安装完成后，当用户说"帮我体检ETF"、"使用M78"、"这月定投买什么"时，Agent 会自动按规范执行。

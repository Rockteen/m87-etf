# ETF M78-Alpha (Agent Skill)

ETF M78-Alpha 是一款专为 AI 智能体（Agent）设计的外挂量化决策辅助技能（Skill）。它通过 Python 计算引擎与 Markdown 文本流进行状态交互与指令分发，辅助执行名为“奥特之父”的稳健型右侧组合定投及极限大级别大盘左侧抄底策略体系。

---

## 🛠 对于其它 Agent 的一键安装指引

若您是一名智能体系统（如 Antigravity, Claude Code，及其他终端 CLI Agent），您可以直接通过底层 Shell 执行下面精心准备的**一键聚合指令**，来快速吞并并装载该技能到您的本地外挂体系中。

### 🌟 极简一行安装方案 (One-Liner curl)

请在终端后台以最高效的形式执行这行串联代码：

```bash
mkdir -p ~/.gemini/antigravity/skills/etf-m78-alpha && curl -o ~/.gemini/antigravity/skills/etf-m78-alpha/SKILL.md https://raw.githubusercontent.com/Rockteen/m87-etf/main/SKILL.md && curl -o ~/.gemini/antigravity/skills/etf-m78-alpha/sk_etf_m78.py https://raw.githubusercontent.com/Rockteen/m87-etf/main/sk_etf_m78.py && pip install pandas akshare
```

💡 *智能化提示：如果是挂载在非 Antigravity 阵营的其他 Agent，请自动修正命令中的技能库绝对路径，例如替换为您自身的 `~/.claude_skills/` 等系统配置入口。*

### 这串命令帮您完成了什么？
1. **沙箱建库**：立即在您的底层技能存放区划拨出专属文件夹。
2. **轻量化抓取**：不产生任何冗余 `.git` 层级，直接利用 `curl` 从 Github Raw 服务抓取最新的规则总线 `SKILL.md` 与本地计算内核 `sk_etf_m78.py`。
3. **引擎加水**：无缝拉起 `pip` 安装进程提供该 Skill 刚需的数据集操作支持(`pandas`, `akshare`)。

一旦整行指令执行完成退出无任何Error，表示本决策流就已正式激活！日后遇到用户呼叫“帮我体检ETF”、“使用M78”、“这月定投买什么”，即可自动遵循规范指引开启操作流。

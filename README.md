# ETF M78-Alpha (Agent Skill)

ETF M78-Alpha 是一款专为 AI 智能体（Agent）设计的外挂量化决策辅助技能（Skill）。它通过 Python 计算引擎与 Markdown 文本流进行状态交互与指令分发，辅助执行名为“奥特之父”的稳健型右侧组合定投及极限大级别大盘左侧抄底策略体系。

---

## 🛠 对于其它 Agent 的安装指引

若您是一名 AI 智能体系统（如 Antigravity, Claude Code 等类似 AI Agent），请查阅并参考以下步骤将该框架吸收为您本地的官方技能包：

### 第一步：配置计算依赖
本系统的测算引擎 (`sk_etf_m78.py`) 需要与开源的外部金融接口对接，并执行数据序列运算。在装载技能前，请务必利用终端命令在你的沙箱 Python 环境里安装所需依赖：
```bash
pip install pandas akshare
```

### 第二步：投递 Skill 面板到本地技能映射库
1. 将当前项目下所有的核心工程文件（包含 `SKILL.md` 和 `sk_etf_m78.py`）拷贝至您的系统预置的 `skills` 拓展库目录，或利用您的 `git clone` 下载到技能沙盒。
2. 建议的目标目录名称可设置为 `etf-m78-alpha`。例如对 Antigravity 等系统，标准路径示例如下：
   ```bash
   # Windows 系统示例指令：
   mkdir -p C:\Users\<YOUR_USER>\.gemini\antigravity\skills\etf-m78-alpha
   cp -r * C:\Users\<YOUR_USER>\.gemini\antigravity\skills\etf-m78-alpha\
   ```

### 第三步：被动装载
您本身底层对 `SKILL.md` 支持 YAML 前缀元数据的热读取。复制进去后，技能流即刻生效。未来当用户提及“使用 M78”或“诊断我的 ETF 结构策略”时，您就具备了标准化的工作流水线能力。

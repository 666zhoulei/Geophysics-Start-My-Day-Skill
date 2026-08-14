# Geophysics Start My Day Skill

面向地球物理学的 Codex skills 套件。它检索地震勘探与智能地球物理论文，将每日 10 篇开放 PDF 保存到 Obsidian，并生成可直接点击本地原文的中文推荐笔记。


## 功能

- 从 arXiv 检索最近论文，并可用 Semantic Scholar 补充近一年热门论文。
- 重点覆盖去混采、去噪与重建、时频/速度分析、波场模拟、成像反演、PINN 与地震深度学习。
- 根据相关性、新近性、热门度和摘要质量排序。
- 强制保存 10 篇本地 PDF；不可下载的候选会按排名顺延补位。
- 在 Obsidian 中使用 `[[本地文件名.pdf|PDF]]`，点击即可打开原文。
- 自动为前三篇生成详细分析并提取论文图片。
- 扫描已有笔记，避免重复并建立研究图谱。
- 已修正宽泛分类误筛选：`cs.LG`、`eess.IV`、`eess.SP` 不能在没有地球物理关键词时单独使论文入选。

## 仓库结构

```text
geophysics-start-my-day-skill/
├─ skills/
│  ├─ start-my-day/
│  ├─ paper-analyze/
│  └─ extract-paper-images/
├─ tests/
├─ config.example.yaml
├─ requirements.txt
├─ LICENSE
├─ ACKNOWLEDGEMENTS.md
└─ README.md
```

三个 skill 应一起安装。`start-my-day` 使用另外两个 skill 完成前三篇论文的深度分析和图片提取。

## 环境要求

- Python 3.10+
- OpenAI Codex Desktop/CLI 或其他支持 `SKILL.md` 的 agent
- Obsidian Vault
- 可访问 arXiv；Semantic Scholar 为可选增强来源

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

Windows 中文环境建议设置：

```powershell
[Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'User')
```

## 安装到 Codex

### Windows PowerShell

```powershell
$skills = Join-Path $env:USERPROFILE '.codex\skills'
Copy-Item -Recurse '.\skills\start-my-day' $skills
Copy-Item -Recurse '.\skills\paper-analyze' $skills
Copy-Item -Recurse '.\skills\extract-paper-images' $skills
```

### macOS/Linux

```bash
cp -r skills/start-my-day ~/.codex/skills/
cp -r skills/paper-analyze ~/.codex/skills/
cp -r skills/extract-paper-images ~/.codex/skills/
```

重新开启一个 Codex 对话，使新 skill 被发现。

## 配置 Obsidian

1. 在 Vault 中创建：

```text
Obsidian Vault/
├─ 10_Daily/
├─ 20_Research/Papers/
└─ 99_System/Config/
```

2. 将 `config.example.yaml` 复制为：

```text
<Vault>/99_System/Config/research_interests.yaml
```

3. 修改其中的 `vault_path`、关键词、优先级与期刊。

4. 设置 Vault 环境变量：

```powershell
[Environment]::SetEnvironmentVariable(
  'OBSIDIAN_VAULT_PATH',
  'C:\Users\your-name\Documents\Obsidian Vault',
  'User'
)
```

macOS/Linux：

```bash
export OBSIDIAN_VAULT_PATH="$HOME/Documents/Obsidian Vault"
```

不要把真实 API Key 提交到 GitHub。公开仓库只保留空的 `semantic_scholar_api_key`。

## 使用

在 Codex 中输入：

```text
使用 $start-my-day 生成今天的论文推荐
```

指定日期：

```text
使用 $start-my-day 生成 2026-08-13 的论文推荐
```

完成后将得到：

```text
Obsidian Vault/
├─ 10_Daily/YYYY-MM-DD论文推荐.md
├─ 20_Research/Papers/*.pdf
├─ 20_Research/Papers/<领域>/*.md
└─ 20_Research/PaperGraph/graph_data.json
```

## 评分与数据来源

普通推荐分由相关性、新近性、热门度和摘要质量组合。`physics.geo-ph` 可作为强领域证据；`eess.SP`、`eess.IV`、`cs.LG` 等跨领域分类只用于增强已有关键词匹配，防止医学影像、食品光谱等论文混入地球物理推荐。

Semantic Scholar 的匿名 API 可能返回 `429 Too Many Requests`。发生限流时，skill 会降级使用 arXiv 结果。可在本地配置 API Key，但不要提交密钥。

## 测试

```powershell
$env:PYTHONUTF8 = '1'
python -m unittest discover -s tests -v
```

校验单个 skill：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/start-my-day
```

## 隐私与版权

- PDF 只保存到用户自己的 Obsidian Vault，不应提交到 GitHub。
- 仅下载 arXiv 或元数据服务明确提供的开放 PDF；不绕过登录、付费墙或访问控制。
- Zotero 馆藏只用于推断研究兴趣，不随本仓库发布。
- 本发布包使用 MIT License。原始源码快照未携带上游 URL 与作者版权信息，因此保留原项目名称并在致谢中如实说明；获得权威上游信息后应补充并持续保留。

## 致谢

本项目改造自 `evil-read-arxiv` skills 集合，并使用 arXiv、Semantic Scholar、Obsidian、OpenAI Codex、PyMuPDF 和 Zotero 相关能力。完整说明见 [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)。

## License

[MIT License](LICENSE)
# Geophysics-Start-My-Day-Skill

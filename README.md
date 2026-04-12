# 服务状态监控面板

基于 GitHub Actions + GitHub Pages 的轻量级服务可用性监控方案。

## 工作原理

```
GitHub Actions (每5分钟)
    └── 运行 scripts/check.py
          └── 探测 config.yml 中所有服务
                └── 写入 data/status.json
                      └── push 到仓库
                            └── GitHub Pages 提供前端展示
```

## 快速部署

### 1. 创建仓库

在 GitHub 上新建一个 **公开** 仓库（例如 `my-status`），然后把本项目的所有文件推送上去：

```bash
git init
git add .
git commit -m "init: status monitor"
git branch -M main
git remote add origin https://github.com/<你的用户名>/my-status.git
git push -u origin main
```

### 2. 开启 GitHub Pages

进入仓库 → **Settings** → **Pages**  
Source 选择 `Deploy from a branch`，Branch 选 `main`，目录选 `/ (root)`  
保存后等约1分钟，访问 `https://<用户名>.github.io/my-status/` 即可看到面板。

### 3. 配置监控服务

编辑 `config.yml`，填入你自己的服务地址：

```yaml
services:
  - name: "主站"
    url: "https://your-site.com"
    expected_status: 200
    timeout: 10

  - name: "API"
    url: "https://api.your-site.com/health"
    expected_status: 200
    expected_text: "ok"   # 可选：验证响应体包含此字符串
    timeout: 10
```

字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 显示名称 |
| `url` | ✅ | 探测地址（需公网可访问） |
| `expected_status` | 否 | 期望的 HTTP 状态码，默认 200 |
| `expected_text` | 否 | 期望响应体包含的字符串（不区分大小写） |
| `timeout` | 否 | 超时秒数，默认 10 |

### 4. 触发第一次检测

推送代码后，进入仓库 → **Actions** → **Service Monitor** → **Run workflow**  
手动触发一次，确认 `data/status.json` 被正确生成。

之后 GitHub Actions 会每5分钟自动运行。

## 文件结构

```
.
├── .github/
│   └── workflows/
│       └── monitor.yml     # Actions 定时任务
├── data/
│   ├── status.json         # 最新状态（自动生成，勿手动编辑）
│   └── history.json        # 历史记录（自动生成）
├── scripts/
│   └── check.py            # 探测逻辑
├── config.yml              # ← 你只需要改这个文件
└── index.html              # 前端面板
```

## 注意事项

- GitHub Actions 免费额度：公开仓库**无限制**；私有仓库每月2000分钟（每次运行约10秒，10分钟间隔每月约 ~4320 次，约 720 分钟，完全够用）
- 探测来源 IP 是 GitHub 的服务器，确保你的服务对公网可访问
- 如果你的服务有 IP 白名单，需要额外配置（GitHub Actions 的 IP 范围见 [官方文档](https://api.github.com/meta)）

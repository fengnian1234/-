---
name: visual-acceptance
description: 视觉验收：一句话启动服务并在浏览器中打开所有入口
metadata:
  type: project
---

用户说 **"验收"** 或 **"视觉验收"** 时，执行以下操作（全部自动化，无需确认）：

**Step 0: 清理旧进程（防止端口冲突）**
```bash
taskkill //F //IM python.exe 2>nul
```
等待 1 秒让端口释放。

**Step 1: 启动服务器**
```bash
cd D:/first-cc && PYTHONUTF8=1 ~/python-embed/python run.py &
```
等待 3 秒。

**Step 2: 健康检查（确认服务器就绪后再打开浏览器）**
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/health
```
必须返回 200。如果失败，再等 2 秒重试一次；仍失败则报告用户。

**Step 3: 自动打开所有验收页面（分 3 批）**

批次1 — 小程序模拟器（3 BnB）:
```bash
start http://127.0.0.1:5000/miniapp?bnb=guishu && start http://127.0.0.1:5000/miniapp?bnb=shanji && start http://127.0.0.1:5000/miniapp?bnb=donglinwai
```

批次2 — 网页端首页（3 BnB）:
```bash
start http://127.0.0.1:5000/gs/ && start http://127.0.0.1:5000/sj/ && start http://127.0.0.1:5000/dlw/
```

批次3 — 工具页:
```bash
start http://127.0.0.1:5000/staff && start http://127.0.0.1:5000/miniapp/chat
```

**Step 4: 输出验收清单**

告诉用户：**8 个页面已全部打开 — 3个小程序模拟器 + 3个网页首页 + 2个工具页**。

**Why:** 用户每次修改后需要在夸克浏览器中视觉验证。旧方案的两个缺陷：(1) 上一轮 kill 服务器后未成功重启 → API 断开；(2) 固定 sleep 3s 不可靠 → 改为 curl 健康检查确认就绪。

**How to apply:** 用户说"验收" → Step 0 清理 → Step 1 启动 → Step 2 确认 → Step 3 打开 → Step 4 报告。

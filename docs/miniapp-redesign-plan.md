# 小程序端改造方案 — 对齐喜茶GO设计语言

> **改造范围**: `style-mp.css` + `miniapp-simulator.html` + `miniapp-chat.html` + `style.css` 移动端响应式
> **不改**: 桌面端 style.css（已验收）、HTML DOM 结构、后端代码
> **隔离原则**: mp-mode 通过 `body.mp-mode` 门控，网页端通过 `@media (max-width: 767px)` 门控，互不污染

---

## 一、喜茶GO设计Token提取

### 1.1 配色
| 用途 | 喜茶值 | 说明 |
|------|--------|------|
| 主背景 | `#FFFFFF` 纯白 / 浅灰底 | 点单页纯白，首页浅灰底 |
| 辅助色/按钮 | `#DBA86F` 暖金 | 功能按钮、强调元素 |
| 深色文字 | `#343434` | 深灰黑，替代纯黑 |
| 灰色文字 | 多级灰阶 | 信息层级靠灰度区分 |
| 卡片 | 白卡 + 极淡灰底 | 二级信息区灰底区分 |
| 悬浮购物车 | 深灰底 `#343434` + 红色购物袋图标 | 品牌视觉锤 |
| 品牌色使用 | **极度克制**，页面90%黑白灰 | 仅关键交互点使用 |

### 1.2 字体
| 喜茶 | 当前项目对齐方向 |
|------|-----------------|
| 数字: NeutraText 独特时尚感 | 价格数字用 `var(--font-serif)` |
| 中文: 方正悠宋（仅国风场景） | Hero/标题保持 serif |
| 正文: 系统无衬线 | `var(--font-sans)` ✅ |
| 行间距刻意加大 | 正文 1.6→1.75 以上 |
| 产品名与价格间距大 | 菜单 item 内间距增加 |

### 1.3 间距与留白
| 喜茶特征 | 具体数值 |
|----------|---------|
| 卡片左边距 20px，右边距 0 | **非对称排版** — 核心品牌识别 |
| 大面积留白 | 首页信息密度极低 |
| Banner 3:2 黄金比例 | Hero 图比例 |
| 产品列表行间距大 | 名称、描述、价格各层间距充足 |

### 1.4 组件样式
| 组件 | 喜茶 | 说明 |
|------|------|------|
| 卡片 | **直角为主**（0-4px圆角） | 时尚、极致、极简 |
| 按钮 | 微圆角 / 50rpx胶囊 | 唯一用圆角的地方 |
| 加购按钮 | 圆形+加号，白底+品牌色描边 | 已实现 ✅ |
| 阴影 | 极浅，几乎不可见 | `--shadow-xs` 为主 |
| 分类Tab | 纯文字，无图标/emoji | 已实现 ✅ |
| 购物车FAB | 深灰底+红色角标 | 需改造 |
| 规格选择 | 底部抽屉式滑出 | 已实现 ✅ |

### 1.5 整体布局
| 喜茶 | 当前项目 |
|------|---------|
| 点单：左分类+右商品 双栏 | menu.html mp-mode 已实现 ✅ |
| 首页：大Banner+2个高频入口 | 当前4个入口，可精简 |
| 百货页：错落有致——不对称排版 | travel/services 需改造 |
| 底部Tab：纯文字 | 模拟器已接近 ✅ |

---

## 二、改动范围隔离设计

```
┌─ 网页端桌面 (>768px) ─────────────────────┐
│  style.css @media (min-width: 768px)         │
│  → 已验收，不再改动                           │
└──────────────────────────────────────────────┘

┌─ 网页端手机竖屏 (≤767px) ──────────────────┐
│  style.css @media (max-width: 767px)          │
│  → 对齐喜茶风格（非对称间距/直角卡片/纯白底） │
└──────────────────────────────────────────────┘

┌─ 小程序模拟器 (mp-mode) ───────────────────┐
│  style-mp.css (body.mp-mode 门控)            │
│  → 精确还原喜茶GO                             │
│  miniapp-simulator.html（外壳）               │
│  → 手机框内视觉与喜茶一致                     │
│  miniapp-chat.html（AI管家）                  │
│  → 聊天气泡对齐喜茶克制配色                   │
└──────────────────────────────────────────────┘
```

---

## 三、实施阶段

### Phase 1: 直角设计语言（喜茶核心识别）

> 喜茶最显著的视觉特征：卡片直角/微圆角，按钮圆角形成唯一对比

**`style-mp.css`** — 卡片圆角大改：
| 组件 | 当前 | 改为 | 理由 |
|------|------|------|------|
| `.room-card` | 12px/14px | **4px** | 直角为主 |
| `.menu-item` | 12px | **4px** | |
| `.entry-card` | 14px | **4px** | |
| `.service-card` | 12px | **4px** | |
| `.food-card` | 16px | **4px** | |
| `.route-card` | 16px | **4px** | |
| `.intro-item` | 12px | **4px** | |
| `.feature-item` | 12px | **4px** | |
| `.review-card` | 12px | **4px** | |
| `.healing-card` | 16px | **4px** | |
| `.tea-*-card` | 16px | **4px** | |
| `.btn-*` 按钮 | 24px/28px | **保持圆角** | 唯一圆角元素 |
| 分类tag/标签 | 10-24px | **0-2px** | 直角标签 |
| 导航激活指示器 | 2px圆角 | **0** | 直角线 |

**`style.css` 手机端** (`@media (max-width: 767px)`) — 同步直角化：
- 所有卡片 `border-radius` 降为 4px
- 按钮保持圆角

### Phase 2: 非对称排版（喜茶空间设计核心）

> 喜茶最独特的空间设计：卡片左margin 20px，右margin 0

**`style-mp.css`** — 卡片改为非对称 margin：
```css
body.mp-mode .room-card,
body.mp-mode .food-card,
body.mp-mode .route-card,
body.mp-mode .menu-item,
body.mp-mode .service-card,
body.mp-mode .entry-card {
    margin-left: 16px;
    margin-right: 0;
}
```

**`style.css` 手机端** — 同步非对称：
```css
@media (max-width: 767px) {
    .room-card, .food-card, .route-card, .service-card, .entry-card {
        margin-left: 16px;
        margin-right: 0;
    }
}
```

**留白增大**：
- `.section-padding`: 1.2rem→2rem
- 卡片 gap 增加 20%
- 区块间距增加

### Phase 3: 配色精调

> 喜茶配色核心：90% 黑白灰 + 暖金辅助，品牌色极度克制

**`style-mp.css`** — 背景更白：
| 变量 | 当前 | 改为 | 理由 |
|------|------|------|------|
| `--color-bg` | `#F5F4F0` | `#F8F7F4` | 更接近纯白 |
| `--color-white` | `#FCFBF9` | `#FFFFFF` | 纯白卡片 |
| `--color-bg-light` | `#EDEBE4` | `#F0EFEC` | 极淡灰底 |

**归墅 accent 调暖金**：
| 变量 | 当前 | 改为 |
|------|------|------|
| `--color-accent` | `#C89878` | `#D0A078`（靠近喜茶 `#DBA86F`） |
| `--color-accent-light` | `#D8B090` | `#DCB890` |

**山纪/东林外 accent 同理偏暖金方向微调**

**购物车FAB** — 改深灰：
- 背景从 `var(--color-primary)` → `#343434`（喜茶深灰购物车）
- 角标保持红色 `var(--color-danger)`

**`style.css` 手机端** — 同步配色调整（仅背景/卡片变量）

### Phase 4: 字体与排版精调

**`style-mp.css`**：
- 正文行高: 1.6→1.75
- 产品名称 letter-spacing: +0.02em
- 价格数字: 强制 `var(--font-serif)` + letter-spacing 0.03em
- 标题与正文大小对比度加大

**`style.css` 手机端** — 同行距/字间距调整

### Phase 5: 模拟器外壳 Heytea 化

**`templates/miniapp-simulator.html`**：
- 面板卡片圆角统一 4px
- 手机框内背景更白
- BnB 切换卡片直角化
- TabBar 激活指示器直角线（2px高）
- 抽屉面板卡片直角化

### Phase 6: AI 管家页

**`templates/miniapp-chat.html`**：
- 聊天气泡圆角: 14px→4px
- AI 气泡左边缘品牌色细线（喜茶克制用色）
- 气泡阴影极浅 `--shadow-xs`
- 头部渐变精简

---

## 四、不改

- 桌面端 `style.css` (>768px 部分)
- HTML 模板 DOM 结构
- JS 功能逻辑
- 后端 Python 代码
- 微信原生小程序 `miniapp/`

## 五、验证

```bash
# 小程序模拟器
http://127.0.0.1:5000/miniapp

# 网页端手机竖屏（Chrome DevTools 手机模式）
http://127.0.0.1:5000/
http://127.0.0.1:5000/menu
http://127.0.0.1:5000/rooms
http://127.0.0.1:5000/travel

# 三 BnB 分别验证 + 暗色/浅色切换
```

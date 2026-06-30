# 网页端风格迭代方案 — 设计 Token 精确映射

> 参考对象：喜茶GO（小程序端）+ 蓝瓶咖啡（网页端）+ 松赞/Elvara（精品酒店网页）  
> 改造范围：`style.css`（桌面+平板），不改 `style-mp.css`（mp 端已完成喜茶对齐）  
> 核心策略：**不改 HTML，不改 JS，只调 CSS 变量值和选择器规则**

---

## 一、参考对象的设计 Token 提取

### 1.1 喜茶GO 小程序（移动端已对齐）

| Token 类别 | 喜茶值 | 说明 |
|-----------|--------|------|
| 页面底色 | `#FFFFFF` 纯白 | 点单页纯白底 |
| 辅助按钮色 | `#DBA86F` 暖金 | 功能按钮 |
| 主文字色 | `#343434` 深灰黑 | 替代纯黑 |
| 卡片底色 | 灰色底 + 白色卡片 | 二级信息区用灰底区分 |
| 圆角 | **直角为主**，按钮微圆角或 50rpx | 极简时尚 |
| 卡片左边距 | 20px | 不对称排版 |
| 字体 | 数字 NeutraText / 中文 方正悠宋 / 正文系统字体 | 层级分明 |
| 行间距 | 加大行间距 | 清爽可读 |

### 1.2 蓝瓶咖啡（网页端对标）

| Token 类别 | 蓝瓶值 | 说明 |
|-----------|--------|------|
| 基础网格 | **120px** 单位 | 所有间距是 120 的因子 |
| 卡片 padding | 大卡 120px / 中卡 60px / 小卡 30px / 紧卡 15px | 四级卡片 |
| 卡片描边 | **2px** | 统一描边 |
| 字体 | 标题 Filson Soft Bold / 正文 Inter Medium | 两字体体系 |
| 字号层级 | 128→80→50→32→24（px） | 极大对比度 |
| 图片策略 | 可突破安全区但不遮挡文字 | 视觉冲击 |
| 容器宽度 | 1680-1920px | 超宽屏友好 |

### 1.3 精品酒店网页（Elvara/Luxilla 模板）

| Token 类别 | 值 | 说明 |
|-----------|-----|------|
| 网格基座 | **8px** | 行业标准 |
| 卡片圆角 | **16px** | 精品酒店卡片标准 |
| 卡片阴影 | `0px 6px 18px rgba(30,52,100,0.1)` | 多层柔和阴影 |
| 卡片 padding | **24px** | 统一卡片内边距 |
| 区块间距 | 48-80px | 大区块之间 |
| 正文字号 | **16px** (base), 18px (large) | 可读性优先 |
| 行高 | ≥ **1.5** | 无障碍标准 |
| 标题字体 | 衬线 (Playfair/Georgia) | 奢华感 |
| 正文字体 | 无衬线 (DM Sans/SF Pro) | 可读性 |
| 12 列栅格 | Desktop: 12 列 + 24px gutter + 40px margin | 宽屏布局 |

---

##二、当前项目 CSS 变量改造方案

### 2.1 配色系统（保留三 BnB 差异化）

**不需要新增色值**——当前项目的 20 个 CSS 变量已覆盖所有需求。只需调整各 BnB 的变量值，使其更接近参考对象的低饱和度、高对比度风格。

参考对象的配色共性：
- 背景：**纯白或极浅灰**（不是暖黄/米色）
- 卡片：纯白 + 极淡边框
- 主色：中低饱和度
- 强调色：偏暖（金/铜色调）
- 文字：`#1a1a1a` → `#666666` → `#999999` 三级灰阶

**调整后的 `:root`（归墅·默认）**：

```css
:root {
    /* ── 主色：降低饱和度，靠近喜茶的克制感 ── */
    --color-primary: #5A7D63;         /* 原 #5C8E6B，降 5% 饱和度 */
    --color-primary-light: #78997F;   /* 原 #7DAA8A */
    --color-primary-dark: #3D5643;    /* 原 #457355 */

    /* ── 强调色：从偏橙转向暖金（喜茶 #DBA86F 方向）── */
    --color-accent: #C09068;          /* 原 #C89878，去橙加金 */
    --color-accent-light: #D4AD88;    /* 原 #D8B090 */

    /* ── 天色/雾色：降低饱和度 ── */
    --color-sky: #98B0AA;             /* 原 #A0BCB8 */
    --color-mist: #D8E2DC;            /* 原 #DCE8E0 */

    /* ── 背景系统：从暖色转向中性 —— 关键改动 ── */
    --color-bg: #F5F4F0;              /* 原 #F8F5F1，更靠近中性灰白 */
    --color-bg-light: #EDEBE4;        /* 原 #F0EBE1 */
    --color-bg-dark: #E4E1D8;         /* 原 #E8E3D8 */

    /* ── 文字系统：增加对比度 ── */
    --color-text: #1C1A17;            /* 原 #2D2A26，深一度 */
    --color-text-light: #6E6A63;      /* 原 #8C8C8C */
    --color-text-lighter: #A09C94;    /* 原 #B0ADA6 */

    /* ── 边框/表面/阴影 —— 更干净 ── */
    --color-border: #E2DED6;          /* 原 #E0DCD5 */
    --color-white: #FCFBF9;           /* 原 #FAF9F6，提亮 */
    --color-shadow: rgba(0,0,0,0.03); /* 原 0.04 */
    --color-shadow-hover: rgba(0,0,0,0.06);

    /* ── 语义色保持 ── */
    --color-success: #5b8c5a;
    --color-warning: #c9954a;
    --color-danger: #c4554a;
}
```

**山纪调整要点**：主色保持深绿方向，强调色保持茶褐，但背景同样转向中性灰白。

**东林外调整要点**：主色保持禅灰蓝，强调色保持禅木，背景同上。

### 2.2 字体层级（对齐蓝瓶 + 精品酒店）

当前已有 `--font-serif` 和 `--font-sans`。改造重点是**字号层级拉大对比**：

```css
:root {
    /* ── 字号层级（基于 8px grid）── */
    --text-xs: 0.6875rem;    /* 11px — Caption / 标签 */
    --text-sm: 0.8125rem;    /* 13px — 描述 / meta */
    --text-base: 1rem;       /* 16px — 正文 */
    --text-md: 1.125rem;     /* 18px — 大正文 / 卡片标题 */
    --text-lg: 1.375rem;     /* 22px — 区块标题 */
    --text-xl: 1.75rem;      /* 28px — 页面标题 */
    --text-2xl: 2.25rem;     /* 36px — Hero 副标题 */
    --text-3xl: 3.25rem;     /* 52px — Hero 主标题 */

    /* ── 字重 ── */
    --font-light: 300;
    --font-normal: 380;      /* 当前 340 偏轻，提升 */
    --font-medium: 520;
    --font-semibold: 620;
    --font-bold: 700;

    /* ── 行高 ── */
    --leading-tight: 1.2;    /* 大标题 */
    --leading-snug: 1.4;     /* 卡片标题 */
    --leading-normal: 1.6;   /* 正文 */
    --leading-relaxed: 1.75; /* 长文 */
}
```

### 2.3 间距系统（对齐 8px 网格 + 蓝瓶 120px 哲学 → 简化为 4px 步进）

```css
:root {
    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px — 紧凑间距 */
    --space-3: 0.75rem;   /* 12px — 元素内间距 */
    --space-4: 1rem;      /* 16px — 默认间距 */
    --space-5: 1.25rem;   /* 20px — 卡片内间距 */
    --space-6: 1.5rem;    /* 24px — 卡片 padding */
    --space-8: 2rem;      /* 32px — 区块间距 */
    --space-10: 2.5rem;   /* 40px — 大区块间距 */
    --space-12: 3rem;     /* 48px — 页面级间距 */
    --space-16: 4rem;     /* 64px — Hero 间距 */
    --space-20: 5rem;     /* 80px — 主页大区块 */
}
```

### 2.4 圆角系统（喜茶直角哲学 + 精品酒店 16px 折中）

喜茶以**直角为主**，精品酒店卡片用 16px。折中方案：**大面积用微圆角，交互组件用大圆角**。

```css
:root {
    --radius-none: 0;          /* 喜茶核心：直角卡片、标签 */
    --radius-xs: 4px;          /* 小标签 */
    --radius-sm: 8px;          /* 按钮、输入框 */
    --radius-md: 12px;         /* 小卡片 */
    --radius-lg: 16px;         /* 主卡片、弹窗（精品酒店标准） */
    --radius-xl: 24px;         /* 大卡片、Hero 下方圆角过渡 */
    --radius-full: 9999px;     /* 胶囊按钮、头像 */
}
```

### 2.5 阴影系统（精品酒店柔和多层阴影）

从当前简单的 `rgba(0,0,0,x)` 升级为带蓝色底调的多层阴影：

```css
:root {
    --shadow-xs: 0 1px 3px rgba(0,0,0,0.04);
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);        /* 卡片默认 */
    --shadow-md: 0 6px 18px rgba(30,52,100,0.08);    /* 卡片 hover */
    --shadow-lg: 0 12px 28px rgba(30,52,100,0.12);   /* 弹窗 */
    --shadow-xl: 0 20px 40px rgba(0,0,0,0.14);       /* 模态框 */
}
```

---

## 三、组件样式精确修改

### 3.1 导航栏 (`.header`)

**参考**：喜茶极简导航 + 精品酒店 sticky header

```css
.header {
    background: rgba(255,255,255,0.92);  /* 半透明毛玻璃 */
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--color-border);
    height: 60px;                         /* 固定高度 */
    padding: 0 var(--space-8);            /* 32px 水平 padding */
}
.header-inner {
    max-width: 1320px;                    /* 比容器宽，容纳更多导航项 */
    margin: 0 auto;
}
.nav-links a {
    font-size: var(--text-sm);            /* 13px */
    font-weight: var(--font-medium);      /* 520 */
    letter-spacing: 0.04em;
    padding: 0.4rem 0.8rem;
    border-radius: var(--radius-sm);      /* 8px，hover 时显底 */
}
.nav-links a:hover {
    background: var(--color-bg-light);
}
.nav-links a.active {
    color: var(--color-primary);
    font-weight: var(--font-semibold);
}
```

### 3.2 按钮系统（喜茶克制 + 精品酒店层级）

```css
/* 一级按钮 — 实心主色 */
.btn-primary {
    background: var(--color-primary-dark);  /* 更深的主色，增加权威感 */
    color: #fff;
    padding: 0.65rem 1.6rem;
    font-size: var(--text-sm);
    font-weight: var(--font-semibold);
    border-radius: var(--radius-full);     /* 胶囊型 */
    letter-spacing: 0.03em;
    transition: all 0.2s var(--ease-out);
    box-shadow: var(--shadow-sm);
}
.btn-primary:hover {
    background: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* 二级按钮 — 描边透明底 */
.btn-outline {
    background: transparent;
    border: 1.5px solid var(--color-border);
    color: var(--color-text);
    padding: 0.55rem 1.4rem;
    font-size: var(--text-sm);
    border-radius: var(--radius-full);
}
.btn-outline:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
}

/* 三级按钮 — 纯文字 */
.btn-ghost {
    background: transparent;
    border: none;
    color: var(--color-text-light);
    padding: 0.4rem 0.8rem;
    font-size: var(--text-xs);
    border-radius: var(--radius-sm);
}
.btn-ghost:hover {
    background: var(--color-bg-light);
    color: var(--color-text);
}
```

### 3.3 卡片（`.menu-item` / `.room-card` / `.food-card` 等）

**统一规范**（对齐精品酒店标准 + 喜茶直角/微圆角哲学）：

```css
/* 所有展示类卡片统一此规范 */
.card,
.room-card,
.food-card,
.route-card,
.healing-card,
.menu-item,
.entry-card,
.intro-item,
.feature-item,
.review-card,
.service-card {
    background: var(--color-white);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);       /* 16px — 精品酒店标准 */
    box-shadow: var(--shadow-sm);          /* 统一默认阴影 */
    transition: all 0.25s var(--ease-out);
}
/* 统一 hover */
.card:hover,
.room-card:hover,
.food-card:hover,
.route-card:hover,
.healing-card:hover,
.menu-item:hover,
.service-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--color-primary-light);
}
```

### 3.4 页面头部 (`.page-header`)

**参考**：松赞内页 Banner

```css
.page-header {
    padding: var(--space-12) 0;            /* 48px 垂直 */
    background: linear-gradient(
        170deg,
        var(--color-sky) 0%,
        var(--color-primary-light) 35%,
        var(--color-primary) 65%,
        var(--color-primary-dark) 100%
    );
    position: relative;
    overflow: hidden;
}
.page-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 32px;
    background: var(--color-bg);
    /* 波浪 SVG 蒙版 */
    mask-image: url("data:image/svg+xml,...");
    -webkit-mask-image: url("data:image/svg+xml,...");
}
.page-header h1 {
    font-size: var(--text-2xl);            /* 36px */
    font-weight: var(--font-bold);
    color: #fff;
    text-shadow: 0 2px 8px rgba(0,0,0,0.12);
    letter-spacing: 0.05em;
}
.page-header p {
    font-size: var(--text-base);
    color: rgba(255,255,255,0.82);
    font-weight: var(--font-normal);
}
```

---

## 四、逐页布局调整（精确值）

### 4.1 首页

| 区域 | 当前 | 改造后 | 理由 |
|------|------|--------|------|
| Hero 高度 | 75vh / max 680px | 80vh / max 720px | 更大视觉冲击 |
| Hero 标题 | 3.4rem / 700 | 3.25rem (52px) / 700 | 对齐 `--text-3xl` |
| Hero 副标题 | 1.3rem | 1.125rem (18px) | 增大层级对比 |
| entry-grid | 4 列, gap 1rem | 4 列, gap 1.5rem (24px) | 对齐 `--space-6` |
| entry-card padding | 1.6rem 1rem | 1.5rem (24px) | 对齐 `--space-6` |
| intro-grid | 4 列, gap 1.2rem | 4 列, gap 1.5rem (24px) | 统一间距 |
| rooms-preview | 4 列, 图高 150px | 4 列, 图高 200px | 图片更大 |
| 区块间距 | 3rem | 5rem (80px) | 对齐 `--space-20` |
| 容器 | padding 0 2rem | padding 0 2.5rem (40px) | 对齐 12 列 margin |

### 4.2 房型列表 (`/rooms`)

| 区域 | 当前 | 改造后 | 理由 |
|------|------|--------|------|
| rooms-list 桌面 | 3 列, gap 1.2rem | **4 列**, gap 1.5rem (24px) | 1200px 容器更充分利用 |
| room-card 图高 | 200px | **220px**, 比例 3:2 | 更大展示 |
| room-card padding | 1rem | **1.5rem** (24px) | 对齐 `--space-6` |
| room-card 标题 | 1.1rem | 1.125rem (18px) | 对齐 `--text-md` |
| room-card 价格 | 1.2rem | 1.375rem (22px) | 对齐 `--text-lg` |

### 4.3 攻略页 (`/travel`)

| 区域 | 当前 | 改造后 | 理由 |
|------|------|--------|------|
| routes-list 桌面 | 2 列 | **3 列** | 更充分利用宽度 |
| foods-list 桌面 | 3 列 | 保持 3 列 | |
| food-card 图高 | 180px | **200px** | |
| food-card padding | 1rem 1.2rem | **1.5rem** (24px) | 对齐 `--space-6` |

### 4.4 服务页 (`/services`)

| 区域 | 当前 | 改造后 | 理由 |
|------|------|--------|------|
| service-grid 桌面 | 3 列 | **4 列** | |
| service-card padding | 1rem | **1.25rem** (20px) | 对齐 `--space-5` |
| service-card 图标 | 1.8rem | 1.5rem | 减少视觉噪音 |

### 4.5 茶场 (`/tea`) + 疗愈 (`/healing`)

| 区域 | 当前 | 改造后 | 理由 |
|------|------|--------|------|
| 卡片 padding | 28px 24px | **24px** (1.5rem) | 对齐 `--space-6` |
| 卡片圆角 | 16px | 保持 16px | 已是精品酒店标准 |
| 卡片 hover | translateY(-2px) + shadow | **统一**到全局 `.card-hover` |
| 价格梯度条 | 硬编码色 | 改用 `color-mix(in srgb, var(--color-primary) ...)` | BnB 自动适配 |

### 4.6 积分页 (`/points`)

| 区域 | 当前 | 改造后 |
|------|------|--------|
| 样式位置 | 大量内联 style | 迁移到 `style.css` 的 `.points-page` 下 |
| 兑换网格 | 2 列 | **3 列** |

---

## 五、全局排版改造

### 5.1 body 基础

```css
body {
    font-size: var(--text-base);           /* 16px */
    font-weight: var(--font-normal);       /* 380 */
    line-height: var(--leading-normal);    /* 1.6 */
    letter-spacing: 0.01em;
    color: var(--color-text);
    background: var(--color-bg);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
```

### 5.2 标题层级

```css
h1 { font-size: var(--text-2xl); font-weight: var(--font-bold); letter-spacing: -0.01em; }
h2 { font-size: var(--text-xl); font-weight: var(--font-semibold); }
h3 { font-size: var(--text-lg); font-weight: var(--font-semibold); }
h4 { font-size: var(--text-md); font-weight: var(--font-medium); }
```

### 5.3 区块标题 (`.section-title`)

```css
.section-title {
    font-size: var(--text-xl);             /* 28px */
    font-weight: var(--font-semibold);     /* 620 */
    letter-spacing: 0.02em;
    margin-bottom: var(--space-3);         /* 12px */
    color: var(--color-text);
    font-family: var(--font-serif);
}
.section-desc {
    font-size: var(--text-sm);             /* 13px */
    color: var(--color-text-light);
    margin-bottom: var(--space-6);         /* 24px */
    line-height: var(--leading-relaxed);
}
```

---

## 六、微交互升级

### 6.1 统一过渡变量

```css
:root {
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --duration-fast: 150ms;
    --duration-normal: 250ms;
    --duration-slow: 400ms;
}
```

### 6.2 图片渐现

```css
img[loading="lazy"] {
    opacity: 0;
    transition: opacity var(--duration-slow) var(--ease-out);
}
img[loading="lazy"].loaded {
    opacity: 1;
}
```

### 6.3 滚动入场优化

```css
.fade-up {
    opacity: 0;
    transform: translateY(24px);
    transition: opacity 0.5s var(--ease-out),
                transform 0.5s var(--ease-out);
}
.fade-up.visible {
    opacity: 1;
    transform: translateY(0);
}
```

---

## 七、实施步骤

### Step 1: CSS 变量层 (`style.css` `:root` 块)

- [ ] 更新全部配色变量值（背景中性化、文字加深、主色降饱和度）
- [ ] 新增 `--text-*` 字号层级变量
- [ ] 新增 `--space-*` 间距变量（保留旧的 `--space-xs/sm/md/lg/xl` 做映射兼容）
- [ ] 新增 `--radius-*` 变量（保留旧的 `--radius-sm/md/lg/xl` 映射兼容）
- [ ] 更新 `--shadow-*` 为多层柔和阴影
- [ ] 新增 `--ease-*` 和 `--duration-*` 变量

### Step 2: 全局元素重定义

- [ ] `body` 基础排版更新
- [ ] `h1-h4` 标题层级
- [ ] `.btn-primary` / `.btn-outline` / `.btn-ghost` 统一
- [ ] `.header` 毛玻璃 + 固定高度
- [ ] `.page-header` 渐变 + 波浪底部
- [ ] `.card` 统一规范（阴影/圆角/hover）

### Step 3: 首页改造

- [ ] Hero 尺寸 + 标题层级
- [ ] entry-grid / intro-grid / rooms-preview 间距和列宽
- [ ] 评价轮播优化
- [ ] FAQ 过渡动画

### Step 4: 子页逐页改造

- [ ] 房型列表：3→4 列，卡片标准对齐
- [ ] 攻略：路线 2→3 列，美食卡片调整
- [ ] 服务：3→4 列，紧急联系横幅
- [ ] 茶场 + 疗愈：卡片 padding 标准化，价格 BnB 色系
- [ ] 积分：内联样式迁移 + 网格调整

### Step 5: 三 BnB 配色精调

- [ ] 归墅 (`:root`) 按上述值更新
- [ ] 山纪 (`[data-bnb="shanji"]`) 保持深绿方向，背景中性化
- [ ] 东林外 (`[data-bnb="donglinwai"]`) 保持禅灰蓝，背景中性化
- [ ] 暗色模式三套同步更新

### Step 6: 收尾验证

- [ ] 所有页面 200
- [ ] 三 BnB 各页面视觉一致性检查
- [ ] 暗色模式检查
- [ ] 响应式断点检查（每个断点截图）

---

## 八、不该改的

- `style-mp.css`（mp 端已对齐喜茶，独立维护）
- HTML 模板结构
- JavaScript 功能逻辑
- `config.py` / `models.py` / 后端代码
- 三 BnB 的**差异化标识**（归墅=竹青、山纪=茶褐、东林外=禅灰蓝）

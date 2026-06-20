/**
 * 云上·印象集 · 微信小程序
 * 全局入口：生命周期、全局状态、初始化、民宿切换
 */
const { login, getOpenId } = require('./utils/auth');
const { initTheme, getTheme } = require('./utils/theme');
const { loadCart } = require('./utils/cart');
const { BNBS } = require('./utils/constants');

App({
  globalData: {
    openid: '',
    unionid: '',
    theme: 'light',
    season: 'summer',
    isLoggedIn: false,
    guestInfo: null,
    cart: null,
    systemInfo: null,
    // ── 多民宿相关 ──────────────────────────────
    currentBnbId: 'guishu',       // 当前选中民宿
    currentBnb: BNBS.guishu,      // 当前民宿完整信息
    bnbs: Object.values(BNBS),    // 三家民宿列表
    hasActiveBooking: false,      // 是否有当前入住
    activeBookingBnbId: null,     // 入住对应的民宿ID
  },

  onLaunch() {
    const sysInfo = wx.getSystemInfoSync();
    this.globalData.systemInfo = sysInfo;
    initTheme(sysInfo);
    this.globalData.cart = loadCart();

    // 恢复上次选择的民宿
    const savedBnbId = wx.getStorageSync('current_bnb_id');
    if (savedBnbId && BNBS[savedBnbId]) {
      this.globalData.currentBnbId = savedBnbId;
      this.globalData.currentBnb = BNBS[savedBnbId];
    }

    this.doLogin();
    console.log(`🏔️ 云上·印象集小程序启动 | 主题:${getTheme()} | 当前民宿:${this.globalData.currentBnb.shortName}`);
  },

  onShow(options) {
    const currentTheme = getTheme();
    if (currentTheme !== this.globalData.theme) {
      this.globalData.theme = currentTheme;
      this.applyThemeToAllPages();
    }
  },

  /** 切换民宿 */
  switchBnb(bnbId) {
    if (!BNBS[bnbId] || bnbId === this.globalData.currentBnbId) return;
    this.globalData.currentBnbId = bnbId;
    this.globalData.currentBnb = BNBS[bnbId];
    wx.setStorageSync('current_bnb_id', bnbId);
    // 触发当前页面刷新
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    if (currentPage && currentPage.onBnbChanged) {
      currentPage.onBnbChanged(bnbId);
    }
  },

  async doLogin() {
    try {
      const cached = getOpenId();
      if (cached) {
        this.globalData.openid = cached;
        this.globalData.isLoggedIn = true;
        return;
      }
      const { code } = await wx.login();
      if (!code) throw new Error('wx.login 失败');
      const result = await login(code);
      this.globalData.openid = result.openid;
      this.globalData.unionid = result.unionid || '';
      this.globalData.isLoggedIn = true;
    } catch (err) {
      console.warn('登录失败，使用离线模式:', err.message);
      if (!this.globalData.openid) {
        this.globalData.openid = this.getOfflineId();
      }
    }
  },

  getOfflineId() {
    const key = 'yunshang_openid';
    let id = wx.getStorageSync(key);
    if (!id) {
      id = 'guest_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 8);
      wx.setStorageSync(key, id);
    }
    return id;
  },

  applyThemeToAllPages() {
    const pages = getCurrentPages();
    pages.forEach(page => {
      if (page.applyTheme) page.applyTheme();
    });
  },
});

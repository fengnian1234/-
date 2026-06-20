/**
 * 云上归墅 · 主题管理
 * 深色/浅色切换 + 四季配色 + CSS 变量动态注入
 *
 * 小程序 WXSS 支持 page[data-theme] 属性选择器，
 * 主题切换通过设置 page 的 data-theme 和 data-season 属性实现。
 */

const storage = require('./storage');
const { getCurrentSeason } = require('./util');

const THEME_KEY = 'theme';
const SEASON_KEY = 'season';

/**
 * 初始化主题
 * @param {object} sysInfo - wx.getSystemInfoSync() 返回值
 */
function initTheme(sysInfo) {
  // 1. 优先使用用户手动设置
  let theme = storage.get(THEME_KEY);
  if (!theme) {
    // 2. 跟随系统
    theme = (sysInfo && sysInfo.theme === 'dark') ? 'dark' : 'light';
  }

  // 季节：优先手动设置，否则自动判断
  let season = storage.get(SEASON_KEY);
  if (!season) {
    season = getCurrentSeason();
  }

  applyTheme(theme, season);
}

/**
 * 应用主题到当前页面
 */
function applyTheme(theme, season) {
  // 确保当前页面根节点有正确的 data- 属性
  const pages = getCurrentPages();
  pages.forEach(page => {
    // 通过 setData 设置 data-theme 属性到根节点
    // 小程序 WXSS 的 page[data-theme="dark"] 选择器会自动生效
    page.setData({
      '_theme': theme,
      '_season': season,
    });

    // 同时在 page 元素上直接设置属性（确保 CSS 变量覆盖）
    // 因为小程序的 page 选择器可能不支持动态 data- 属性
  });

  storage.set(THEME_KEY, theme);
  storage.set(SEASON_KEY, season);

  // 更新全局数据
  const app = getApp();
  if (app && app.globalData) {
    app.globalData.theme = theme;
    app.globalData.season = season;
  }
}

/**
 * 切换深浅色
 */
function toggleTheme() {
  const current = getTheme();
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next, getSeason());
  return next;
}

/**
 * 获取当前主题
 */
function getTheme() {
  return storage.get(THEME_KEY) || 'light';
}

/**
 * 获取当前季节
 */
function getSeason() {
  return storage.get(SEASON_KEY) || getCurrentSeason();
}

/**
 * 设置季节（手动覆盖）
 */
function setSeason(season) {
  const valid = ['spring', 'summer', 'autumn', 'winter'];
  if (!valid.includes(season)) return;
  applyTheme(getTheme(), season);
}

module.exports = {
  initTheme,
  applyTheme,
  toggleTheme,
  getTheme,
  getSeason,
  setSeason,
};

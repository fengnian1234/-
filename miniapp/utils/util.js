/**
 * 云上归墅 · 通用工具函数
 */

/**
 * 格式化价格
 * @param {number} price - 价格
 * @returns {string} 格式化后的价格字符串
 */
function formatPrice(price) {
  if (price == null || isNaN(price)) return '¥0';
  return '¥' + Number(price).toFixed(0);
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式 (默认 'YYYY-MM-DD')
 */
function formatDate(date, format) {
  if (!date) return '';
  format = format || 'YYYY-MM-DD';
  const d = typeof date === 'string' ? new Date(date.replace(/-/g, '/')) : date;
  if (isNaN(d.getTime())) return String(date);

  const map = {
    YYYY: d.getFullYear(),
    MM: String(d.getMonth() + 1).padStart(2, '0'),
    DD: String(d.getDate()).padStart(2, '0'),
    HH: String(d.getHours()).padStart(2, '0'),
    mm: String(d.getMinutes()).padStart(2, '0'),
    ss: String(d.getSeconds()).padStart(2, '0'),
  };
  return format.replace(/YYYY|MM|DD|HH|mm|ss/g, m => map[m]);
}

/**
 * 防抖
 */
function debounce(fn, delay) {
  delay = delay || 300;
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * 截断文字
 */
function truncate(text, maxLen) {
  maxLen = maxLen || 80;
  if (!text || text.length <= maxLen) return text;
  return text.slice(0, maxLen) + '...';
}

/**
 * 获取当前季节
 */
function getCurrentSeason() {
  const month = new Date().getMonth() + 1;
  if (month >= 3 && month <= 5) return 'spring';
  if (month >= 6 && month <= 8) return 'summer';
  if (month >= 9 && month <= 11) return 'autumn';
  return 'winter';
}

/**
 * 生成唯一序列号（购物车用）
 */
function generateSeq() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 6);
}

/**
 * 手机号脱敏
 */
function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone;
  return phone.slice(0, 3) + '****' + phone.slice(-4);
}

/**
 * 判断是否为饮品（含咖啡、茶、特调）
 */
function isDrink(name) {
  if (!name) return false;
  return /咖啡|拿铁|美式|卡布|摩卡|茶|抹茶|可可|热巧|气泡|冰沙|奶昔|苏打/i.test(name);
}

/**
 * 计算住宿天数
 */
function calcNights(checkIn, checkOut) {
  if (!checkIn || !checkOut) return 0;
  const d1 = new Date(checkIn.replace(/-/g, '/'));
  const d2 = new Date(checkOut.replace(/-/g, '/'));
  return Math.max(1, Math.round((d2 - d1) / 86400000));
}

module.exports = {
  formatPrice,
  formatDate,
  debounce,
  truncate,
  getCurrentSeason,
  generateSeq,
  maskPhone,
  isDrink,
  calcNights,
};

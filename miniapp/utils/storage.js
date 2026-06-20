/**
 * 云上归墅 · Storage 封装
 * 统一命名空间前缀，防止键冲突
 */

const PREFIX = 'yunshang_';

/**
 * 同步读取
 */
function get(key, defaultValue) {
  try {
    const val = wx.getStorageSync(PREFIX + key);
    return val !== '' && val !== undefined ? val : (defaultValue || null);
  } catch (e) {
    return defaultValue || null;
  }
}

/**
 * 同步写入
 */
function set(key, value) {
  try {
    wx.setStorageSync(PREFIX + key, value);
  } catch (e) {
    console.warn(`Storage.set 失败: ${key}`, e);
  }
}

/**
 * 删除
 */
function remove(key) {
  try {
    wx.removeStorageSync(PREFIX + key);
  } catch (e) {
    // ignore
  }
}

/**
 * 检查是否存在
 */
function has(key) {
  return get(key) !== null;
}

module.exports = { get, set, remove, has };

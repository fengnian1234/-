/**
 * 云上归墅 · 登录管理
 * wx.login → code → POST /api/auth/miniapp-login → openid
 */

const api = require('./api');
const storage = require('./storage');

const OPENID_KEY = 'openid';
const UNIONID_KEY = 'unionid';

/**
 * 获取本地缓存的 openid
 */
function getOpenId() {
  return storage.get(OPENID_KEY);
}

/**
 * 执行小程序登录，换取 openid
 * @param {string} code - wx.login() 返回的临时 code
 * @returns {Promise<{openid: string, unionid?: string}>}
 */
async function login(code) {
  const result = await api.post('/api/auth/miniapp-login', { code });
  if (result.success && result.openid) {
    storage.set(OPENID_KEY, result.openid);
    if (result.unionid) {
      storage.set(UNIONID_KEY, result.unionid);
    }
    return { openid: result.openid, unionid: result.unionid };
  }
  throw new Error(result.message || '登录失败');
}

/**
 * 生成离线访客 ID（开发/离线用）
 */
function getOfflineId() {
  let id = storage.get(OPENID_KEY);
  if (!id) {
    id = 'guest_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 8);
    storage.set(OPENID_KEY, id);
  }
  return id;
}

module.exports = { login, getOpenId, getOfflineId };

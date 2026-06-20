/**
 * 云上·印象集 · API 请求封装
 * 统一处理 BASE_URL、openid、bnb_id 注入、错误拦截
 */

const { API_BASE_URL } = require('./constants');
const storage = require('./storage');

/**
 * 获取当前 openid
 */
function getOpenId() {
  const app = getApp();
  return (app && app.globalData && app.globalData.openid) || storage.get('openid') || '';
}

/**
 * 获取当前民宿 bnb_id
 */
function getCurrentBnbId() {
  const app = getApp();
  return (app && app.globalData && app.globalData.currentBnbId) || storage.get('current_bnb_id') || 'guishu';
}

/**
 * 发起 GET 请求
 */
function get(path, params) {
  return request('GET', path, params);
}

/**
 * 发起 POST 请求
 */
function post(path, data) {
  return request('POST', path, data);
}

/**
 * 底层请求方法
 */
function request(method, path, data) {
  const openid = getOpenId();
  const bnbId = getCurrentBnbId();
  const header = { 'Content-Type': 'application/json' };

  // GET 自动附加 bnb_id
  let url = API_BASE_URL + path;
  if (method === 'GET') {
    const sep = path.includes('?') ? '&' : '?';
    url += `${sep}bnb_id=${bnbId}`;
  }

  // POST 自动注入 openid 和 bnb_id
  let body = data;
  if (method === 'POST') {
    body = { bnb_id: bnbId, ...(data || {}) };
    if (!body.openid && openid) {
      body.openid = openid;
    }
  }

  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    wx.request({
      url,
      method,
      data: body,
      header,
      timeout: 15000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 429) {
          wx.showToast({ title: '操作太频繁，请稍后再试', icon: 'none' });
          reject(new Error('请求过于频繁'));
        } else {
          const msg = (res.data && res.data.message) || `请求失败(${res.statusCode})`;
          reject(new Error(msg));
        }
      },
      fail(err) {
        console.error(`API 请求失败: ${method} ${path}`, err);
        wx.showToast({ title: '网络异常，请检查连接', icon: 'none' });
        reject(err);
      },
      complete() {
        if (process.env.NODE_ENV !== 'production') {
          console.debug(`[API] ${method} ${path} (${Date.now() - startTime}ms)`);
        }
      },
    });
  });
}

module.exports = { get, post, getOpenId, getCurrentBnbId };

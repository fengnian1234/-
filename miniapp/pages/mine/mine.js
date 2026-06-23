const api = require('../../utils/api');
const { getTheme } = require('../../utils/theme');
const { BNBS } = require('../../utils/constants');
const app = getApp();

Page({
  data: {
    guest: null,
    membershipInfo: null,
    loading: false,
    theme: 'light',
    currentBnb: BNBS.guishu,
  },

  onLoad() {
    this.setData({ currentBnb: app.globalData.currentBnb });
    this.fetchPoints();
  },

  onShow() {
    this.setData({
      theme: getTheme(),
      currentBnb: app.globalData.currentBnb,
    });
    this.fetchPoints();
  },

  async fetchPoints() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/points/' + (getApp().globalData.openid || ''));
      if (data && data.guest) {
        this.setData({
          guest: data.guest,
          membershipInfo: data.membership_info || null,
        });
      }
    } catch (err) {
      // 未登录或首次使用，忽略
    } finally {
      this.setData({ loading: false });
    }
  },

  /** 功能入口导航 */
  onNavServices() {
    wx.navigateTo({ url: '/pages/services/services' });
  },
  onNavPoints() {
    wx.navigateTo({ url: '/pages/points/points' });
  },
  onNavOrders() {
    wx.navigateTo({ url: '/pages/orders/orders' });
  },
  onNavBooking() {
    wx.navigateTo({ url: '/pages/booking/booking' });
  },

  /** 拨打电话 */
  onCallPhone() {
    wx.makePhoneCall({ phoneNumber: BNB.phone });
  },

  /** 关于民宿 */
  onAbout() {
    wx.showModal({
      title: `关于${BNB.shortName}`,
      content: `${BNB.name}\n\n${BNB.address}\n电话：${BNB.phone}\n\n${BNB.description}\n\n期待您的光临。`,
      showCancel: false,
      confirmText: '好的',
    });
  },
});

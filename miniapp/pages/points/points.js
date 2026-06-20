const api = require('../../utils/api');

Page({
  data: {
    guest: null,
    logs: [],
    redeemItems: [],
    earnRules: [],
    membershipInfo: null,
    loading: true,
  },

  onLoad() {
    this.fetchData();
  },

  onShow() {
    this.fetchData();
  },

  async fetchData() {
    this.setData({ loading: true });
    try {
      const openid = getApp().globalData.openid || '';
      const data = await api.get(`/api/points/${openid}`);
      if (data) {
        this.setData({
          guest: data.guest || null,
          logs: data.logs || [],
          redeemItems: data.redeem_items || [],
          earnRules: data.earn_rules || [],
          membershipInfo: data.membership_info || null,
        });
      }
    } catch (err) {
      // ignore
    } finally {
      this.setData({ loading: false });
    }
  },

  /** 签到 */
  async onCheckIn() {
    try {
      const result = await api.post('/api/points/earn', { action: 'checkin' });
      if (result.success) {
        wx.showToast({ title: '签到成功！+10积分', icon: 'success' });
        this.fetchData();
      } else {
        wx.showToast({ title: result.message || '签到失败', icon: 'none' });
      }
    } catch (err) {
      wx.showToast({ title: '网络异常', icon: 'none' });
    }
  },

  /** 兑换 */
  async onRedeem(e) {
    const item = e.currentTarget.dataset.item;
    if (!this.data.guest || this.data.guest.total_points < item.points) {
      wx.showToast({ title: '积分不足', icon: 'none' });
      return;
    }
    wx.showModal({
      title: `兑换：${item.name}`,
      content: `消耗 ${item.points} 积分，确认兑换？`,
      success: async (res) => {
        if (!res.confirm) return;
        try {
          const result = await api.post('/api/points/redeem', { item: item.key });
          if (result.success) {
            wx.showToast({ title: '兑换成功！', icon: 'success' });
            this.fetchData();
          } else {
            wx.showToast({ title: result.message, icon: 'none' });
          }
        } catch (err) {
          wx.showToast({ title: '兑换失败', icon: 'none' });
        }
      },
    });
  },
});

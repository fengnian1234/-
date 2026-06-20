const api = require('../../utils/api');
const { SERVICE_CATEGORIES, BNB } = require('../../utils/constants');

Page({
  data: {
    services: [],
    categories: {},
    loading: true,
    BNB,
  },

  onLoad() {
    this.fetchServices();
  },

  async fetchServices() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/services');
      if (data.success) {
        const categories = {};
        (data.services || []).forEach(s => {
          const key = s.category || 'other';
          if (!categories[key]) categories[key] = [];
          categories[key].push(s);
        });
        this.setData({ services: data.services, categories });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  async onServiceTap(e) {
    const { service } = e.detail;
    wx.showModal({
      title: `确认请求：${service.name}`,
      content: service.description || '',
      confirmText: '确认',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          const result = await api.post('/api/service/request', {
            service_name: service.name,
            room_number: '',
            urgency: 'normal',
          });
          if (result.success) {
            wx.showToast({ title: '已通知前台，请稍候', icon: 'success' });
          }
        } catch (err) {
          wx.showToast({ title: '请求失败', icon: 'none' });
        }
      },
    });
  },

  onCallPhone() {
    wx.makePhoneCall({ phoneNumber: BNB.phone });
  },
});

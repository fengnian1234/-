const api = require('../../utils/api');

Page({
  data: {
    orders: [],
    loading: true,
  },

  onLoad() {
    this.fetchOrders();
  },

  onShow() {
    this.fetchOrders();
  },

  onPullDownRefresh() {
    this.fetchOrders().then(() => wx.stopPullDownRefresh());
  },

  async fetchOrders() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/orders', { limit: 30 });
      this.setData({ orders: Array.isArray(data) ? data : [] });
    } catch (err) {
      // ignore
    } finally {
      this.setData({ loading: false });
    }
  },
});

const api = require('../../utils/api');
const { DIFFICULTY } = require('../../utils/constants');

Page({
  data: {
    routes: [],
    foods: [],
    loading: true,
    DIFFICULTY,
  },

  onLoad() {
    this.fetchData();
  },

  onPullDownRefresh() {
    this.fetchData().then(() => wx.stopPullDownRefresh());
  },

  async fetchData() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/travel');
      if (data.success) {
        this.setData({
          routes: data.routes || [],
          foods: data.foods || [],
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onRouteTap(e) {
    const { route } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/travel-detail/travel-detail?id=${route.id}` });
  },

  onFoodTap(e) {
    const { food } = e.detail;
    wx.navigateTo({ url: `/pages/food-detail/food-detail?id=${food.id}` });
  },
});

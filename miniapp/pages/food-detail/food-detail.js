const api = require('../../utils/api');

Page({
  data: { food: null, loading: true },

  onLoad(options) {
    if (options.id) this.fetchDetail(options.id);
  },

  async fetchDetail(id) {
    this.setData({ loading: true });
    try {
      const data = await api.get(`/api/travel/food/${id}`);
      if (data.success) {
        this.setData({ food: data.food });
        wx.setNavigationBarTitle({ title: data.food.name || '美食详情' });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onOpenLocation() {
    const { food } = this.data;
    if (!food) return;
    wx.showModal({
      title: food.name || '导航',
      content: `地址：${food.address || '暂无地址信息'}`,
      showCancel: true,
      confirmText: '复制地址',
      success(res) {
        if (res.confirm && food.address) {
          wx.setClipboardData({ data: food.address });
          wx.showToast({ title: '地址已复制', icon: 'none' });
        }
      },
    });
  },
});

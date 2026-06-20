const api = require('../../utils/api');
const { DIFFICULTY } = require('../../utils/constants');

Page({
  data: {
    route: null,
    loading: true,
    DIFFICULTY,
  },

  onLoad(options) {
    if (options.id) this.fetchDetail(options.id);
  },

  async fetchDetail(id) {
    this.setData({ loading: true });
    try {
      const data = await api.get(`/api/travel/${id}`);
      if (data.success) {
        this.setData({ route: data.route });
        wx.setNavigationBarTitle({ title: data.route.name || '路线详情' });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onOpenMap(e) {
    const { mapLink } = this.data.route || {};
    if (mapLink) {
      // 尝试打开地图链接
      wx.showModal({
        title: '导航提示',
        content: '是否打开地图导航？',
        success(res) {
          if (res.confirm) {
            // 微信小程序内不支持直接打开外部URL，提示复制
            wx.setClipboardData({ data: mapLink });
            wx.showToast({ title: '地图链接已复制', icon: 'none' });
          }
        },
      });
    }
  },
});

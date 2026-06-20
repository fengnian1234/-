const api = require('../../utils/api');
const { BNB, VIEW_ICONS } = require('../../utils/constants');

Page({
  data: {
    room: null,
    loading: true,
    BNB,
  },

  onLoad(options) {
    const id = options.id;
    if (id) this.fetchDetail(id);
  },

  async fetchDetail(id) {
    this.setData({ loading: true });
    try {
      const data = await api.get(`/api/rooms/${id}`);
      if (data.success) {
        this.setData({
          room: data.room,
          viewIcon: VIEW_ICONS[data.room.view_type] || '🏡',
        });
        wx.setNavigationBarTitle({ title: data.room.name || '房型详情' });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onCallPhone() {
    wx.makePhoneCall({ phoneNumber: BNB.phone });
  },

  onBookingTap() {
    wx.navigateTo({ url: '/pages/booking/booking' });
  },
});

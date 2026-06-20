const api = require('../../utils/api');

Page({
  data: {
    rooms: [],
    loading: true,
  },

  onLoad() {
    this.fetchRooms();
  },

  onPullDownRefresh() {
    this.fetchRooms().then(() => wx.stopPullDownRefresh());
  },

  async fetchRooms() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/rooms');
      if (data.success) {
        this.setData({ rooms: data.rooms });
      }
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  onRoomTap(e) {
    const { room } = e.detail;
    wx.navigateTo({ url: `/pages/room-detail/room-detail?id=${room.id}` });
  },

  onBookingTap() {
    wx.navigateTo({ url: '/pages/booking/booking' });
  },
});

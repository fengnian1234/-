const api = require('../../utils/api');
const app = getApp();

Page({
  data: {
    rooms: [],
    loading: true,
    currentBnb: {},
    noticeItems: [],
  },

  onLoad() {
    const bnb = app.globalData.currentBnb;
    this.setData({
      currentBnb: bnb,
      noticeItems: [
        `预订请通过携程/美团/飞猪/大众点评搜索「${bnb.name}」`,
        '支付方式：平台在线支付或到店支付',
        '入住时间14:00后 · 退房时间12:00前',
        '订房成功后请截图发至民宿微信获取AI管家服务'
      ],
    });
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

/**
 * 民宿选择页 — 三民宿卡片式选择
 */
const { BNBS } = require('../../utils/constants');
const app = getApp();

Page({
  data: {
    bnbs: [],
  },

  onLoad() {
    const bnbs = Object.values(BNBS).map(b => ({
      ...b,
      selected: b.bnb_id === app.globalData.currentBnbId,
    }));
    this.setData({ bnbs });
  },

  onSelect(e) {
    const bnbId = e.currentTarget.dataset.bnbId;
    app.switchBnb(bnbId);
    wx.showToast({ title: `已切换到${BNBS[bnbId].shortName}`, icon: 'success', duration: 1200 });
    setTimeout(() => {
      wx.switchTab({ url: '/pages/index/index' });
    }, 800);
  },
});

/**
 * 民宿切换器组件 — 首页顶部三民宿快速切换
 */
const { BNBS } = require('../../utils/constants');
const app = getApp();

Component({
  properties: {
    showLabel: { type: Boolean, value: true },
  },

  data: {
    bnbs: [],
    currentBnbId: 'guishu',
  },

  lifetimes: {
    attached() {
      const bnbs = Object.values(BNBS).map(b => ({
        bnb_id: b.bnb_id,
        shortName: b.shortName,
        themeColor: b.themeColor,
      }));
      this.setData({
        bnbs,
        currentBnbId: app.globalData.currentBnbId,
      });
    },
  },

  methods: {
    onSwitch(e) {
      const bnbId = e.currentTarget.dataset.bnbId;
      if (bnbId === this.data.currentBnbId) return;
      app.switchBnb(bnbId);
      this.setData({ currentBnbId: bnbId });
      this.triggerEvent('change', { bnbId });
    },

    onGoSelect() {
      wx.navigateTo({ url: '/pages/bnb-select/bnb-select' });
    },
  },
});

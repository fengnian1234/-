const { BOOKING_PLATFORMS, BNB } = require('../../utils/constants');

Page({
  data: {
    platforms: [],
    BNB,
  },

  onLoad() {
    const list = Object.entries(BOOKING_PLATFORMS).map(([key, val]) => ({
      key,
      ...val,
    }));
    this.setData({ platforms: list });
  },

  onPlatformTap(e) {
    const { name } = e.currentTarget.dataset;
    // 小程式中无法直接打开外部链接，提示用户在对应平台搜索
    wx.showModal({
      title: `前往${name}预订`,
      content: `请在${name}APP中搜索「云上归墅」或「${BNB.name}」进行预订`,
      showCancel: true,
      confirmText: '复制名称',
      success(res) {
        if (res.confirm) {
          wx.setClipboardData({ data: BNB.name });
          wx.showToast({ title: '民宿名称已复制', icon: 'none' });
        }
      },
    });
  },

  onCallPhone() {
    wx.makePhoneCall({ phoneNumber: BNB.phone });
  },
});

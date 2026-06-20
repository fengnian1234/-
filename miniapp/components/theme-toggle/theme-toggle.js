const { toggleTheme, getTheme } = require('../../utils/theme');

Component({
  data: {
    isDark: false,
  },

  lifetimes: {
    attached() {
      this.updateState();
    },
  },

  pageLifetimes: {
    show() {
      this.updateState();
    },
  },

  methods: {
    updateState() {
      this.setData({ isDark: getTheme() === 'dark' });
    },

    onToggle() {
      const next = toggleTheme();
      this.setData({ isDark: next === 'dark' });
      wx.showToast({
        title: next === 'dark' ? '已切换深色模式' : '已切换浅色模式',
        icon: 'none',
        duration: 1000,
      });
    },
  },
});

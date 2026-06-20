const api = require('../../utils/api');
const { getCart } = require('../../utils/cart');
const { isDrink } = require('../../utils/util');

let cart = null;

Page({
  data: {
    categories: [],
    recommended: [],
    loading: true,
    cartVisible: false,
    cartCount: 0,
    drinkModalVisible: false,
    drinkTarget: null,
  },

  onLoad() {
    cart = getCart();
    this.fetchMenu();
    this.updateCartBadge();
  },

  onShow() {
    this.updateCartBadge();
  },

  onPullDownRefresh() {
    this.fetchMenu().then(() => wx.stopPullDownRefresh());
  },

  async fetchMenu() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/menu');
      if (data.success) {
        this.setData({
          categories: data.categories || [],
          recommended: data.recommended || [],
        });
      }
    } catch (err) {
      wx.showToast({ title: '加载菜单失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  updateCartBadge() {
    if (cart) {
      this.setData({ cartCount: cart.getCount() });
      // 同步更新 TabBar 角标
      wx.setTabBarBadge({
        index: 2,
        text: cart.getCount() > 0 ? String(cart.getCount()) : '',
      }).catch(() => {}); // 忽略 0 时的错误
    }
  },

  /** 点击"点单" */
  onAddItem(e) {
    const { item } = e.detail;
    // 饮品触发定制弹窗
    if (isDrink(item.name)) {
      this.setData({ drinkModalVisible: true, drinkTarget: item });
    } else {
      cart.add({ ...item });
      this.updateCartBadge();
      wx.showToast({ title: `已加入：${item.name}`, icon: 'success', duration: 800 });
    }
  },

  /** 饮品定制确认 */
  onDrinkConfirm(e) {
    const { item, options } = e.detail;
    cart.add({ ...item, options });
    this.setData({ drinkModalVisible: false, drinkTarget: null });
    this.updateCartBadge();
    wx.showToast({ title: `已加入：${item.name} (${options})`, icon: 'success', duration: 800 });
  },

  onDrinkCancel() {
    this.setData({ drinkModalVisible: false, drinkTarget: null });
  },

  /** 购物车 */
  onOpenCart() {
    this.setData({ cartVisible: true });
  },

  onCloseCart() {
    this.setData({ cartVisible: false });
  },

  onOrderSuccess(e) {
    this.updateCartBadge();
    // 清空 TabBar 角标
    wx.removeTabBarBadge({ index: 2 }).catch(() => {});
  },
});

const { getCart } = require('../../utils/cart');
const api = require('../../utils/api');

let cart = null;

Component({
  properties: {
    visible: { type: Boolean, value: false },
  },

  data: {
    items: [],
    roomNumber: '',
    remark: '',
    totalCount: 0,
    totalPrice: 0,
    submitting: false,
    _hasItems: false,
  },

  lifetimes: {
    attached() {
      cart = getCart();
      this.refresh();
    },
  },

  pageLifetimes: {
    show() {
      this.refresh();
    },
  },

  observers: {
    'visible'(val) {
      if (val) this.refresh();
    },
  },

  methods: {
    /** 刷新购物车数据 */
    refresh() {
      if (!cart) return;
      this.setData({
        items: cart.items.slice(),
        roomNumber: cart.roomNumber,
        remark: cart.remark,
        totalCount: cart.getCount(),
        totalPrice: cart.getTotal(),
        _hasItems: cart.items.length > 0,
      });
    },

    onClose() {
      this.setData({ visible: false });
    },

    onClear() {
      wx.showModal({
        title: '确认清空',
        content: '确定要清空购物车吗？',
        success: (res) => {
          if (res.confirm) {
            cart.clear();
            this.refresh();
          }
        },
      });
    },

    onIncrease(e) {
      const seq = e.currentTarget.dataset.seq;
      const item = cart.items.find(i => i.seq === seq);
      if (item) {
        cart.updateQuantity(seq, item.quantity + 1);
        this.refresh();
      }
    },

    onDecrease(e) {
      const seq = e.currentTarget.dataset.seq;
      const item = cart.items.find(i => i.seq === seq);
      if (item) {
        if (item.quantity <= 1) {
          cart.remove(seq);
        } else {
          cart.updateQuantity(seq, item.quantity - 1);
        }
        this.refresh();
      }
    },

    onRemove(e) {
      cart.remove(e.currentTarget.dataset.seq);
      this.refresh();
    },

    onRoomInput(e) {
      cart.setRoomNumber(e.detail.value);
    },

    onRemarkInput(e) {
      cart.setRemark(e.detail.value);
    },

    async onSubmit() {
      if (this.data.submitting) return;
      if (cart.isEmpty()) {
        wx.showToast({ title: '购物车为空', icon: 'none' });
        return;
      }

      this.setData({ submitting: true });

      try {
        const orderData = cart.toOrderData();
        const result = await api.post('/api/order', orderData);
        if (result.success) {
          wx.showToast({ title: '下单成功！', icon: 'success' });
          cart.clear();
          this.refresh();
          this.setData({ visible: false });
          this.triggerEvent('order-success', { order: result.order });
        } else {
          wx.showToast({ title: result.message || '下单失败', icon: 'none' });
        }
      } catch (err) {
        wx.showToast({ title: err.message || '网络异常', icon: 'none' });
      } finally {
        this.setData({ submitting: false });
      }
    },
  },
});

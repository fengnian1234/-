const STATUS_TAG_MAP = {
  'pending': 'accent',
  'paid': 'success',
  'preparing': 'warning',
  'delivered': 'primary',
  'completed': 'primary',
  'cancelled': 'accent',
};

Component({
  properties: {
    order: { type: Object, value: {} },
  },
  observers: {
    'order.status'(status) {
      this.setData({ statusTag: STATUS_TAG_MAP[status] || 'accent' });
    },
  },
});

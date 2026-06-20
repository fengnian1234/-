const { truncate } = require('../../utils/util');

Component({
  properties: {
    food: { type: Object, value: {} },
  },

  observers: {
    'food'(food) {
      if (!food) return;
      this.setData({
        truncatedDesc: truncate(food.description, 80),
        truncatedAddress: truncate(food.address, 20),
      });
    },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { food: this.data.food });
    },
  },
});

const { formatPrice, truncate } = require('../../utils/util');
const { VIEW_ICONS } = require('../../utils/constants');

// 景观 → 占位渐变类名映射
const GRADIENT_MAP = {
  '山景': 'mountain',
  '云海': 'sky',
  '竹林': 'forest',
  '湖景': 'sky',
  '花园': 'earth',
};

Component({
  properties: {
    room: { type: Object, value: {} },
    compact: { type: Boolean, value: false }, // compact 模式用于首页精选
  },

  observers: {
    'room'(room) {
      if (!room) return;
      const stock = room.total_count || 1;
      let stockText = '';
      if (stock <= 1) stockText = '仅剩1间';
      else if (stock <= 3) stockText = '热订中';

      this.setData({
        priceText: formatPrice(room.price),
        truncatedDesc: truncate(room.description, 100),
        viewIcon: VIEW_ICONS[room.view_type] || '🏡',
        gradientClass: GRADIENT_MAP[room.view_type] || 'forest',
        stockText,
      });
    },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { room: this.data.room });
    },
  },
});

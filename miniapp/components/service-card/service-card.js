const { truncate } = require('../../utils/util');

Component({
  properties: {
    service: { type: Object, value: {} },
  },
  observers: {
    'service'(s) {
      if (s) this.setData({ truncatedDesc: truncate(s.description, 30) });
    },
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { service: this.data.service });
    },
  },
});

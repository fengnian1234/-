Component({
  properties: {
    images: { type: Array, value: [] },
  },

  data: {
    current: 0,
  },

  methods: {
    onSwiperChange(e) {
      this.setData({ current: e.detail.current });
    },

    onPrev() {
      const { current, images } = this.data;
      if (current > 0) {
        this.setData({ current: current - 1 });
      }
    },

    onNext() {
      const { current, images } = this.data;
      if (current < images.length - 1) {
        this.setData({ current: current + 1 });
      }
    },

    onDotTap(e) {
      this.setData({ current: e.currentTarget.dataset.index });
    },
  },
});

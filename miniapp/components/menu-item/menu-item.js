Component({
  properties: {
    item: { type: Object, value: {} },
  },
  methods: {
    onAdd() {
      this.triggerEvent('add', { item: this.data.item });
    },
  },
});

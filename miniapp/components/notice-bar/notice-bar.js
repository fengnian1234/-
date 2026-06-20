Component({
  properties: {
    type: { type: String, value: 'info' },   // info|warning|success
    icon: { type: String, value: '📢' },
    title: { type: String, value: '' },
    items: { type: Array, value: [] },
  },
});

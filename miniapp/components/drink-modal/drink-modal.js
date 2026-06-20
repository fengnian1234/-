const { isDrink } = require('../../utils/util');

Component({
  properties: {
    visible: { type: Boolean, value: false },
    item: { type: Object, value: {} },
  },

  data: {
    isTea: false,
    // 茶选项
    teaTypes: ['庐山云雾', '红茶', '绿茶', '普洱'],
    teaSizes: ['热饮·大杯', '热饮·小杯', '冷泡·大杯'],
    selectedTea: '庐山云雾',
    selectedSize: '热饮·大杯',
    // 咖啡等饮品选项
    sugarLevels: ['无糖', '三分糖', '半糖', '七分糖', '全糖'],
    temperatures: ['热', '冰', '常温'],
    selectedSugar: '半糖',
    selectedTemp: '热',
  },

  observers: {
    'item'(item) {
      if (item) {
        this.setData({ isTea: item.name && item.name.includes('茶') });
      }
    },
  },

  methods: {
    onSelectTea(e) { this.setData({ selectedTea: e.currentTarget.dataset.value }); },
    onSelectSize(e) { this.setData({ selectedSize: e.currentTarget.dataset.value }); },
    onSelectSugar(e) { this.setData({ selectedSugar: e.currentTarget.dataset.value }); },
    onSelectTemp(e) { this.setData({ selectedTemp: e.currentTarget.dataset.value }); },

    onCancel() {
      this.triggerEvent('cancel');
    },

    onConfirm() {
      const { isTea, selectedTea, selectedSize, selectedSugar, selectedTemp, item } = this.data;
      const options = isTea
        ? `${selectedTea}·${selectedSize}`
        : `${selectedSugar}·${selectedTemp}`;

      this.triggerEvent('confirm', {
        item,
        options,
      });
    },
  },
});

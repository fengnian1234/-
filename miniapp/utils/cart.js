/**
 * 云上归墅 · 购物车状态管理（Singleton）
 * 持久化到 Storage，跨页面共享
 */

const storage = require('./storage');
const { generateSeq } = require('./util');

const CART_KEY = 'cart';
let instance = null;

/**
 * 购物车类
 */
class Cart {
  constructor() {
    this.items = [];
    this.roomNumber = '';
    this.remark = '';
    this._loaded = false;
  }

  /** 从 Storage 加载 */
  load() {
    if (this._loaded) return;
    const saved = storage.get(CART_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        this.items = data.items || [];
        this.roomNumber = data.roomNumber || '';
        this.remark = data.remark || '';
      } catch (e) {
        this.items = [];
      }
    }
    this._loaded = true;
  }

  /** 保存到 Storage */
  save() {
    storage.set(CART_KEY, JSON.stringify({
      items: this.items,
      roomNumber: this.roomNumber,
      remark: this.remark,
    }));
  }

  /**
   * 添加菜品
   * @param {object} item - { id, name, price, description, image, is_recommended, options? }
   * @returns {string} seq - 购物车条目唯一 ID
   */
  add(item) {
    const seq = generateSeq();
    const existing = this.items.find(i =>
      i.id === item.id &&
      JSON.stringify(i.options) === JSON.stringify(item.options)
    );

    if (existing) {
      existing.quantity += 1;
      existing.seq = seq; // 更新 seq 以触发 UI 刷新
    } else {
      this.items.push({
        ...item,
        seq,
        quantity: 1,
        options: item.options || null,
      });
    }
    this.save();
    return seq;
  }

  /**
   * 删除条目
   */
  remove(seq) {
    this.items = this.items.filter(i => i.seq !== seq);
    this.save();
  }

  /**
   * 更新数量
   */
  updateQuantity(seq, quantity) {
    const item = this.items.find(i => i.seq === seq);
    if (item) {
      item.quantity = Math.max(1, quantity);
      this.save();
    }
  }

  /**
   * 清空购物车
   */
  clear() {
    this.items = [];
    this.roomNumber = '';
    this.remark = '';
    this.save();
  }

  /**
   * 设置房间号
   */
  setRoomNumber(room) {
    this.roomNumber = room || '';
    this.save();
  }

  /**
   * 设置备注
   */
  setRemark(remark) {
    this.remark = remark || '';
    this.save();
  }

  /**
   * 获取商品总数
   */
  getCount() {
    return this.items.reduce((sum, i) => sum + i.quantity, 0);
  }

  /**
   * 获取总价
   */
  getTotal() {
    return this.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  }

  /**
   * 获取下单用的数据
   */
  toOrderData() {
    return {
      items: this.items.map(i => ({
        id: i.id,
        name: i.name,
        quantity: i.quantity,
        price: i.price,
      })),
      room_number: this.roomNumber,
      remark: this.remark,
    };
  }

  /**
   * 检查是否为空
   */
  isEmpty() {
    return this.items.length === 0;
  }
}

/** 获取购物车单例 */
function getCart() {
  if (!instance) {
    instance = new Cart();
    instance.load();
  }
  return instance;
}

/** 从 Storage 加载购物车（用于 app.js 初始化） */
function loadCart() {
  return getCart();
}

module.exports = { getCart, loadCart };

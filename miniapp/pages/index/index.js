/**
 * 首页 - 数据与交互（三民宿平台）
 */
const api = require('../../utils/api');
const { getTheme, getSeason } = require('../../utils/theme');
const { SEASON_POEMS, BNBS } = require('../../utils/constants');
const app = getApp();

// FAQ 数据
const FAQS = [
  { q: '民宿在庐山什么位置？', a: '庐山山上的大林沟路27号，位于牯岭镇核心地带，步行可达花径、如琴湖。索道站下车后约5分钟车程即到。' },
  { q: '入住和退房时间是几点？', a: '入住时间：14:00之后\n退房时间：12:00之前\n如需提前入住或延迟退房，请提前联系前台协商。' },
  { q: '如何预订房间？', a: '您可以通过携程、美团、飞猪、大众点评等平台搜索对应民宿名称预订。预订成功后建议联系前台，解锁AI管家服务。' },
  { q: '停车方便吗？', a: '庐山山上停车位有限。7-8月周末及节假日禁止外地车辆上山，建议将车停在山下索道站停车场，乘坐索道上山。' },
  { q: '可以带宠物吗？', a: '我们理解您对宠物的喜爱，但为保证所有客人的舒适体验，目前暂不支持携带宠物入住，感谢理解。' },
  { q: 'AI管家是什么？', a: '预订成功后联系前台确认，即可解锁AI管家，享受24小时智能旅行顾问服务。' },
  { q: '积分有什么用？', a: '签到、评价、分享民宿都可以获得积分，积分可以在积分商城兑换咖啡券、房费抵扣等礼品。三家民宿积分通用。' },
  { q: '三家民宿有什么不同？', a: '云上·归墅：经典山居体验\n云上·山纪：茶园环绕品茗\n云上·东林外：禅修疗愈身心' },
];

Page({
  data: {
    currentBnb: BNBS.guishu,
    featuredRooms: [],
    loading: true,
    currentSlide: 0,
    reviews: [],
    faqOpenIndex: -1,
    seasonPoem: '',
    season: 'summer',
    theme: 'light',
    FAQS,
  },

  onLoad() {
    this.setData({
      currentBnb: app.globalData.currentBnb,
      season: getSeason(),
      theme: getTheme(),
      seasonPoem: SEASON_POEMS[getSeason()] || SEASON_POEMS.summer,
      reviews: DEFAULT_REVIEWS,
    });
    this.fetchData();
  },

  onShow() {
    this.setData({
      theme: getTheme(),
      currentBnb: app.globalData.currentBnb,
    });
  },

  /** 民宿切换回调（bnb-switcher 触发） */
  onBnbChanged(e) {
    this.setData({ currentBnb: app.globalData.currentBnb });
    this.fetchData();
  },

  onPullDownRefresh() {
    this.fetchData().then(() => wx.stopPullDownRefresh());
  },

  async fetchData() {
    this.setData({ loading: true });
    try {
      const data = await api.get('/api/rooms');
      if (data.success) {
        this.setData({ featuredRooms: data.rooms.slice(0, 4) });
      }
    } catch (err) {
      console.error('首页数据加载失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /** 快捷入口导航 */
  onQuickNav(e) {
    const tab = e.currentTarget.dataset.tab;
    switch (tab) {
      case 'rooms': wx.switchTab({ url: '/pages/rooms/rooms' }); break;
      case 'menu': wx.switchTab({ url: '/pages/menu/menu' }); break;
      case 'travel': wx.switchTab({ url: '/pages/travel/travel' }); break;
      case 'services': wx.navigateTo({ url: '/pages/services/services' }); break;
    }
  },

  /** 房型卡片点击 */
  onRoomTap(e) {
    const { room } = e.detail;
    wx.navigateTo({ url: `/pages/room-detail/room-detail?id=${room.id}` });
  },

  /** FAQ 展开/折叠 */
  onFaqToggle(e) {
    const idx = e.currentTarget.dataset.index;
    this.setData({
      faqOpenIndex: this.data.faqOpenIndex === idx ? -1 : idx,
    });
  },

  /** 拨打电话 */
  onCallPhone() {
    wx.makePhoneCall({ phoneNumber: BNB.phone });
  },
});

// 硬编码评价（与 Web 版一致）
const DEFAULT_REVIEWS = [
  [
    { name: '小雨', avatar: '👩', rating: 5, text: '太美了！窗外就是云雾缭绕的山景，早晨被鸟鸣唤醒，咖啡也非常好喝～', date: '2025-10-12' },
    { name: '山居客', avatar: '👨', rating: 5, text: '房间设计很有格调，床品舒适。管家服务周到，给我们推荐了超棒的徒步路线。', date: '2025-10-08' },
    { name: '云游四海', avatar: '🧑', rating: 5, text: '庐山最佳民宿没有之一！位置绝佳，步行可达花径，下次还会再来。', date: '2025-10-03' },
    { name: '归隐人士', avatar: '👩‍🦳', rating: 4, text: '非常安静的住宿体验，远离喧嚣。夜晚星空很美，适合放空自己。', date: '2025-09-28' },
  ],
  [
    { name: '摄影爱好者', avatar: '📷', rating: 5, text: '窗外云海日出太震撼了！拍到了很多满意的作品，民宿本身就是一道风景。', date: '2025-09-20' },
    { name: '蜜月旅行', avatar: '💑', rating: 5, text: '在这里度过了难忘的蜜月，管家还贴心地准备了玫瑰花和香槟，感动～', date: '2025-09-15' },
    { name: '背包客', avatar: '🎒', rating: 5, text: '一个人来庐山徒步，住在这里很方便。咖啡馆的小姐姐还给了我很多路线建议。', date: '2025-09-10' },
    { name: '退休生活', avatar: '👴', rating: 5, text: '和老伴在这里住了三天，空气好、环境美、服务佳，强烈推荐给同龄朋友！', date: '2025-09-05' },
  ],
  [
    { name: '小红书博主', avatar: '📝', rating: 5, text: '拍照超出片！每个角落都是精心设计过的，发了三篇笔记都爆了。', date: '2025-08-28' },
    { name: '吃货达人', avatar: '🍜', rating: 5, text: '咖啡馆的庐山云雾茶和提拉米苏绝了！早餐也超级丰盛，食材都是当地新鲜的。', date: '2025-08-20' },
    { name: '避暑游客', avatar: '🏖️', rating: 5, text: '夏天来庐山避暑，选了云上归墅太明智了。凉爽舒适，完全不想走。', date: '2025-08-12' },
    { name: '商务出差', avatar: '💼', rating: 4, text: '出差顺道来庐山，没想到民宿也能这么舒适。WiFi很稳定，适合远程办公。', date: '2025-08-05' },
  ],
];

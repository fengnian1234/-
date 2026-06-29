/**
 * 云上·印象集 · 常量配置（三民宿平台）
 */

// API 基础地址
const API_BASE_URL = 'http://127.0.0.1:5000';

// ── 三民宿配置 ──────────────────────────────────────
const BNBS = {
  guishu: {
    bnb_id: 'guishu',
    name: '云上·归墅民宿',
    shortName: '云上归墅',
    address: '庐山山上·庐山风景名胜区大林沟路27号',
    phone: '16607927666',
    latitude: 29.5568,
    longitude: 115.9797,
    themeColor: '#5C8E6B',
    description: '庐山之巅，大林沟路27号，云雾深处的静谧之所。',
  },
  shanji: {
    bnb_id: 'shanji',
    name: '云上·山纪民宿',
    shortName: '云上山纪',
    address: '庐山山上·庐山风景名胜区慧远路104号',
    phone: '19880281717',
    latitude: 29.572595,
    longitude: 115.978075,
    themeColor: '#2C4335',
    description: '位于景区中心，30间精品客房，私享300平花园庭院。咖啡书吧、云上茶吧、山货餐厅，提供贴心管家服务。',
    features: ['tea'],
  },
  donglinwai: {
    bnb_id: 'donglinwai',
    name: '云上·东林外民宿',
    shortName: '云上东林外',
    address: '庐山山下·九江濂溪区赛阳镇赛阳路8号',
    phone: '18807028687',
    latitude: 29.595012,
    longitude: 115.940758,
    themeColor: '#4A5D78',
    description: '东林寺旁，禅意疗愈之所。20间禅房式客房，禅拍/铜锣浴/素斋/晨钟暮课。可携宠入住。',
    features: ['healing'],
  },
};

// 默认民宿（向后兼容）
const BNB = BNBS.guishu;

// BnB ID → URL前缀映射
const BNB_PREFIX_MAP = {
  guishu: '/gs',
  shanji: '/sj',
  donglinwai: '/dlw',
};

// 景观图标映射
const VIEW_ICONS = {
  '山景': '🏔️',
  '云海': '☁️',
  '竹林': '🎋',
  '湖景': '🌊',
  '花园': '🌸',
};

// 服务分类中英文映射
const SERVICE_CATEGORIES = {
  'housekeeping': '客房服务',
  'maintenance': '设施维修',
  'frontdesk': '前台服务',
  'other': '其他服务',
};

// 预订平台信息
const BOOKING_PLATFORMS = {
  '携程': { name: '携程旅行', icon: '🏨', color: '#2577e3' },
  '美团': { name: '美团民宿', icon: '🏠', color: '#ffc300' },
  '飞猪': { name: '飞猪旅行', icon: '✈️', color: '#ff5a00' },
  '大众点评': { name: '大众点评', icon: '⭐', color: '#ffc300' },
};

// 季节月份映射
const SEASONS = {
  spring: [3, 4, 5],
  summer: [6, 7, 8],
  autumn: [9, 10, 11],
  winter: [12, 1, 2],
};

// 季节诗词
const SEASON_POEMS = {
  spring: '人间四月芳菲尽，山寺桃花始盛开。',
  summer: '庐山秀出南斗傍，屏风九叠云锦张。',
  autumn: '停车坐爱枫林晚，霜叶红于二月花。',
  winter: '忽如一夜春风来，千树万树梨花开。',
};

// 难度标签
const DIFFICULTY = {
  easy: { label: '轻松', color: 'tag--success' },
  medium: { label: '适中', color: 'tag--accent' },
  hard: { label: '挑战', color: 'tag--warning' },
};

// 平台评价链接
const REVIEW_PLATFORMS = {
  '携程': { name: '携程旅行', icon: '🏨' },
  '美团': { name: '美团', icon: '🏠' },
  '飞猪': { name: '飞猪旅行', icon: '✈️' },
  '大众点评': { name: '大众点评', icon: '⭐' },
  '小红书': { name: '小红书', icon: '📕' },
  '抖音': { name: '抖音', icon: '🎵' },
};

module.exports = {
  API_BASE_URL,
  BNB,
  BNBS,
  BNB_PREFIX_MAP,
  VIEW_ICONS,
  SERVICE_CATEGORIES,
  BOOKING_PLATFORMS,
  SEASONS,
  SEASON_POEMS,
  DIFFICULTY,
  REVIEW_PLATFORMS,
};

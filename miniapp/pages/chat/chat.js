/**
 * AI 管家聊天页 — 智能对话
 */
const api = require('../../utils/api');

Page({
  data: {
    messages: [],
    inputValue: '',
    isTyping: false,
    scrollToView: '',
  },

  onLoad() {
    this.addSysMsg('你好！我是你的 AI 管家 🤖\n\n可以问我房型、美食、攻略、交通等问题，也可以直接说「打扫」「叫醒」等快捷指令～');
  },

  onInput(e) {
    this.setData({ inputValue: e.detail.value });
  },

  async sendMsg(e) {
    const content = (e && e.currentTarget && e.currentTarget.dataset.msg) || this.data.inputValue.trim();
    if (!content || this.data.isTyping) return;
    if (!e || !e.currentTarget || !e.currentTarget.dataset.msg) {
      this.setData({ inputValue: '' });
    }

    // 用户消息
    const msgs = [...this.data.messages, { role: 'me', text: content }];
    this.setData({ messages: msgs, isTyping: true, scrollToView: 'msg-' + (msgs.length - 1) });

    try {
      const res = await api.post('/api/simulate-chat', {
        content,
        openid: api.getOpenId(),
      });
      const reply = res.reply || '抱歉，我暂时无法回复～';
      const handler = res.handler || '';
      const labelMap = { keyword: '关键词', ai_travel_advisor: 'AI·旅行顾问', ai_pre_arrival: 'AI·待入住', ai_guest_butler: 'AI·已入住', ai_post_stay: 'AI·复购关怀' };
      const meta = labelMap[handler] || handler;
      const final = [...this.data.messages, { role: 'you', text: reply, meta: meta || '' }];
      this.setData({ messages: final, isTyping: false, scrollToView: 'msg-' + (final.length - 1) });
    } catch (e) {
      const final = [...this.data.messages, { role: 'you', text: '连接失败，请确认服务已启动', meta: '错误' }];
      this.setData({ messages: final, isTyping: false });
    }
  },

  addSysMsg(text) {
    this.setData({ messages: [{ role: 'sys', text }] });
  },

  async resetChat() {
    try {
      await api.post('/api/simulate/reset', { openid: api.getOpenId() });
    } catch (e) { /* ignore */ }
    this.setData({ messages: [] });
    this.addSysMsg('对话已重置，有什么可以帮你的？');
  },
});

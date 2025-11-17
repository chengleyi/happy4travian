// 首页页面：调用后端健康检查接口并展示结果
const { BASE_URL } = require('../../utils/request')
Page({
  data: { health: '' },
  // 主动拉取健康状态
  checkHealth() {
    wx.request({
      url: BASE_URL + '/health',
      method: 'GET',
      success: res => { this.setData({ health: res.data }) },
      fail: () => { this.setData({ health: 'error' }) }
    })
  },
  // 页面加载时触发一次检查
  onLoad() { this.checkHealth() }
})
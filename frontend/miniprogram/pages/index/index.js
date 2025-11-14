const { BASE_URL } = require('../../utils/request')
Page({
  data: { health: '' },
  checkHealth() {
    wx.request({
      url: BASE_URL + '/health',
      method: 'GET',
      success: res => { this.setData({ health: res.data }) },
      fail: () => { this.setData({ health: 'error' }) }
    })
  },
  onLoad() { this.checkHealth() }
})
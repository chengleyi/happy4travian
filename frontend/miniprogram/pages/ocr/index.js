const { BASE_URL } = require('../../utils/request')
Page({
  data: {
    imagePath: '',
    gameAccountId: '',
    write: false,
    resultText: '',
    uploading: false
  },
  chooseImage() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: res => {
        const p = res.tempFilePaths && res.tempFilePaths[0]
        if (p) this.setData({ imagePath: p })
      }
    })
  },
  onInputAccount(e) { this.setData({ gameAccountId: (e && e.detail && e.detail.value) || '' }) },
  onToggleWrite(e) { this.setData({ write: !!(e && e.detail && e.detail.value) }) },
  uploadAndParse() {
    const fp = this.data.imagePath
    if (!fp) { wx.showToast({ title: '请先选择截图', icon: 'none' }); return }
    this.setData({ uploading: true, resultText: '' })
    const formData = {}
    if (this.data.gameAccountId) formData.gameAccountId = this.data.gameAccountId
    if (this.data.write) formData.write = '1'
    wx.uploadFile({
      url: BASE_URL + '/troops/parse-image',
      filePath: fp,
      name: 'file',
      formData,
      success: res => {
        let body = {}
        try { body = JSON.parse(res.data) } catch (_) { body = res.data }
        const txt = typeof body === 'object' ? JSON.stringify(body) : String(body)
        this.setData({ resultText: txt })
      },
      fail: err => {
        this.setData({ resultText: String(err && err.errMsg || err) })
      },
      complete: () => { this.setData({ uploading: false }) }
    })
  }
})
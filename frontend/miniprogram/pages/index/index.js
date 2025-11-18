// 首页页面：调用后端健康检查接口并展示结果
// 说明：这是一个演示页面，包含两类接口清单（只读与写入），
// - 点击按钮会依次调用相应后端 API，并在界面上显示“通过/失败”与简短总结。
// - `data` 是页面的状态，WXML 模板通过 `{{...}}` 读取这些值进行渲染。
const { BASE_URL } = require('../../utils/request')
Page({
  data: { 
    health: '',                // 健康检查返回内容（字符串化显示）
    testResults: [],           // 批量测试结果列表
    writeEnabled: false,       // 是否允许执行写入类接口（默认关闭，避免误操作）
    endpointStatuses: {},      // 每个接口当前状态（pass/fail）与简要说明
    // 只读接口清单：用于快速探测服务是否正常
    readList: [
    { key: 'GET_health', label: '健康检查' },
    { key: 'GET_healthz', label: '健康存活检查' },
    { key: 'GET_db_ping', label: '数据库连通' },
    { key: 'GET_servers', label: '服务器列表' },
    { key: 'GET_tribes', label: '部落列表' },
    { key: 'GET_users', label: '用户列表' },
    { key: 'GET_troop_types', label: '兵种类型' },
    { key: 'GET_troops_params', label: '兵种参数(1.46,1x)' }
  ], 
  // 写入接口清单：创建/更新实体，演示端到端流程
  writeList: [
    { key: 'POST_servers', label: '创建服务器' },
    { key: 'POST_tribes', label: '创建部落' },
    { key: 'POST_users', label: '创建用户' },
    { key: 'POST_accounts', label: '创建账号' },
    { key: 'POST_villages', label: '创建村庄' },
    { key: 'POST_troops_upload', label: '上传兵力' },
    { key: 'GET_troops_aggregate', label: '查看兵力汇总' },
    { key: 'POST_alliances', label: '创建联盟' },
    { key: 'GET_alliances_query', label: '查询联盟' },
    { key: 'GET_alliances_id', label: '查看联盟详情' },
    { key: 'POST_alliances_members', label: '添加联盟成员' },
    { key: 'GET_alliances_members', label: '查看联盟成员' },
    { key: 'PUT_alliances_id', label: '更新联盟描述' },
    { key: 'PUT_alliances_members', label: '更新成员角色' },
    { key: 'DELETE_alliances_members', label: '移除联盟成员' },
    { key: 'DELETE_alliances_id', label: '删除联盟' }
  ] },
  // 仅调用健康检查后端接口并展示 JSON 文本
  checkHealth: function() {
    wx.request({
      url: BASE_URL + '/health',
      method: 'GET',
      success: res => { this.setData({ health: typeof res.data === 'object' ? JSON.stringify(res.data) : String(res.data) }) },
      fail: () => { this.setData({ health: 'error' }) }
    })
  },
  onLoad: function() { this.checkHealth() },
  // 切换是否允许写入（勾选开关才允许执行写入测试）
  toggleWriteEnabled: function(e) { this.setData({ writeEnabled: !!(e && e.detail && e.detail.value) }) },
  // 执行一个只读接口测试（根据按钮绑定的 data-key 决定调用哪个 API）
  runOneRead: async function(e) {
    const key = e && e.currentTarget && e.currentTarget.dataset && e.currentTarget.dataset.key
    const setStatus = (k, status, summary) => {
      const s = this.data.endpointStatuses
      s[k] = { status, summary }
      this.setData({ endpointStatuses: s })
    }
    const req = (method, path, data) => new Promise((resolve, reject) => {
      wx.request({ url: BASE_URL + path, method, data, header: { 'Content-Type': 'application/json' }, success: res => resolve(res), fail: err => reject(err) })
    })
    const fmt = (k, d) => {
      if (d && typeof d === 'object') {
        if (k === 'GET_health' || k === 'GET_healthz' || k === 'GET_db_ping') { return (d.data && d.data.message) ? ('状态：' + d.data.message) : (d.success ? '成功' : '失败') }
        if (k === 'GET_servers' || k === 'GET_tribes' || k === 'GET_users' || k === 'GET_troop_types') {
          const arr = d.data
          const n = Array.isArray(arr) ? arr.length : (d.count || 0)
          return '列表条目：' + n
        }
        if (k === 'GET_troops_params') {
          const tribes = d.data && d.data.tribes
          return '部落数：' + (Array.isArray(tribes) ? tribes.length : 0)
        }
        return d.success ? '成功' : ('失败：' + (d.error || ''))
      }
      return String(d)
    }
    try {
      let r
      if (key === 'GET_health') r = await req('GET', '/health')
      else if (key === 'GET_healthz') r = await req('GET', '/healthz')
      else if (key === 'GET_db_ping') r = await req('GET', '/db/ping')
      else if (key === 'GET_troops_params') r = await req('GET', '/troops/params?version=1.46&speed=1x')
      else if (key === 'GET_servers') r = await req('GET', '/servers')
      else if (key === 'GET_tribes') r = await req('GET', '/tribes')
      else if (key === 'GET_users') r = await req('GET', '/users')
      else if (key === 'GET_troop_types') r = await req('GET', '/troop-types')
      if (r) setStatus(key, r.statusCode === 200 ? 'pass' : 'fail', fmt(key, r.data))
    } catch (e2) {
      setStatus(key, 'fail', String(e2 && e2.errMsg || e2))
    }
  },
  // 执行一个写入接口测试（会自动前置创建依赖实体，如服务器/用户等）
  runOneWrite: async function(e) {
    if (!this.data.writeEnabled) return
    const key = e && e.currentTarget && e.currentTarget.dataset && e.currentTarget.dataset.key
    const setStatus = (k, status, summary) => {
      const s = this.data.endpointStatuses
      s[k] = { status, summary }
      this.setData({ endpointStatuses: s })
    }
    const req = (method, path, data) => new Promise((resolve, reject) => {
      wx.request({ url: BASE_URL + path, method, data, header: { 'Content-Type': 'application/json' }, success: res => resolve(res), fail: err => reject(err) })
    })
    const fmt = (k, d) => {
      if (d && typeof d === 'object') {
        if (k === 'POST_servers') { const it = d.data || {}; return '服务器：id=' + (it.id || '') + ' code=' + (it.code || '') }
        if (k === 'POST_tribes') { const it = d.data || {}; return '部落：id=' + (it.id || '') + ' code=' + (it.code || '') }
        if (k === 'POST_users') { const it = d.data || {}; return '用户：id=' + (it.id || '') + ' 昵称=' + (it.nickname || '') }
        if (k === 'POST_accounts') { const it = d.data || {}; return '账号：id=' + (it.id || '') + ' 名称=' + (it.inGameName || '') }
        if (k === 'POST_villages') { const it = d.data || {}; return '村庄：id=' + (it.id || '') + ' 名称=' + (it.name || '') }
        if (k === 'POST_troops_upload') { const it = d.data || {}; return '上传结果：' + (it.written ? '已写入' : '未写入') }
        if (k === 'GET_troops_aggregate') { const it = d.data || {}; const m = Object.keys(it).length; return '兵种类型数：' + m }
        if (k === 'POST_alliances') { const it = d.data || {}; return '联盟：id=' + (it.id || '') + ' 名称=' + (it.name || '') }
        if (k === 'GET_alliances_query') { const arr = d.data; const n = Array.isArray(arr) ? arr.length : (d.count || 0); return '联盟数量：' + n }
        if (k === 'GET_alliances_id') { const it = d.data || {}; return '联盟详情：标签=' + (it.tag || '') }
        if (k === 'POST_alliances_members' || k === 'PUT_alliances_members') { const it = d.data || {}; return '成员：id=' + (it.id || '') + ' 角色=' + (it.role || '') }
        if (k === 'GET_alliances_members') { const arr = d.data; const n = Array.isArray(arr) ? arr.length : (d.count || 0); return '成员数量：' + n }
        if (k === 'PUT_alliances_id') { const it = d.data || {}; return '联盟更新：描述=' + (it.description || '') }
        if (k === 'DELETE_alliances_members' || k === 'DELETE_alliances_id') { const it = d.data || {}; return '删除：' + (it.deleted ? '成功' : '失败') }
        return d.success ? '成功' : ('失败：' + (d.error || ''))
      }
      return String(d)
    }
    this._ctx = this._ctx || {}
    const C = this._ctx
    try {
      let r
      if (key === 'POST_servers') {
        const code = 'srv_' + Date.now(); r = await req('POST', '/servers', { code }); C.serverId = r.data && r.data.data && r.data.data.id
      } else if (key === 'POST_tribes') {
        const tcode = 'tb_' + Date.now(); r = await req('POST', '/tribes', { code: tcode, name: tcode }); C.tribeId = r.data && r.data.data && r.data.data.id
      } else if (key === 'POST_users') {
        const nick = 'u_' + Date.now(); r = await req('POST', '/users', { nickname: nick }); C.userId = r.data && r.data.data && r.data.data.id
      } else if (key === 'POST_accounts') {
        if (!C.userId) { const nick = 'u_' + Date.now(); const rr = await req('POST', '/users', { nickname: nick }); C.userId = rr.data && rr.data.data && rr.data.data.id }
        if (!C.serverId) { const code = 'srv_' + Date.now(); const rr = await req('POST', '/servers', { code }); C.serverId = rr.data && rr.data.data && rr.data.data.id }
        if (!C.tribeId) { const tcode = 'tb_' + Date.now(); const rr = await req('POST', '/tribes', { code: tcode, name: tcode }); C.tribeId = rr.data && rr.data.data && rr.data.data.id }
        const accName = 'acc_' + Date.now(); r = await req('POST', '/accounts', { userId: C.userId, serverId: C.serverId, tribeId: C.tribeId, inGameName: accName }); C.accountId = r.data && r.data.data && r.data.data.id
      } else if (key === 'POST_villages') {
        if (!C.accountId) { const accName = 'acc_' + Date.now(); if (!C.userId || !C.serverId || !C.tribeId) { if (!C.userId) { const rr1 = await req('POST', '/users', { nickname: 'u_' + Date.now() }); C.userId = rr1.data && rr1.data.data && rr1.data.data.id } if (!C.serverId) { const rr2 = await req('POST', '/servers', { code: 'srv_' + Date.now() }); C.serverId = rr2.data && rr2.data.data && rr2.data.data.id } if (!C.tribeId) { const rr3 = await req('POST', '/tribes', { code: 'tb_' + Date.now(), name: 'tb_' + Date.now() }); C.tribeId = rr3.data && rr3.data.data && rr3.data.data.id } } const rr = await req('POST', '/accounts', { userId: C.userId, serverId: C.serverId, tribeId: C.tribeId, inGameName: accName }); C.accountId = rr.data && rr.data.data && rr.data.data.id }
        const vName = 'v_' + Date.now(); r = await req('POST', '/villages', { serverId: C.serverId, gameAccountId: C.accountId, name: vName, x: 0, y: 0 }); C.villageId = r.data && r.data.data && r.data.data.id
      } else if (key === 'POST_troops_upload') {
        if (!C.villageId) { const vName = 'v_' + Date.now(); if (!C.accountId) { const accName = 'acc_' + Date.now(); if (!C.userId) { const rr1 = await req('POST', '/users', { nickname: 'u_' + Date.now() }); C.userId = rr1.data && rr1.data.data && rr1.data.data.id } if (!C.serverId) { const rr2 = await req('POST', '/servers', { code: 'srv_' + Date.now() }); C.serverId = rr2.data && rr2.data.data && rr2.data.data.id } if (!C.tribeId) { const rr3 = await req('POST', '/tribes', { code: 'tb_' + Date.now(), name: 'tb_' + Date.now() }); C.tribeId = rr3.data && rr3.data.data && rr3.data.data.id } const rr4 = await req('POST', '/accounts', { userId: C.userId, serverId: C.serverId, tribeId: C.tribeId, inGameName: accName }); C.accountId = rr4.data && rr4.data.data && rr4.data.data.id } const rr5 = await req('POST', '/villages', { serverId: C.serverId, gameAccountId: C.accountId, name: vName, x: 0, y: 0 }); C.villageId = rr5.data && rr5.data.data && rr5.data.data.id }
        const tr = await req('GET', `/troop-types?tribeId=${C.tribeId}`); const types = tr.data && tr.data.data; const firstTypeId = Array.isArray(types) && types.length ? types[0].id : 1
        r = await req('POST', '/troops/upload', { villageId: C.villageId, counts: { [firstTypeId]: 10 } })
      } else if (key === 'GET_troops_aggregate') {
        if (!C.villageId) return setStatus(key, 'fail', '需要先创建村庄'); r = await req('GET', `/troops/aggregate?villageId=${C.villageId}`)
      } else if (key === 'POST_alliances') {
        if (!C.serverId) { const rr2 = await req('POST', '/servers', { code: 'srv_' + Date.now() }); C.serverId = rr2.data && rr2.data.data && rr2.data.data.id }
        if (!C.userId) { const rr1 = await req('POST', '/users', { nickname: 'u_' + Date.now() }); C.userId = rr1.data && rr1.data.data && rr1.data.data.id }
        const aname = 'al_' + Date.now(); r = await req('POST', '/alliances', { serverId: C.serverId, name: aname, tag: aname, createdBy: C.userId }); C.allianceId = r.data && r.data.data && r.data.data.id
      } else if (key === 'GET_alliances_query') {
        if (!C.serverId) return setStatus(key, 'fail', '需要先创建服务器'); const name = 'al_' + Date.now(); const rr = await req('GET', `/alliances?serverId=${C.serverId}&name=${name}`); r = rr
      } else if (key === 'GET_alliances_id') {
        if (!C.allianceId) return setStatus(key, 'fail', '需要先创建联盟'); r = await req('GET', `/alliances/${C.allianceId}`)
      } else if (key === 'POST_alliances_members') {
        if (!C.allianceId || !C.accountId) return setStatus(key, 'fail', '需要先创建联盟与账号'); r = await req('POST', `/alliances/${C.allianceId}/members`, { gameAccountId: C.accountId, role: 'member' }); C.memberId = r.data && r.data.data && r.data.data.id
      } else if (key === 'GET_alliances_members') {
        if (!C.allianceId) return setStatus(key, 'fail', '需要先创建联盟'); r = await req('GET', `/alliances/${C.allianceId}/members`)
      } else if (key === 'PUT_alliances_id') {
        if (!C.allianceId) return setStatus(key, 'fail', '需要先创建联盟'); r = await req('PUT', `/alliances/${C.allianceId}`, { description: 'd' + Date.now() })
      } else if (key === 'PUT_alliances_members') {
        if (!C.memberId || !C.allianceId) return setStatus(key, 'fail', '需要先添加成员'); r = await req('PUT', `/alliances/${C.allianceId}/members/${C.memberId}`, { role: 'leader' })
      } else if (key === 'DELETE_alliances_members') {
        if (!C.memberId || !C.allianceId) return setStatus(key, 'fail', '需要先添加成员'); r = await req('DELETE', `/alliances/${C.allianceId}/members/${C.memberId}`)
      } else if (key === 'DELETE_alliances_id') {
        if (!C.allianceId) return setStatus(key, 'fail', '需要先创建联盟'); r = await req('DELETE', `/alliances/${C.allianceId}`)
      }
      if (r) setStatus(key, (r.statusCode === 200 && (r.data && (r.data.success !== false))) ? 'pass' : 'fail', fmt(key, r.data))
    } catch (e2) {
      setStatus(key, 'fail', String(e2 && e2.errMsg || e2))
    }
  },
  // 批量执行只读接口测试（按固定顺序）
  runReadTests: async function() {
    const addResult = (name, status, summary) => {
      const list = this.data.testResults.concat([{ name, status, summary: typeof summary === 'string' ? summary : JSON.stringify(summary) }])
      this.setData({ testResults: list })
    }
    const req = (method, path, data) => new Promise((resolve, reject) => {
      wx.request({ url: BASE_URL + path, method, data, header: { 'Content-Type': 'application/json' }, success: res => resolve(res), fail: err => reject(err) })
    })
    try {
      let r
      r = await req('GET', '/health')
      addResult('GET /health', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/healthz')
      addResult('GET /healthz', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/db/ping')
      addResult('GET /db/ping', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/troops/params?version=1.46&speed=1x')
      addResult('GET /troops/params', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/servers')
      addResult('GET /servers', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/tribes')
      addResult('GET /tribes', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/users')
      addResult('GET /users', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/troop-types')
      addResult('GET /troop-types', r.statusCode === 200 ? 'pass' : 'fail', r.data)
    } catch (e) {
      addResult('仅读接口测试错误', 'fail', String(e && e.errMsg || e))
    }
  },
  // 批量执行写入接口测试（创建服务器、部落、用户、账号、村庄、兵力、联盟、成员等）
  runWriteTests: async function() {
    const addResult = (name, status, summary) => {
      const list = this.data.testResults.concat([{ name, status, summary: typeof summary === 'string' ? summary : JSON.stringify(summary) }])
      this.setData({ testResults: list })
    }
    const req = (method, path, data) => new Promise((resolve, reject) => {
      wx.request({ url: BASE_URL + path, method, data, header: { 'Content-Type': 'application/json' }, success: res => resolve(res), fail: err => reject(err) })
    })
    const ctx = {}
    try {
      let r
      const code = 'srv_' + Date.now()
      r = await req('POST', '/servers', { code })
      addResult('POST /servers', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.serverId = r.data && r.data.data && r.data.data.id
      r = await req('GET', '/servers')
      addResult('GET /servers', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', '/tribes')
      addResult('GET /tribes', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      const tribeList = r.data && r.data.data
      ctx.tribeId = Array.isArray(tribeList) && tribeList.length ? tribeList[0].id : undefined
      const tcode = 'tb_' + Date.now()
      r = await req('POST', '/tribes', { code: tcode, name: tcode })
      addResult('POST /tribes', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      if (!ctx.tribeId) ctx.tribeId = r.data && r.data.data && r.data.data.id
      const nick = 'u_' + Date.now()
      r = await req('POST', '/users', { nickname: nick })
      addResult('POST /users', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.userId = r.data && r.data.data && r.data.data.id
      r = await req('GET', '/users')
      addResult('GET /users', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      const accName = 'acc_' + Date.now()
      r = await req('POST', '/accounts', { userId: ctx.userId, serverId: ctx.serverId, tribeId: ctx.tribeId, inGameName: accName })
      addResult('POST /accounts', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.accountId = r.data && r.data.data && r.data.data.id
      r = await req('GET', `/accounts?userId=${ctx.userId}`)
      addResult('GET /accounts', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      const vName = 'v_' + Date.now()
      r = await req('POST', '/villages', { serverId: ctx.serverId, gameAccountId: ctx.accountId, name: vName, x: 0, y: 0 })
      addResult('POST /villages', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.villageId = r.data && r.data.data && r.data.data.id
      r = await req('GET', `/villages?serverId=${ctx.serverId}`)
      addResult('GET /villages', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', `/troop-types?tribeId=${ctx.tribeId}`)
      addResult('GET /troop-types', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      const types = r.data && r.data.data
      const firstTypeId = Array.isArray(types) && types.length ? types[0].id : 1
      r = await req('POST', '/troops/upload', { villageId: ctx.villageId, counts: { [firstTypeId]: 10 } })
      addResult('POST /troops/upload', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      r = await req('GET', `/troops/aggregate?villageId=${ctx.villageId}`)
      addResult('GET /troops/aggregate', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      const aname = 'al_' + Date.now()
      r = await req('POST', '/alliances', { serverId: ctx.serverId, name: aname, tag: aname, createdBy: ctx.userId })
      addResult('POST /alliances', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.allianceId = r.data && r.data.data && r.data.data.id
      r = await req('GET', `/alliances?serverId=${ctx.serverId}&name=${aname}`)
      addResult('GET /alliances', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('GET', `/alliances/${ctx.allianceId}`)
      addResult('GET /alliances/{id}', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('POST', `/alliances/${ctx.allianceId}/members`, { gameAccountId: ctx.accountId, role: 'member' })
      addResult('POST /alliances/{id}/members', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      ctx.memberId = r.data && r.data.data && r.data.data.id
      r = await req('GET', `/alliances/${ctx.allianceId}/members`)
      addResult('GET /alliances/{id}/members', r.statusCode === 200 ? 'pass' : 'fail', r.data)
      r = await req('PUT', `/alliances/${ctx.allianceId}`, { description: 'd' + Date.now() })
      addResult('PUT /alliances/{id}', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      r = await req('PUT', `/alliances/${ctx.allianceId}/members/${ctx.memberId}`, { role: 'leader' })
      addResult('PUT /alliances/{id}/members/{mid}', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      r = await req('DELETE', `/alliances/${ctx.allianceId}/members/${ctx.memberId}`)
      addResult('DELETE /alliances/{id}/members/{mid}', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
      r = await req('DELETE', `/alliances/${ctx.allianceId}`)
      addResult('DELETE /alliances/{id}', r.statusCode === 200 && r.data && r.data.success ? 'pass' : 'fail', r.data)
    } catch (e) {
      addResult('写入接口测试错误', 'fail', String(e && e.errMsg || e))
    }
  },
  // 一键执行所有测试：先读接口，再根据开关决定是否执行写入接口
  runAllTests: async function() {
    await this.runReadTests()
    if (this.data.writeEnabled) { await this.runWriteTests() }
  }
})
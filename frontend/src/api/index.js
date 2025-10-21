import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 200) {
      return res
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  error => {
    console.error('响应错误:', error)
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

// API接口
export const chatAPI = {
  // 发送消息
  sendMessage(data) {
    return request.post('/chat', data)
  }
}

export const knowledgeAPI = {
  // 获取知识库列表
  getList(params) {
    return request.get('/knowledge', { params })
  },
  
  // 创建知识
  create(data) {
    return request.post('/knowledge', data)
  },
  
  // 更新知识
  update(id, data) {
    return request.put(`/knowledge/${id}`, data)
  },
  
  // 删除知识
  delete(id) {
    return request.delete(`/knowledge/${id}`)
  },
  
  // 搜索知识
  search(keyword) {
    return request.get('/knowledge/search', { params: { q: keyword } })
  }
}

export default request


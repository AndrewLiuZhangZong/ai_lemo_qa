<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>💬 智能问答助手</h2>
      <p>有什么可以帮到您？</p>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <el-icon :size="60" color="#909399"><ChatDotRound /></el-icon>
        <p>开始对话吧！我会尽力帮助您</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-item', msg.type]"
      >
        <div class="message-avatar">
          <el-icon :size="24" v-if="msg.type === 'user'"><User /></el-icon>
          <el-icon :size="24" v-else><Service /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-bubble">
            {{ msg.content }}
          </div>
          <div v-if="msg.type === 'bot'" class="message-meta">
            <el-tag size="small" :type="msg.answerSource === 'knowledge_base' ? 'success' : msg.answerSource === 'web_search' ? 'primary' : 'warning'">
              {{ msg.answerSource === 'knowledge_base' ? '📚 知识库' : msg.answerSource === 'web_search' ? '🌐 网络搜索' : '🤖 AI推理' }}
            </el-tag>
            <el-tag size="small" type="info" v-if="msg.confidence > 0">
              置信度: {{ (msg.confidence * 100).toFixed(1) }}%
            </el-tag>
            <el-tag size="small" type="success" v-if="msg.intent">{{ msg.intent }}</el-tag>
          </div>
          <div v-if="msg.sources && msg.sources.length > 0 && msg.sources[0].url" class="search-sources">
            <p class="sources-title">🔗 参考来源：</p>
            <div v-for="(source, i) in msg.sources" :key="i" class="source-item">
              <a :href="source.url" target="_blank" class="source-link">
                {{ i + 1 }}. {{ source.title || source.url }}
              </a>
            </div>
          </div>
          <div v-if="msg.relatedQuestions && msg.relatedQuestions.length > 0" class="related-questions">
            <p class="related-title">相关问题：</p>
            <el-tag
              v-for="(q, i) in msg.relatedQuestions"
              :key="i"
              class="related-tag"
              @click="sendRelatedQuestion(q)"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message-item bot">
        <div class="message-avatar">
          <el-icon :size="24"><Service /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-bubble typing">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <div class="input-wrapper">
        <div class="input-container">
          <el-icon class="input-icon" :size="20"><ChatLineRound /></el-icon>
          <el-autocomplete
            v-model="inputMessage"
            :fetch-suggestions="queryHistory"
            placeholder="输入您的问题，按回车发送..."
            @keyup.enter="sendMessage"
            @select="handleHistorySelect"
            :disabled="loading"
            size="large"
            class="chat-input-field"
            :popper-class="'history-popper'"
            clearable
          >
            <template #default="{ item }">
              <div class="history-item">
                <el-icon class="history-icon"><Clock /></el-icon>
                <span class="history-text">{{ item.value }}</span>
              </div>
            </template>
          </el-autocomplete>
        </div>
        <el-button
          class="send-button"
          @click="sendMessage"
          :loading="loading"
          type="primary"
          size="large"
          :disabled="!inputMessage.trim()"
        >
          <el-icon v-if="!loading" :size="20"><Position /></el-icon>
          <span>{{ loading ? '发送中...' : '发送' }}</span>
        </el-button>
      </div>
      <div class="input-tips">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>💡 支持知识库查询、网络搜索和AI问答</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Position, Clock, InfoFilled, ChatLineRound } from '@element-plus/icons-vue'
import { chatAPI } from '@/api'
import { ElMessage } from 'element-plus'

const HISTORY_KEY = 'chat_history'
const MAX_HISTORY = 10

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(`session-${Date.now()}`)
const questionHistory = ref([])

// 从localStorage加载历史记录
const loadHistory = () => {
  try {
    const saved = localStorage.getItem(HISTORY_KEY)
    if (saved) {
      questionHistory.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

// 保存历史记录到localStorage
const saveHistory = (question) => {
  try {
    // 移除重复项
    questionHistory.value = questionHistory.value.filter(q => q !== question)
    // 添加到开头
    questionHistory.value.unshift(question)
    // 限制最多10条
    if (questionHistory.value.length > MAX_HISTORY) {
      questionHistory.value = questionHistory.value.slice(0, MAX_HISTORY)
    }
    // 保存到localStorage
    localStorage.setItem(HISTORY_KEY, JSON.stringify(questionHistory.value))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

// 查询历史记录（用于autocomplete）
const queryHistory = (queryString, cb) => {
  const results = queryString
    ? questionHistory.value
        .filter(q => q.toLowerCase().includes(queryString.toLowerCase()))
        .map(q => ({ value: q }))
    : questionHistory.value.map(q => ({ value: q }))
  cb(results)
}

// 选择历史记录
const handleHistorySelect = (item) => {
  inputMessage.value = item.value
  sendMessage()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  
  // 保存到历史记录
  saveHistory(userMessage)
  
  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: userMessage
  })
  
  inputMessage.value = ''
  scrollToBottom()
  
  loading.value = true
  
  try {
    const response = await chatAPI.sendMessage({
      message: userMessage,
      session_id: sessionId.value
    })
    
    const data = response.data
    
    // 添加机器人回复
    messages.value.push({
      type: 'bot',
      content: data.answer,
      confidence: data.confidence,
      intent: data.intent,
      sources: data.sources,
      relatedQuestions: data.related_questions,
      answerSource: data.answer_source
    })
    
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送失败，请重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const sendRelatedQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: white;
}

.chat-header {
  padding: 20px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-header h2 {
  margin: 0 0 5px 0;
  font-size: 24px;
}

.chat-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-state p {
  margin-top: 20px;
  font-size: 16px;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: white;
  margin: 0 10px;
}

.message-item.user .message-avatar {
  background: #67c23a;
}

.message-content {
  max-width: 60%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-item.user .message-bubble {
  background: #67c23a;
  color: white;
}

.message-item.bot .message-bubble {
  background: white;
  color: #303133;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-bubble.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 15px 20px;
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.message-meta {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.related-questions {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.related-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.related-tag {
  margin: 4px 8px 4px 0;
  cursor: pointer;
  transition: all 0.3s;
}

.related-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.search-sources {
  margin-top: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 13px;
}

.sources-title {
  margin: 0 0 8px 0;
  font-weight: 500;
  color: #606266;
}

.source-item {
  margin: 4px 0;
}

.source-link {
  color: #409eff;
  text-decoration: none;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-link:hover {
  text-decoration: underline;
  color: #66b1ff;
}

.chat-input {
  padding: 20px 30px;
  background: white;
  border-top: 1px solid #e4e7ed;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
}

.input-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 24px;
  padding: 0 20px;
  transition: all 0.3s;
}

.input-container:focus-within {
  background: white;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15);
}

.input-icon {
  color: #909399;
  margin-right: 12px;
  flex-shrink: 0;
}

.chat-input-field {
  flex: 1;
}

:deep(.chat-input-field .el-input__wrapper) {
  background: transparent;
  box-shadow: none;
  padding: 8px 0;
}

:deep(.chat-input-field .el-input__inner) {
  font-size: 15px;
  color: #303133;
}

:deep(.chat-input-field .el-input__inner::placeholder) {
  color: #a8abb2;
}

.send-button {
  padding: 12px 28px;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.send-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.send-button:active {
  transform: translateY(0);
}

.send-button.is-disabled {
  background: #e4e7ed;
  color: #a8abb2;
  box-shadow: none;
  cursor: not-allowed;
}

.send-button.is-loading {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0.8;
}

.input-tips {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  padding-left: 4px;
}

.input-tips .el-icon {
  color: #409eff;
}

/* 历史记录下拉框样式 */
:deep(.history-popper) {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

:deep(.history-popper .el-autocomplete-suggestion__list) {
  padding: 8px;
}

:deep(.history-popper .el-autocomplete-suggestion__wrap) {
  max-height: 320px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-icon {
  color: #909399;
  flex-shrink: 0;
}

.history-text {
  flex: 1;
  color: #606266;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.history-popper .el-autocomplete-suggestion__list .is-highlighted) {
  background: #ecf5ff;
}

:deep(.history-popper .el-autocomplete-suggestion__list .is-highlighted .history-item) {
  background: transparent;
}

:deep(.history-popper .el-autocomplete-suggestion__list .is-highlighted .history-text) {
  color: #409eff;
}
</style>


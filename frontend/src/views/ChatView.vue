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
            <el-tag size="small" :type="msg.answerSource === 'knowledge_base' ? 'success' : 'warning'">
              {{ msg.answerSource === 'knowledge_base' ? '📚 知识库' : '🤖 AI推理' }}
            </el-tag>
            <el-tag size="small" type="info" v-if="msg.sources && msg.sources.length > 0">
              置信度: {{ (msg.confidence * 100).toFixed(1) }}%
            </el-tag>
            <el-tag size="small" type="success" v-if="msg.intent">{{ msg.intent }}</el-tag>
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
      <el-input
        v-model="inputMessage"
        placeholder="输入您的问题..."
        @keyup.enter="sendMessage"
        :disabled="loading"
        size="large"
      >
        <template #append>
          <el-button
            :icon="Position"
            @click="sendMessage"
            :loading="loading"
            type="primary"
          >
            发送
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Position } from '@element-plus/icons-vue'
import { chatAPI } from '@/api'
import { ElMessage } from 'element-plus'

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(`session-${Date.now()}`)

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

.chat-input {
  padding: 20px 30px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

:deep(.el-input-group__append) {
  background: #409eff;
  border: none;
  padding: 0;
}

:deep(.el-input-group__append .el-button) {
  margin: 0;
}
</style>


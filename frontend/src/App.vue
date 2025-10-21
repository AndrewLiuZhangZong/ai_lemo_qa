<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <el-icon :size="32"><ChatDotRound /></el-icon>
          <h2>AI客服</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="menu"
          router
          @select="handleMenuSelect"
        >
          <el-menu-item index="/chat">
            <el-icon><ChatLineRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Collection /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = ref('/chat')

onMounted(() => {
  activeMenu.value = route.path
})

const handleMenuSelect = (index) => {
  activeMenu.value = index
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100vh;
  overflow: hidden;
}

.layout-container {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin-top: 10px;
  font-size: 20px;
  font-weight: 600;
}

.menu {
  flex: 1;
  border: none;
  background: transparent;
}

.el-menu-item {
  color: rgba(255, 255, 255, 0.8) !important;
  font-size: 15px;
}

.el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: white !important;
}

.el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.main-content {
  padding: 0;
  height: 100%;
  overflow: auto;
  background: #f5f7fa;
}
</style>


# AI智能客服问答系统 - 前端

基于 Vue 3 + Element Plus 的现代化前端界面

## 功能特性

### 1. 智能问答
- ✨ 实时对话界面
- 💡 智能回答推荐
- 📊 置信度和意图识别显示
- 🔄 相关问题推荐
- 📝 对话历史保存

### 2. 知识库管理
- 📚 知识列表展示
- ➕ 添加/编辑/删除知识
- 🔍 关键词搜索
- 📋 分类管理
- 📄 分页浏览

## 技术栈

- **框架**: Vue 3 (Composition API)
- **UI库**: Element Plus
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **路由**: Vue Router

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发运行

```bash
npm run dev
```

访问：http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口封装
│   ├── components/       # 通用组件
│   ├── views/            # 页面视图
│   │   ├── ChatView.vue      # 聊天页面
│   │   └── KnowledgeView.vue # 知识库管理
│   ├── router/           # 路由配置
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML模板
├── vite.config.js       # Vite配置
└── package.json         # 依赖配置
```

## 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

## 开发说明

### API代理配置

在 `vite.config.js` 中配置了API代理：

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
  }
}
```

确保后端服务运行在 `http://localhost:8080`

### 界面预览

#### 智能问答
- 现代化的聊天界面
- 实时消息展示
- 打字动画效果
- 相关问题快速选择

#### 知识库管理
- 表格化展示
- 搜索和筛选
- 快速编辑
- 批量操作

## 部署建议

### 使用 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 许可证

MIT License


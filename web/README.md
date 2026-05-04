# Web前端界面

## 技术栈

- Vue 3
- element-ai-vue 组件库
- Vite 构建工具

## 启动步骤

### 1. 配置地图密钥

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入高德地图 Web API 的 Key 和 Security Code：

```
VITE_AMAP_KEY=your_amap_web_api_key_here
VITE_AMAP_SECURITY_CODE=your_amap_security_code_here
```

### 2. 安装依赖

```bash
cd web
npm install
```

### 3. 启动OpenCode服务器

在项目根目录运行：

```bash
opencode serve --cors http://localhost:8080
```

说明：
- `--cors` 参数允许前端页面跨域访问
- 默认端口 4096

### 4. 启动Web服务器

```bash
npm run dev
```

### 5. 访问界面

打开浏览器访问：`http://localhost:8080`

## 功能说明

- 左侧悬浮面板：与 gis-orchestrator 智能体对话
- 底层：地图界面
- 支持新建会话、发送消息

## 目录结构

```
web/
├── index.html        # 入口页面
├── package.json     # 项目配置
├── vite.config.js   # Vite配置
└── src/
    ├── main.js      # 入口文件
    ├── App.vue      # 根组件
    └── components/
        ├── ChatPanel.vue   # 对话面板
        └── MapContainer.vue # 地图容器
```
# Web前端界面

## 技术栈

- Vue 3
- element-ai-vue 组件库
- Vite 构建工具

## 启动步骤

### 1. 安装依赖

```bash
cd web
npm install
```

### 2. 启动OpenCode服务器

在项目根目录运行：

```bash
opencode serve --cors http://localhost:8080
```

说明：
- `--cors` 参数允许前端页面跨域访问
- 默认端口 4096

### 3. 启动Web服务器

```bash
npm run dev
```

### 4. 访问界面

打开浏览器访问：`http://localhost:8080`

## 功能说明

- 左侧悬浮面板：与 gis-orchestrator 智能体对话
- 底层：地图界面（暂未实现）
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
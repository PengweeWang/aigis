import { createApp } from 'vue'
import ElementAI from 'element-ai-vue'
import 'element-ai-vue/dist/index.css'
import App from './App.vue'

const app = createApp(App)
app.use(ElementAI)
app.mount('#app')
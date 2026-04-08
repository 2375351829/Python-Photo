<template>
  <div class="debug-log-panel">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>实时日志</span>
          <div class="header-actions">
            <el-select v-model="logLevel" size="small" style="width: 100px">
              <el-option label="全部" value="" />
              <el-option label="DEBUG" value="debug" />
              <el-option label="INFO" value="info" />
              <el-option label="WARNING" value="warning" />
              <el-option label="ERROR" value="error" />
            </el-select>
            <el-button size="small" @click="clearLogs">清空</el-button>
          </div>
        </div>
      </template>
      
      <div class="log-container" ref="logContainer">
        <div
          v-for="(log, index) in filteredLogs"
          :key="index"
          :class="['log-item', `log-${log.level}`]"
        >
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="filteredLogs.length === 0" class="no-logs">
          暂无日志
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  taskId: {
    type: Number,
    default: null
  }
})

const logs = ref([])
const logLevel = ref('')
const logContainer = ref(null)
let ws = null

const filteredLogs = computed(() => {
  if (!logLevel.value) return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

const addLog = (log) => {
  logs.value.push({
    timestamp: new Date().toLocaleTimeString(),
    level: log.level || 'info',
    message: log.message
  })
  
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  logs.value = []
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/logs`
  
  ws = new WebSocket(wsUrl)
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (props.taskId && data.task_id !== props.taskId) return
    addLog(data)
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    addLog({ level: 'error', message: 'WebSocket连接错误' })
  }
  
  ws.onclose = () => {
    addLog({ level: 'warning', message: 'WebSocket连接已关闭' })
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

defineExpose({
  addLog,
  clearLogs
})
</script>

<style scoped>
.debug-log-panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.log-container {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-item {
  padding: 4px 0;
  border-bottom: 1px solid #333;
}

.log-time {
  color: #888;
  margin-right: 10px;
}

.log-level {
  margin-right: 10px;
  font-weight: bold;
}

.log-message {
  color: #d4d4d4;
}

.log-debug .log-level { color: #608b4e; }
.log-info .log-level { color: #4ec9b0; }
.log-warning .log-level { color: #dcdcaa; }
.log-error .log-level { color: #f14c4c; }

.no-logs {
  color: #888;
  text-align: center;
  padding: 20px;
}
</style>

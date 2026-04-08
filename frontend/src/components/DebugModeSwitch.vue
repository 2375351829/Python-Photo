<template>
  <div class="debug-mode-switch">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>调试模式</span>
          <el-switch v-model="debugEnabled" @change="handleToggle" />
        </div>
      </template>
      
      <div v-if="debugEnabled" class="debug-options">
        <el-divider content-position="left">断点设置</el-divider>
        
        <div class="breakpoint-list">
          <el-tag
            v-for="bp in breakpoints"
            :key="bp"
            closable
            @close="removeBreakpoint(bp)"
            class="breakpoint-tag"
          >
            步骤 {{ bp }}
          </el-tag>
          <el-tag v-if="breakpoints.length === 0" type="info">暂无断点</el-tag>
        </div>
        
        <div class="add-breakpoint">
          <el-input-number
            v-model="newBreakpoint"
            :min="0"
            :max="1000"
            placeholder="步骤编号"
          />
          <el-button type="primary" @click="addBreakpoint">添加断点</el-button>
        </div>
        
        <el-divider content-position="left">执行控制</el-divider>
        
        <div class="control-buttons">
          <el-button
            type="success"
            :disabled="!isPaused"
            @click="stepForward"
          >
            单步执行
          </el-button>
          <el-button
            type="warning"
            :disabled="!isPaused"
            @click="continueExecution"
          >
            继续执行
          </el-button>
        </div>
        
        <el-divider content-position="left">当前状态</el-divider>
        
        <div class="status-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="当前步骤">{{ currentStep }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="isPaused ? 'warning' : 'success'">
                {{ isPaused ? '已暂停' : '运行中' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  taskId: {
    type: Number,
    required: true
  }
})

const debugEnabled = ref(false)
const breakpoints = ref([])
const newBreakpoint = ref(0)
const currentStep = ref(0)
const isPaused = ref(false)

const handleToggle = async (val) => {
  try {
    if (val) {
      await fetch(`/api/debug/${props.taskId}/enable`, { method: 'POST' })
      ElMessage.success('调试模式已启用')
    } else {
      await fetch(`/api/debug/${props.taskId}/disable`, { method: 'POST' })
      ElMessage.info('调试模式已禁用')
    }
  } catch (error) {
    ElMessage.error('操作失败')
    debugEnabled.value = !val
  }
}

const addBreakpoint = async () => {
  if (newBreakpoint.value < 0) return
  
  try {
    await fetch(`/api/debug/${props.taskId}/breakpoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step: newBreakpoint.value })
    })
    if (!breakpoints.value.includes(newBreakpoint.value)) {
      breakpoints.value.push(newBreakpoint.value)
      breakpoints.value.sort((a, b) => a - b)
    }
    ElMessage.success(`断点已设置: 步骤 ${newBreakpoint.value}`)
  } catch (error) {
    ElMessage.error('设置断点失败')
  }
}

const removeBreakpoint = async (step) => {
  try {
    await fetch(`/api/debug/${props.taskId}/breakpoint/${step}`, { method: 'DELETE' })
    breakpoints.value = breakpoints.value.filter(bp => bp !== step)
    ElMessage.info(`断点已移除: 步骤 ${step}`)
  } catch (error) {
    ElMessage.error('移除断点失败')
  }
}

const stepForward = async () => {
  try {
    await fetch(`/api/debug/${props.taskId}/step`, { method: 'POST' })
    ElMessage.success('已执行单步')
    loadStatus()
  } catch (error) {
    ElMessage.error('单步执行失败')
  }
}

const continueExecution = async () => {
  try {
    await fetch(`/api/debug/${props.taskId}/continue`, { method: 'POST' })
    ElMessage.success('继续执行')
    loadStatus()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const loadStatus = async () => {
  try {
    const response = await fetch(`/api/debug/${props.taskId}/status`)
    const data = await response.json()
    debugEnabled.value = data.enabled
    currentStep.value = data.current_step
    isPaused.value = data.paused
    breakpoints.value = data.breakpoints || []
  } catch (error) {
    console.error('Failed to load debug status:', error)
  }
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.debug-mode-switch {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.debug-options {
  padding: 10px 0;
}

.breakpoint-list {
  margin-bottom: 15px;
}

.breakpoint-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.add-breakpoint {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.control-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.status-info {
  margin-top: 10px;
}
</style>

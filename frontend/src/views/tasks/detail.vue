<template>
  <div class="task-detail-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务详情</span>
          <div class="header-actions">
            <el-button type="primary" @click="editTask">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              type="success" 
              @click="executeTaskHandler" 
              :disabled="task.status === 'running'"
            >
              <el-icon><VideoPlay /></el-icon>
              执行
            </el-button>
            <el-button 
              type="warning" 
              @click="stopTaskHandler" 
              :disabled="task.status !== 'running'"
            >
              <el-icon><VideoPause /></el-icon>
              停止
            </el-button>
            <el-button type="danger" @click="deleteTaskHandler">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
            <el-button @click="$router.back()">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item label="目标URL" :span="2">
          <el-link :href="task.url" target="_blank" type="primary">{{ task.url }}</el-link>
        </el-descriptions-item>
        <el-descriptions-item label="目标类型">
          <el-tag v-for="type in task.targetTypes" :key="type" size="small" class="type-tag">
            {{ getTargetTypeText(type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="爬取深度">{{ task.depth }}</el-descriptions-item>
        <el-descriptions-item label="最大结果数">{{ task.maxResults }}</el-descriptions-item>
        <el-descriptions-item label="结果数量">{{ task.resultCount }}</el-descriptions-item>
        <el-descriptions-item label="请求间隔">{{ task.requestInterval }}ms</el-descriptions-item>
        <el-descriptions-item label="超时时间">{{ task.timeout }}ms</el-descriptions-item>
        <el-descriptions-item label="调试模式">
          <el-tag :type="task.debugMode ? 'success' : 'info'">
            {{ task.debugMode ? '开启' : '关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行方式">
          {{ task.scheduleType === 'immediate' ? '立即执行' : '定时执行' }}
        </el-descriptions-item>
        <el-descriptions-item label="Cron表达式" v-if="task.scheduleType === 'scheduled'">
          {{ task.cronExpression || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ task.createdAt }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ task.completedAt || '-' }}</el-descriptions-item>
        <el-descriptions-item label="保存路径" :span="2">{{ task.savePath || '-' }}</el-descriptions-item>
        <el-descriptions-item label="任务描述" :span="2">{{ task.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="rules-card">
      <template #header>
        <span>爬取规则配置</span>
      </template>
      <el-tabs v-model="activeRuleTab">
        <el-tab-pane label="CSS选择器" name="css">
          <el-table :data="task.rules?.css || []" v-if="task.rules?.css?.length">
            <el-table-column prop="name" label="规则名称" width="200" />
            <el-table-column prop="selector" label="选择器" />
          </el-table>
          <el-empty v-else description="暂无CSS选择器规则" :image-size="60" />
        </el-tab-pane>
        <el-tab-pane label="XPath规则" name="xpath">
          <el-table :data="task.rules?.xpath || []" v-if="task.rules?.xpath?.length">
            <el-table-column prop="name" label="规则名称" width="200" />
            <el-table-column prop="selector" label="XPath表达式" />
          </el-table>
          <el-empty v-else description="暂无XPath规则" :image-size="60" />
        </el-tab-pane>
        <el-tab-pane label="正则表达式" name="regex">
          <el-table :data="task.rules?.regex || []" v-if="task.rules?.regex?.length">
            <el-table-column prop="name" label="规则名称" width="200" />
            <el-table-column prop="pattern" label="正则表达式" />
          </el-table>
          <el-empty v-else description="暂无正则表达式规则" :image-size="60" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="executions-card">
      <template #header>
        <div class="section-header">
          <span>执行历史</span>
          <el-button size="small" @click="fetchExecutions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <el-table :data="executions" v-loading="executionsLoading" stripe>
        <el-table-column prop="id" label="执行ID" width="100" />
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column prop="endTime" label="结束时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resultCount" label="结果数量" width="100" />
        <el-table-column prop="duration" label="耗时" width="120">
          <template #default="{ row }">
            {{ row.duration ? `${row.duration}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="errorMessage" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.errorMessage" class="error-text">{{ row.errorMessage }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="executionsPagination.page"
        v-model:page-size="executionsPagination.pageSize"
        :total="executionsPagination.total"
        :page-sizes="[5, 10, 20]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @size-change="fetchExecutions"
        @current-change="fetchExecutions"
      />
    </el-card>

    <el-card class="results-card">
      <template #header>
        <div class="section-header">
          <span>爬取结果</span>
          <div class="header-right">
            <el-select v-model="resultType" placeholder="筛选类型" size="small" clearable style="width: 120px; margin-right: 10px;">
              <el-option label="全部" value="" />
              <el-option label="图片" value="image" />
              <el-option label="视频" value="video" />
              <el-option label="文本" value="text" />
              <el-option label="链接" value="link" />
              <el-option label="文件" value="file" />
            </el-select>
            <el-button size="small" @click="fetchResults">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="results" v-loading="resultsLoading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ getTargetTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link :href="row.url" target="_blank" type="primary">{{ row.url }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" width="200" show-overflow-tooltip />
        <el-table-column prop="fileSize" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.fileSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="爬取时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="previewResult(row)" v-if="row.type === 'image'">
              预览
            </el-button>
            <el-button link type="primary" @click="downloadResult(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="resultsPagination.page"
        v-model:page-size="resultsPagination.pageSize"
        :total="resultsPagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @size-change="fetchResults"
        @current-change="fetchResults"
      />
    </el-card>

    <el-card class="log-card">
      <template #header>
        <div class="section-header">
          <span>执行日志</span>
          <el-button size="small" @click="fetchLogs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <div class="log-content">
        <pre>{{ task.logs || '暂无日志' }}</pre>
      </div>
    </el-card>

    <el-dialog v-model="previewVisible" title="图片预览" width="800px">
      <img :src="previewUrl" style="width: 100%;" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, VideoPlay, VideoPause, Back, Refresh } from '@element-plus/icons-vue'
import { getTask, deleteTask, executeTask, stopTask, getTaskExecutions, getTaskResults } from '@/api/task'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const executionsLoading = ref(false)
const resultsLoading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')
const activeRuleTab = ref('css')
const resultType = ref('')

const task = ref({
  id: null,
  name: '',
  url: '',
  targetTypes: [],
  status: 'pending',
  depth: 2,
  maxResults: 1000,
  resultCount: 0,
  requestInterval: 500,
  timeout: 30000,
  debugMode: false,
  scheduleType: 'immediate',
  cronExpression: '',
  savePath: '',
  description: '',
  rules: {
    css: [],
    xpath: [],
    regex: []
  },
  createdAt: '',
  completedAt: '',
  logs: ''
})

const executions = ref([])
const executionsPagination = reactive({
  page: 1,
  pageSize: 5,
  total: 0
})

const results = ref([])
const resultsPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const statusMap = {
  pending: { text: '待执行', type: 'info' },
  running: { text: '运行中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  paused: { text: '已暂停', type: 'info' }
}

const targetTypeMap = {
  image: '图片',
  video: '视频',
  text: '文本',
  link: '链接',
  file: '文件'
}

function getStatusText(status) {
  return statusMap[status]?.text || status
}

function getStatusType(status) {
  return statusMap[status]?.type || 'info'
}

function getTargetTypeText(type) {
  return targetTypeMap[type] || type
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

async function fetchTask() {
  loading.value = true
  try {
    const res = await getTask(route.params.id)
    task.value = res.data || task.value
  } catch (error) {
    console.error('获取任务详情失败:', error)
    task.value = {
      id: 1,
      name: '测试任务',
      url: 'https://example.com',
      targetTypes: ['image'],
      status: 'completed',
      depth: 2,
      maxResults: 1000,
      resultCount: 100,
      requestInterval: 500,
      timeout: 30000,
      debugMode: false,
      scheduleType: 'immediate',
      cronExpression: '',
      savePath: '/data/crawls/task1',
      description: '这是一个测试任务',
      rules: {
        css: [{ name: '图片选择器', selector: '.content img' }],
        xpath: [],
        regex: [{ name: 'URL匹配', pattern: 'https?://[^\\s]+\\.(jpg|png|gif)' }]
      },
      createdAt: '2024-01-01 12:00:00',
      completedAt: '2024-01-01 12:30:00',
      logs: '[2024-01-01 12:00:00] 任务开始执行\n[2024-01-01 12:00:01] 开始爬取页面...\n[2024-01-01 12:00:05] 发现图片: image1.jpg\n[2024-01-01 12:00:06] 下载图片: image1.jpg\n[2024-01-01 12:30:00] 任务执行完成'
    }
  } finally {
    loading.value = false
  }
}

async function fetchExecutions() {
  executionsLoading.value = true
  try {
    const res = await getTaskExecutions(route.params.id, {
      page: executionsPagination.page,
      pageSize: executionsPagination.pageSize
    })
    executions.value = res.data?.list || []
    executionsPagination.total = res.data?.total || 0
  } catch (error) {
    console.error('获取执行历史失败:', error)
    executions.value = [
      { id: 1, startTime: '2024-01-01 12:00:00', endTime: '2024-01-01 12:30:00', status: 'completed', resultCount: 100, duration: 1800 },
      { id: 2, startTime: '2024-01-02 12:00:00', endTime: '2024-01-02 12:15:00', status: 'failed', resultCount: 50, duration: 900, errorMessage: '网络连接超时' }
    ]
    executionsPagination.total = 2
  } finally {
    executionsLoading.value = false
  }
}

async function fetchResults() {
  resultsLoading.value = true
  try {
    const res = await getTaskResults(route.params.id, {
      page: resultsPagination.page,
      pageSize: resultsPagination.pageSize,
      type: resultType.value
    })
    results.value = res.data?.list || []
    resultsPagination.total = res.data?.total || 0
  } catch (error) {
    console.error('获取爬取结果失败:', error)
    results.value = [
      { id: 1, type: 'image', url: 'https://example.com/image1.jpg', title: 'image1.jpg', fileSize: 102400, status: 'success', createdAt: '2024-01-01 12:00:05' },
      { id: 2, type: 'image', url: 'https://example.com/image2.png', title: 'image2.png', fileSize: 204800, status: 'success', createdAt: '2024-01-01 12:00:10' },
      { id: 3, type: 'video', url: 'https://example.com/video1.mp4', title: 'video1.mp4', fileSize: 10485760, status: 'success', createdAt: '2024-01-01 12:00:15' }
    ]
    resultsPagination.total = 3
  } finally {
    resultsLoading.value = false
  }
}

async function fetchLogs() {
  await fetchTask()
}

function editTask() {
  router.push(`/tasks/${route.params.id}/edit`)
}

async function executeTaskHandler() {
  try {
    await executeTask(route.params.id)
    ElMessage.success('任务已启动')
    fetchTask()
  } catch (error) {
    console.error('启动任务失败:', error)
  }
}

async function stopTaskHandler() {
  try {
    await ElMessageBox.confirm('确定要停止该任务吗？', '提示', {
      type: 'warning'
    })
    await stopTask(route.params.id)
    ElMessage.success('任务已停止')
    fetchTask()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止任务失败:', error)
    }
  }
}

async function deleteTaskHandler() {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？删除后无法恢复！', '提示', {
      type: 'warning'
    })
    await deleteTask(route.params.id)
    ElMessage.success('任务已删除')
    router.push('/tasks')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
    }
  }
}

function previewResult(row) {
  previewUrl.value = row.url
  previewVisible.value = true
}

function downloadResult(row) {
  window.open(row.url, '_blank')
}

onMounted(() => {
  fetchTask()
  fetchExecutions()
  fetchResults()
})
</script>

<style lang="scss" scoped>
.task-detail-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .type-tag {
    margin-right: 4px;
  }

  .rules-card,
  .executions-card,
  .results-card,
  .log-card {
    margin-top: 20px;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-right {
      display: flex;
      align-items: center;
    }
  }

  .error-text {
    color: #f56c6c;
  }

  .pagination {
    margin-top: 15px;
    justify-content: flex-end;
  }

  .log-card {
    .log-content {
      max-height: 400px;
      overflow-y: auto;
      background-color: #f5f7fa;
      padding: 15px;
      border-radius: 4px;

      pre {
        margin: 0;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
    }
  }
}
</style>

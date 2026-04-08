<template>
  <div class="resources-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="任务">
          <el-select
            v-model="filterForm.task_id"
            placeholder="选择任务"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="资源类型">
          <el-select
            v-model="filterForm.resource_type"
            placeholder="选择类型"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="type in resourceTypes"
              :key="type"
              :label="getTypeName(type)"
              :value="type"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="域名">
          <el-select
            v-model="filterForm.domain"
            placeholder="选择域名"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="domain in domains"
              :key="domain"
              :label="domain"
              :value="domain"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态码">
          <el-input
            v-model.number="filterForm.status_code"
            placeholder="状态码"
            clearable
            style="width: 120px"
          />
        </el-form-item>
        
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索URL"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="success" @click="showStatsDialog = true">
            <el-icon><DataAnalysis /></el-icon>
            统计分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="resources"
        stripe
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="URL" min-width="300">
          <template #default="{ row }">
            <div class="url-cell">
              <el-link
                :href="row.url"
                target="_blank"
                type="primary"
                :underline="false"
              >
                {{ truncateUrl(row.url) }}
              </el-link>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="getMethodType(row.method)" size="small">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ getTypeName(row.resource_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态码" width="90">
          <template #default="{ row }">
            <el-tag
              v-if="row.status_code"
              :type="getStatusType(row.status_code)"
              size="small"
            >
              {{ row.status_code }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click.stop="handleViewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              type="success"
              size="small"
              link
              @click.stop="handleReplay(row)"
            >
              重放
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click.stop="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showDetailDialog"
      title="资源详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">
          {{ currentResource.id }}
        </el-descriptions-item>
        <el-descriptions-item label="任务ID">
          {{ currentResource.task_id }}
        </el-descriptions-item>
        <el-descriptions-item label="URL" :span="2">
          <el-link :href="currentResource.url" target="_blank" type="primary">
            {{ currentResource.url }}
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">
          {{ currentResource.method }}
        </el-descriptions-item>
        <el-descriptions-item label="资源类型">
          {{ getTypeName(currentResource.resource_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态码">
          <el-tag :type="getStatusType(currentResource.status_code)">
            {{ currentResource.status_code || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资源大小">
          {{ formatSize(currentResource.size) }}
        </el-descriptions-item>
        <el-descriptions-item label="请求耗时">
          {{ formatDuration(currentResource.duration) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatTime(currentResource.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="请求头" :span="2">
          <el-scrollbar max-height="200px">
            <pre class="headers-pre">{{ formatHeaders(currentResource.headers) }}</pre>
          </el-scrollbar>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="showReplayDialog"
      title="请求重放"
      width="600px"
    >
      <el-form :model="replayForm" label-width="100px">
        <el-form-item label="URL">
          <el-input v-model="replayForm.url" />
        </el-form-item>
        <el-form-item label="方法">
          <el-select v-model="replayForm.method" style="width: 100%">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求头">
          <el-input
            v-model="replayForm.headersText"
            type="textarea"
            :rows="5"
            placeholder="JSON格式的请求头"
          />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input
            v-model="replayForm.body"
            type="textarea"
            :rows="5"
            placeholder="请求体内容"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showReplayDialog = false">取消</el-button>
        <el-button type="primary" :loading="replayLoading" @click="executeReplay">
          发送请求
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showReplayResultDialog"
      title="重放结果"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态码">
          <el-tag :type="getStatusType(replayResult.status_code)">
            {{ replayResult.status_code }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="响应大小">
          {{ formatSize(replayResult.size) }}
        </el-descriptions-item>
        <el-descriptions-item label="响应时间">
          {{ formatDuration(replayResult.duration) }}
        </el-descriptions-item>
        <el-descriptions-item label="响应头" :span="2">
          <el-scrollbar max-height="200px">
            <pre class="headers-pre">{{ formatHeaders(replayResult.headers) }}</pre>
          </el-scrollbar>
        </el-descriptions-item>
        <el-descriptions-item label="响应体" :span="2">
          <el-scrollbar max-height="400px">
            <pre class="headers-pre">{{ replayResult.body }}</pre>
          </el-scrollbar>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="showStatsDialog"
      title="资源统计分析"
      width="90%"
      top="5vh"
    >
      <ResourceStats :stats="resourceStats" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, DataAnalysis } from '@element-plus/icons-vue'
import { 
  getResources, 
  getResourceStats, 
  getResourceTypes,
  getResourceDomains,
  replayRequest,
  deleteResource 
} from '@/api/resource'
import { getTasks } from '@/api/task'
import ResourceStats from '@/components/ResourceStats.vue'

const loading = ref(false)
const resources = ref([])
const tasks = ref([])
const resourceTypes = ref([])
const domains = ref([])
const resourceStats = ref({})

const filterForm = reactive({
  task_id: null,
  resource_type: null,
  domain: null,
  status_code: null,
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const showDetailDialog = ref(false)
const currentResource = ref({})

const showReplayDialog = ref(false)
const replayLoading = ref(false)
const replayForm = reactive({
  url: '',
  method: 'GET',
  headersText: '',
  body: ''
})

const showReplayResultDialog = ref(false)
const replayResult = ref({})

const showStatsDialog = ref(false)

const typeNames = {
  'document': 'HTML文档',
  'stylesheet': '样式表',
  'script': 'JavaScript',
  'image': '图片',
  'font': '字体',
  'xhr': 'XHR请求',
  'video': '视频',
  'audio': '音频'
}

onMounted(() => {
  loadTasks()
  loadResourceTypes()
  loadDomains()
  loadResources()
})

async function loadTasks() {
  try {
    const res = await getTasks({ page: 1, page_size: 1000 })
    tasks.value = res.items || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

async function loadResourceTypes() {
  try {
    const res = await getResourceTypes()
    resourceTypes.value = res.types || []
  } catch (error) {
    console.error('加载资源类型失败:', error)
  }
}

async function loadDomains() {
  try {
    const res = await getResourceDomains()
    domains.value = res.domains || []
  } catch (error) {
    console.error('加载域名列表失败:', error)
  }
}

async function loadResources() {
  loading.value = true
  
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    if (filterForm.task_id) params.task_id = filterForm.task_id
    if (filterForm.resource_type) params.resource_type = filterForm.resource_type
    if (filterForm.domain) params.domain = filterForm.domain
    if (filterForm.status_code) params.status_code = filterForm.status_code
    if (filterForm.search) params.search = filterForm.search
    
    const res = await getResources(params)
    resources.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    ElMessage.error('加载资源列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const params = {}
    if (filterForm.task_id) params.task_id = filterForm.task_id
    
    const res = await getResourceStats(params)
    resourceStats.value = res
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

function handleSearch() {
  pagination.page = 1
  loadResources()
}

function handleReset() {
  filterForm.task_id = null
  filterForm.resource_type = null
  filterForm.domain = null
  filterForm.status_code = null
  filterForm.search = ''
  pagination.page = 1
  loadResources()
}

function handleSizeChange(size) {
  pagination.page_size = size
  loadResources()
}

function handlePageChange(page) {
  pagination.page = page
  loadResources()
}

function handleRowClick(row) {
  currentResource.value = row
  showDetailDialog.value = true
}

function handleViewDetail(row) {
  currentResource.value = row
  showDetailDialog.value = true
}

function handleReplay(row) {
  replayForm.url = row.url
  replayForm.method = row.method || 'GET'
  replayForm.headersText = row.headers ? JSON.stringify(row.headers, null, 2) : ''
  replayForm.body = ''
  showReplayDialog.value = true
}

async function executeReplay() {
  replayLoading.value = true
  
  try {
    let headers = {}
    if (replayForm.headersText) {
      try {
        headers = JSON.parse(replayForm.headersText)
      } catch (e) {
        ElMessage.error('请求头格式错误，请使用JSON格式')
        return
      }
    }
    
    const res = await replayRequest({
      url: replayForm.url,
      method: replayForm.method,
      headers: headers,
      body: replayForm.body || null
    })
    
    replayResult.value = res
    showReplayDialog.value = false
    showReplayResultDialog.value = true
    ElMessage.success('请求重放成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '请求重放失败')
  } finally {
    replayLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该资源记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteResource(row.id)
    ElMessage.success('删除成功')
    loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function getTypeName(type) {
  return typeNames[type] || type || '未知'
}

function getMethodType(method) {
  const types = {
    'GET': '',
    'POST': 'success',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return types[method] || ''
}

function getStatusType(code) {
  if (!code) return 'info'
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return ''
}

function truncateUrl(url) {
  if (!url) return ''
  return url.length > 60 ? url.substring(0, 60) + '...' : url
}

function formatSize(bytes) {
  if (!bytes) return '-'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(0)} ms`
  }
  
  return `${seconds.toFixed(2)} s`
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function formatHeaders(headers) {
  if (!headers) return '-'
  return JSON.stringify(headers, null, 2)
}
</script>

<style scoped lang="scss">
.resources-page {
  .filter-card {
    margin-bottom: 20px;
    
    .filter-form {
      display: flex;
      flex-wrap: wrap;
      
      .el-form-item {
        margin-bottom: 10px;
      }
    }
  }
  
  .table-card {
    .url-cell {
      .el-link {
        font-size: 13px;
      }
    }
    
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .headers-pre {
    background: #f5f7fa;
    padding: 12px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}
</style>

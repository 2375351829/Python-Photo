<template>
  <div class="task-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-button type="primary" @click="$router.push('/tasks/create')">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>

      <div class="search-bar">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="搜索任务名称/URL"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
              <el-option label="待执行" value="pending" />
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="已暂停" value="paused" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标类型">
            <el-select v-model="searchForm.targetType" placeholder="全部类型" clearable>
              <el-option label="图片" value="image" />
              <el-option label="视频" value="video" />
              <el-option label="文本" value="text" />
              <el-option label="链接" value="link" />
              <el-option label="文件" value="file" />
            </el-select>
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
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="taskList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="url" label="目标URL" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link :href="row.url" target="_blank" type="primary">{{ row.url }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="targetTypes" label="目标类型" width="150">
          <template #default="{ row }">
            <el-tag v-for="type in row.targetTypes" :key="type" size="small" class="type-tag">
              {{ getTargetTypeText(type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resultCount" label="结果数量" width="100" />
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">
              查看
            </el-button>
            <el-button link type="warning" @click="editTask(row.id)">
              编辑
            </el-button>
            <el-button 
              link 
              type="success" 
              @click="executeTaskHandler(row)" 
              :disabled="row.status === 'running'"
            >
              执行
            </el-button>
            <el-button 
              link 
              type="info" 
              @click="stopTaskHandler(row)" 
              :disabled="row.status !== 'running'"
            >
              停止
            </el-button>
            <el-button link type="danger" @click="deleteTaskHandler(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="fetchTasks"
        @current-change="fetchTasks"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getTasks, deleteTask, executeTask, stopTask } from '@/api/task'

const router = useRouter()

const loading = ref(false)
const taskList = ref([])

const searchForm = reactive({
  keyword: '',
  status: '',
  targetType: ''
})

const pagination = reactive({
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

async function fetchTasks() {
  loading.value = true
  try {
    const res = await getTasks({
      page: pagination.page,
      pageSize: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status,
      targetType: searchForm.targetType
    })
    taskList.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('获取任务列表失败:', error)
    taskList.value = [
      { id: 1, name: '测试任务1', url: 'https://example.com', status: 'completed', targetTypes: ['image'], resultCount: 100, createdAt: '2024-01-01 12:00:00' },
      { id: 2, name: '测试任务2', url: 'https://example.org', status: 'running', targetTypes: ['image', 'video'], resultCount: 50, createdAt: '2024-01-02 12:00:00' },
      { id: 3, name: '测试任务3', url: 'https://test.com', status: 'pending', targetTypes: ['text'], resultCount: 0, createdAt: '2024-01-03 12:00:00' }
    ]
    pagination.total = 3
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchTasks()
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.targetType = ''
  pagination.page = 1
  fetchTasks()
}

function viewDetail(id) {
  router.push(`/tasks/${id}`)
}

function editTask(id) {
  router.push(`/tasks/${id}/edit`)
}

async function executeTaskHandler(row) {
  try {
    await executeTask(row.id)
    ElMessage.success('任务已启动')
    fetchTasks()
  } catch (error) {
    console.error('启动任务失败:', error)
  }
}

async function stopTaskHandler(row) {
  try {
    await ElMessageBox.confirm('确定要停止该任务吗？', '提示', {
      type: 'warning'
    })
    await stopTask(row.id)
    ElMessage.success('任务已停止')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止任务失败:', error)
    }
  }
}

async function deleteTaskHandler(id) {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？删除后无法恢复！', '提示', {
      type: 'warning'
    })
    await deleteTask(id)
    ElMessage.success('任务已删除')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
    }
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<style lang="scss" scoped>
.task-list-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-bar {
    margin-bottom: 20px;

    .search-form {
      display: flex;
      flex-wrap: wrap;
    }
  }

  .type-tag {
    margin-right: 4px;
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>

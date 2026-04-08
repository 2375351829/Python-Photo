<template>
  <div class="resource-stats">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_requests || 0 }}</div>
              <div class="stat-label">总请求数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.successful_requests || 0 }}</div>
              <div class="stat-label">成功请求</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.failed_requests || 0 }}</div>
              <div class="stat-label">失败请求</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatTime(stats.average_response_time) }}</div>
              <div class="stat-label">平均响应时间</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>资源类型分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div v-if="Object.keys(stats.resource_types || {}).length === 0" class="empty-chart">
              暂无数据
            </div>
            <div v-else class="pie-chart">
              <div 
                v-for="(count, type) in stats.resource_types" 
                :key="type"
                class="pie-item"
              >
                <div class="pie-label">
                  <span class="pie-color" :style="{ background: getTypeColor(type) }"></span>
                  <span class="pie-name">{{ getTypeName(type) }}</span>
                </div>
                <div class="pie-bar-container">
                  <div 
                    class="pie-bar" 
                    :style="{ 
                      width: getPercentage(count, stats.resource_types) + '%',
                      background: getTypeColor(type)
                    }"
                  ></div>
                </div>
                <div class="pie-count">{{ count }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>域名分布 TOP 10</span>
            </div>
          </template>
          <div class="chart-container">
            <div v-if="Object.keys(stats.domains || {}).length === 0" class="empty-chart">
              暂无数据
            </div>
            <div v-else class="bar-chart">
              <div 
                v-for="(item, index) in getTopDomains" 
                :key="item.domain"
                class="bar-item"
              >
                <div class="bar-label">{{ item.domain }}</div>
                <div class="bar-container">
                  <div 
                    class="bar-fill" 
                    :style="{ 
                      width: item.percentage + '%',
                      background: getBarColor(index)
                    }"
                  ></div>
                </div>
                <div class="bar-count">{{ item.count }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>状态码分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div v-if="Object.keys(stats.status_codes || {}).length === 0" class="empty-chart">
              暂无数据
            </div>
            <div v-else class="status-chart">
              <div 
                v-for="(count, code) in stats.status_codes" 
                :key="code"
                class="status-item"
              >
                <el-tag :type="getStatusType(code)" size="large">
                  {{ code }}
                </el-tag>
                <div class="status-bar-container">
                  <div 
                    class="status-bar" 
                    :style="{ 
                      width: getPercentage(count, stats.status_codes) + '%',
                      background: getStatusColor(code)
                    }"
                  ></div>
                </div>
                <div class="status-count">{{ count }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>资源大小统计</span>
            </div>
          </template>
          <div class="size-stats">
            <div class="size-item">
              <div class="size-label">总大小</div>
              <div class="size-value">{{ formatSize(stats.total_size_bytes) }}</div>
            </div>
            <div class="size-item">
              <div class="size-label">平均大小</div>
              <div class="size-value">{{ formatSize(averageSize) }}</div>
            </div>
            <div class="size-item">
              <div class="size-label">总响应时间</div>
              <div class="size-value">{{ formatTime(stats.total_response_time) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document, CircleCheck, CircleClose, Timer } from '@element-plus/icons-vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({})
  }
})

const typeColors = {
  'document': '#409eff',
  'stylesheet': '#67c23a',
  'script': '#e6a23c',
  'image': '#f56c6c',
  'font': '#909399',
  'xhr': '#b37feb',
  'video': '#ff85c0',
  'audio': '#36cfc9',
  'other': '#8c8c8c'
}

const typeNames = {
  'document': 'HTML文档',
  'stylesheet': '样式表',
  'script': 'JavaScript',
  'image': '图片',
  'font': '字体',
  'xhr': 'XHR请求',
  'video': '视频',
  'audio': '音频',
  'other': '其他'
}

const barColors = [
  '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#b37beb',
  '#ff85c0', '#36cfc9', '#ffc53d', '#ff7a45', '#9254de'
]

const averageSize = computed(() => {
  const total = props.stats.total_requests || 0
  const size = props.stats.total_size_bytes || 0
  return total > 0 ? size / total : 0
})

const getTopDomains = computed(() => {
  const domains = props.stats.domains || {}
  const entries = Object.entries(domains)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
  
  const maxCount = entries.length > 0 ? entries[0][1] : 0
  
  return entries.map(([domain, count]) => ({
    domain,
    count,
    percentage: maxCount > 0 ? (count / maxCount * 100) : 0
  }))
})

function getTypeColor(type) {
  return typeColors[type] || typeColors['other']
}

function getTypeName(type) {
  return typeNames[type] || type || '未知'
}

function getBarColor(index) {
  return barColors[index % barColors.length]
}

function getStatusType(code) {
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'info'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return ''
}

function getStatusColor(code) {
  if (code >= 200 && code < 300) return '#67c23a'
  if (code >= 300 && code < 400) return '#909399'
  if (code >= 400 && code < 500) return '#e6a23c'
  if (code >= 500) return '#f56c6c'
  return '#8c8c8c'
}

function getPercentage(count, data) {
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  return total > 0 ? (count / total * 100) : 0
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

function formatTime(seconds) {
  if (!seconds || seconds === 0) return '0 ms'
  
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(2)} ms`
  }
  
  return `${seconds.toFixed(2)} s`
}
</script>

<style scoped lang="scss">
.resource-stats {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 28px;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
          line-height: 1.2;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .card-header {
    font-weight: bold;
    font-size: 16px;
  }
  
  .chart-container {
    min-height: 200px;
    
    .empty-chart {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;
      color: #909399;
    }
  }
  
  .pie-chart {
    .pie-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      gap: 12px;
      
      .pie-label {
        width: 120px;
        display: flex;
        align-items: center;
        gap: 8px;
        
        .pie-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }
        
        .pie-name {
          font-size: 14px;
          color: #606266;
        }
      }
      
      .pie-bar-container {
        flex: 1;
        height: 20px;
        background: #f5f7fa;
        border-radius: 4px;
        overflow: hidden;
        
        .pie-bar {
          height: 100%;
          transition: width 0.3s ease;
        }
      }
      
      .pie-count {
        width: 50px;
        text-align: right;
        font-size: 14px;
        color: #606266;
      }
    }
  }
  
  .bar-chart {
    .bar-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      gap: 12px;
      
      .bar-label {
        width: 200px;
        font-size: 13px;
        color: #606266;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .bar-container {
        flex: 1;
        height: 24px;
        background: #f5f7fa;
        border-radius: 4px;
        overflow: hidden;
        
        .bar-fill {
          height: 100%;
          transition: width 0.3s ease;
        }
      }
      
      .bar-count {
        width: 50px;
        text-align: right;
        font-size: 14px;
        color: #606266;
        font-weight: 500;
      }
    }
  }
  
  .status-chart {
    .status-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      gap: 12px;
      
      .status-bar-container {
        flex: 1;
        height: 20px;
        background: #f5f7fa;
        border-radius: 4px;
        overflow: hidden;
        
        .status-bar {
          height: 100%;
          transition: width 0.3s ease;
        }
      }
      
      .status-count {
        width: 50px;
        text-align: right;
        font-size: 14px;
        color: #606266;
      }
    }
  }
  
  .size-stats {
    display: flex;
    flex-direction: column;
    gap: 20px;
    
    .size-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      
      .size-label {
        font-size: 14px;
        color: #606266;
      }
      
      .size-value {
        font-size: 20px;
        font-weight: bold;
        color: #409eff;
      }
    }
  }
}
</style>

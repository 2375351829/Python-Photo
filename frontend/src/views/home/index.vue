<template>
  <div class="home-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon task">
              <el-icon><List /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalTasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.runningTasks }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon completed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completedTasks }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon images">
              <el-icon><Picture /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalImages }}</div>
              <div class="stat-label">图片总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="welcome-card">
      <template #header>
        <span>欢迎使用图片爬虫管理平台</span>
      </template>
      <div class="welcome-content">
        <p>这是一个功能强大的图片爬虫管理平台，支持以下功能：</p>
        <ul>
          <li>创建和管理爬虫任务</li>
          <li>自动下载和分类图片</li>
          <li>查看爬取进度和日志</li>
          <li>图片预览和管理</li>
        </ul>
        <el-button type="primary" @click="$router.push('/tasks/create')">
          创建新任务
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { List, Loading, CircleCheck, Picture } from '@element-plus/icons-vue'

const stats = ref({
  totalTasks: 0,
  runningTasks: 0,
  completedTasks: 0,
  totalImages: 0
})

onMounted(() => {
  stats.value = {
    totalTasks: 12,
    runningTasks: 3,
    completedTasks: 8,
    totalImages: 1234
  }
})
</script>

<style lang="scss" scoped>
.home-container {
  .stat-card {
    margin-bottom: 20px;

    .stat-content {
      display: flex;
      align-items: center;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;

        .el-icon {
          font-size: 28px;
          color: #fff;
        }

        &.task {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        &.running {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        &.completed {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        &.images {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }

      .stat-info {
        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #333;
        }

        .stat-label {
          font-size: 14px;
          color: #999;
          margin-top: 5px;
        }
      }
    }
  }

  .welcome-card {
    .welcome-content {
      p {
        color: #666;
        margin-bottom: 15px;
      }

      ul {
        margin-bottom: 20px;
        padding-left: 20px;

        li {
          color: #666;
          margin-bottom: 8px;
        }
      }
    }
  }
}
</style>

<template>
  <div class="image-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>图片列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索图片"
              style="width: 200px; margin-right: 10px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <div class="image-grid" v-loading="loading">
        <div
          v-for="image in imageList"
          :key="image.id"
          class="image-item"
          @click="previewImage(image)"
        >
          <el-image
            :src="image.thumbnail"
            fit="cover"
            class="image-thumb"
          >
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="image-info">
            <div class="image-name">{{ image.name }}</div>
            <div class="image-meta">{{ image.size }} | {{ image.format }}</div>
          </div>
        </div>
      </div>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 40, 60, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="fetchImages"
        @current-change="fetchImages"
      />
    </el-card>

    <el-dialog v-model="previewVisible" title="图片预览" width="800px">
      <el-image :src="previewUrl" fit="contain" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Picture } from '@element-plus/icons-vue'

const loading = ref(false)
const searchKeyword = ref('')
const imageList = ref([])
const previewVisible = ref(false)
const previewUrl = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

async function fetchImages() {
  loading.value = true
  try {
    imageList.value = [
      { id: 1, name: 'image1.jpg', thumbnail: '', size: '1.2MB', format: 'JPG' },
      { id: 2, name: 'image2.png', thumbnail: '', size: '2.5MB', format: 'PNG' },
      { id: 3, name: 'image3.jpg', thumbnail: '', size: '800KB', format: 'JPG' }
    ]
    pagination.total = 3
  } finally {
    loading.value = false
  }
}

function previewImage(image) {
  previewUrl.value = image.thumbnail
  previewVisible.value = true
}

onMounted(() => {
  fetchImages()
})
</script>

<style lang="scss" scoped>
.image-list-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    min-height: 200px;

    .image-item {
      border: 1px solid #ebeef5;
      border-radius: 4px;
      overflow: hidden;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
      }

      .image-thumb {
        width: 100%;
        height: 150px;
        background-color: #f5f7fa;

        .image-error {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #c0c4cc;
          font-size: 40px;
        }
      }

      .image-info {
        padding: 10px;

        .image-name {
          font-size: 14px;
          color: #303133;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .image-meta {
          font-size: 12px;
          color: #909399;
          margin-top: 5px;
        }
      }
    }
  }

  .pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>

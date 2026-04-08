<template>
  <div class="resource-filter-config">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="图片过滤" name="image">
        <div class="filter-section">
          <el-divider content-position="left">格式过滤</el-divider>
          <el-form-item label="图片格式">
            <el-checkbox-group v-model="filterConfig.image.formats">
              <el-checkbox v-for="fmt in imageFormats" :key="fmt.value" :value="fmt.value">
                {{ fmt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="自定义格式">
            <el-input
              v-model="customImageFormats"
              placeholder="输入自定义格式，用逗号分隔，如: bmp,tiff,raw"
              @blur="handleCustomImageFormats"
            />
          </el-form-item>

          <el-divider content-position="left">尺寸过滤</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小宽度">
                <el-input-number v-model="filterConfig.image.minWidth" :min="0" :max="10000" />
                <span class="unit">px</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大宽度">
                <el-input-number v-model="filterConfig.image.maxWidth" :min="0" :max="10000" />
                <span class="unit">px</span>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小高度">
                <el-input-number v-model="filterConfig.image.minHeight" :min="0" :max="10000" />
                <span class="unit">px</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大高度">
                <el-input-number v-model="filterConfig.image.maxHeight" :min="0" :max="10000" />
                <span class="unit">px</span>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="宽高比限制">
            <el-select v-model="filterConfig.image.aspectRatio" placeholder="不限制" clearable>
              <el-option label="横图 (>1)" value="landscape" />
              <el-option label="竖图 (<1)" value="portrait" />
              <el-option label="正方形 (=1)" value="square" />
              <el-option label="16:9" value="16:9" />
              <el-option label="4:3" value="4:3" />
              <el-option label="3:2" value="3:2" />
            </el-select>
          </el-form-item>

          <el-divider content-position="left">大小过滤</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小文件大小">
                <el-input-number v-model="filterConfig.image.minSize" :min="0" />
                <el-select v-model="filterConfig.image.minSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="B" value="B" />
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大文件大小">
                <el-input-number v-model="filterConfig.image.maxSize" :min="0" />
                <el-select v-model="filterConfig.image.maxSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="B" value="B" />
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="视频过滤" name="video">
        <div class="filter-section">
          <el-divider content-position="left">格式过滤</el-divider>
          <el-form-item label="视频格式">
            <el-checkbox-group v-model="filterConfig.video.formats">
              <el-checkbox v-for="fmt in videoFormats" :key="fmt.value" :value="fmt.value">
                {{ fmt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="自定义格式">
            <el-input
              v-model="customVideoFormats"
              placeholder="输入自定义格式，用逗号分隔，如: mkv,mov,flv"
              @blur="handleCustomVideoFormats"
            />
          </el-form-item>

          <el-divider content-position="left">时长过滤</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小时长">
                <el-input-number v-model="filterConfig.video.minDuration" :min="0" />
                <span class="unit">秒</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大时长">
                <el-input-number v-model="filterConfig.video.maxDuration" :min="0" />
                <span class="unit">秒</span>
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">分辨率过滤</el-divider>
          <el-form-item label="最低分辨率">
            <el-select v-model="filterConfig.video.minResolution" placeholder="不限制" clearable>
              <el-option label="240p" value="240p" />
              <el-option label="360p" value="360p" />
              <el-option label="480p" value="480p" />
              <el-option label="720p (HD)" value="720p" />
              <el-option label="1080p (Full HD)" value="1080p" />
              <el-option label="1440p (2K)" value="1440p" />
              <el-option label="2160p (4K)" value="2160p" />
            </el-select>
          </el-form-item>

          <el-divider content-position="left">大小过滤</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小文件大小">
                <el-input-number v-model="filterConfig.video.minSize" :min="0" />
                <el-select v-model="filterConfig.video.minSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                  <el-option label="GB" value="GB" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大文件大小">
                <el-input-number v-model="filterConfig.video.maxSize" :min="0" />
                <el-select v-model="filterConfig.video.maxSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                  <el-option label="GB" value="GB" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="文件过滤" name="file">
        <div class="filter-section">
          <el-divider content-position="left">文档类型</el-divider>
          <el-form-item label="文档格式">
            <el-checkbox-group v-model="filterConfig.file.documentFormats">
              <el-checkbox v-for="fmt in documentFormats" :key="fmt.value" :value="fmt.value">
                {{ fmt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-divider content-position="left">压缩包</el-divider>
          <el-form-item label="压缩格式">
            <el-checkbox-group v-model="filterConfig.file.archiveFormats">
              <el-checkbox v-for="fmt in archiveFormats" :key="fmt.value" :value="fmt.value">
                {{ fmt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-divider content-position="left">其他文件</el-divider>
          <el-form-item label="其他格式">
            <el-checkbox-group v-model="filterConfig.file.otherFormats">
              <el-checkbox v-for="fmt in otherFileFormats" :key="fmt.value" :value="fmt.value">
                {{ fmt.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="自定义格式">
            <el-input
              v-model="customFileFormats"
              placeholder="输入自定义格式，用逗号分隔，如: iso,dmg,exe"
              @blur="handleCustomFileFormats"
            />
          </el-form-item>

          <el-divider content-position="left">大小过滤</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小文件大小">
                <el-input-number v-model="filterConfig.file.minSize" :min="0" />
                <el-select v-model="filterConfig.file.minSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="B" value="B" />
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                  <el-option label="GB" value="GB" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大文件大小">
                <el-input-number v-model="filterConfig.file.maxSize" :min="0" />
                <el-select v-model="filterConfig.file.maxSizeUnit" style="width: 80px; margin-left: 8px;">
                  <el-option label="B" value="B" />
                  <el-option label="KB" value="KB" />
                  <el-option label="MB" value="MB" />
                  <el-option label="GB" value="GB" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="高级过滤" name="advanced">
        <div class="filter-section">
          <el-divider content-position="left">URL过滤</el-divider>
          <el-form-item label="URL包含关键词">
            <el-select
              v-model="filterConfig.advanced.urlIncludeKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后按回车添加"
            />
          </el-form-item>
          <el-form-item label="URL排除关键词">
            <el-select
              v-model="filterConfig.advanced.urlExcludeKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后按回车添加"
            />
          </el-form-item>
          <el-form-item label="URL正则匹配">
            <el-input
              v-model="filterConfig.advanced.urlRegex"
              placeholder="正则表达式，如: .*wallpaper.*"
            />
          </el-form-item>

          <el-divider content-position="left">文件名过滤</el-divider>
          <el-form-item label="文件名包含关键词">
            <el-select
              v-model="filterConfig.advanced.filenameIncludeKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后按回车添加"
            />
          </el-form-item>
          <el-form-item label="文件名排除关键词">
            <el-select
              v-model="filterConfig.advanced.filenameExcludeKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后按回车添加"
            />
          </el-form-item>

          <el-divider content-position="left">其他选项</el-divider>
          <el-form-item label="跳过重复文件">
            <el-switch v-model="filterConfig.advanced.skipDuplicates" />
            <span class="form-tip">根据文件哈希值判断</span>
          </el-form-item>
          <el-form-item label="跳过已下载">
            <el-switch v-model="filterConfig.advanced.skipDownloaded" />
            <span class="form-tip">跳过历史已下载的文件</span>
          </el-form-item>
          <el-form-item label="验证文件完整性">
            <el-switch v-model="filterConfig.advanced.validateFile" />
            <span class="form-tip">下载后验证文件是否完整</span>
          </el-form-item>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="filter-summary">
      <el-divider />
      <div class="summary-header">
        <span>过滤条件摘要</span>
        <el-button type="primary" size="small" @click="handleReset">重置所有</el-button>
      </div>
      <div class="summary-content">
        <el-tag
          v-for="(tag, index) in filterSummary"
          :key="index"
          :type="tag.type"
          class="summary-tag"
        >
          {{ tag.label }}: {{ tag.value }}
        </el-tag>
        <el-empty v-if="filterSummary.length === 0" description="暂无过滤条件" :image-size="40" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const activeTab = ref('image')

const imageFormats = [
  { value: 'jpg', label: 'JPG' },
  { value: 'jpeg', label: 'JPEG' },
  { value: 'png', label: 'PNG' },
  { value: 'gif', label: 'GIF' },
  { value: 'webp', label: 'WebP' },
  { value: 'svg', label: 'SVG' },
  { value: 'bmp', label: 'BMP' },
  { value: 'ico', label: 'ICO' },
  { value: 'tiff', label: 'TIFF' },
  { value: 'avif', label: 'AVIF' }
]

const videoFormats = [
  { value: 'mp4', label: 'MP4' },
  { value: 'webm', label: 'WebM' },
  { value: 'avi', label: 'AVI' },
  { value: 'mkv', label: 'MKV' },
  { value: 'mov', label: 'MOV' },
  { value: 'wmv', label: 'WMV' },
  { value: 'flv', label: 'FLV' },
  { value: 'm4v', label: 'M4V' }
]

const documentFormats = [
  { value: 'pdf', label: 'PDF' },
  { value: 'doc', label: 'DOC' },
  { value: 'docx', label: 'DOCX' },
  { value: 'xls', label: 'XLS' },
  { value: 'xlsx', label: 'XLSX' },
  { value: 'ppt', label: 'PPT' },
  { value: 'pptx', label: 'PPTX' },
  { value: 'txt', label: 'TXT' }
]

const archiveFormats = [
  { value: 'zip', label: 'ZIP' },
  { value: 'rar', label: 'RAR' },
  { value: '7z', label: '7Z' },
  { value: 'tar', label: 'TAR' },
  { value: 'gz', label: 'GZ' }
]

const otherFileFormats = [
  { value: 'apk', label: 'APK' },
  { value: 'ipa', label: 'IPA' },
  { value: 'exe', label: 'EXE' },
  { value: 'dmg', label: 'DMG' },
  { value: 'iso', label: 'ISO' },
  { value: 'torrent', label: 'Torrent' }
]

const defaultFilterConfig = {
  image: {
    formats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    minWidth: 0,
    maxWidth: 0,
    minHeight: 0,
    maxHeight: 0,
    aspectRatio: '',
    minSize: 0,
    maxSize: 0,
    minSizeUnit: 'KB',
    maxSizeUnit: 'MB'
  },
  video: {
    formats: ['mp4', 'webm'],
    minDuration: 0,
    maxDuration: 0,
    minResolution: '',
    minSize: 0,
    maxSize: 0,
    minSizeUnit: 'MB',
    maxSizeUnit: 'GB'
  },
  file: {
    documentFormats: ['pdf'],
    archiveFormats: ['zip', 'rar'],
    otherFormats: [],
    minSize: 0,
    maxSize: 0,
    minSizeUnit: 'KB',
    maxSizeUnit: 'MB'
  },
  advanced: {
    urlIncludeKeywords: [],
    urlExcludeKeywords: [],
    urlRegex: '',
    filenameIncludeKeywords: [],
    filenameExcludeKeywords: [],
    skipDuplicates: true,
    skipDownloaded: false,
    validateFile: true
  }
}

const filterConfig = ref({
  ...defaultFilterConfig,
  ...props.modelValue
})

const customImageFormats = ref('')
const customVideoFormats = ref('')
const customFileFormats = ref('')

const filterSummary = computed(() => {
  const summary = []
  
  if (filterConfig.value.image.formats.length > 0) {
    summary.push({
      type: 'primary',
      label: '图片格式',
      value: filterConfig.value.image.formats.join(', ').toUpperCase()
    })
  }
  
  if (filterConfig.value.image.minWidth > 0 || filterConfig.value.image.minHeight > 0) {
    const dims = []
    if (filterConfig.value.image.minWidth > 0) dims.push(`宽≥${filterConfig.value.image.minWidth}px`)
    if (filterConfig.value.image.minHeight > 0) dims.push(`高≥${filterConfig.value.image.minHeight}px`)
    summary.push({ type: 'success', label: '图片尺寸', value: dims.join(', ') })
  }
  
  if (filterConfig.value.video.formats.length > 0) {
    summary.push({
      type: 'warning',
      label: '视频格式',
      value: filterConfig.value.video.formats.join(', ').toUpperCase()
    })
  }
  
  if (filterConfig.value.advanced.urlExcludeKeywords.length > 0) {
    summary.push({
      type: 'danger',
      label: '排除URL',
      value: filterConfig.value.advanced.urlExcludeKeywords.join(', ')
    })
  }
  
  if (filterConfig.value.advanced.skipDuplicates) {
    summary.push({ type: 'info', label: '去重', value: '已开启' })
  }
  
  return summary
})

watch(filterConfig, (val) => {
  emit('update:modelValue', val)
}, { deep: true })

watch(() => props.modelValue, (val) => {
  filterConfig.value = { ...defaultFilterConfig, ...val }
}, { deep: true })

function handleCustomImageFormats() {
  if (customImageFormats.value) {
    const formats = customImageFormats.value.split(',').map(f => f.trim().toLowerCase())
    formats.forEach(f => {
      if (f && !filterConfig.value.image.formats.includes(f)) {
        filterConfig.value.image.formats.push(f)
      }
    })
    customImageFormats.value = ''
  }
}

function handleCustomVideoFormats() {
  if (customVideoFormats.value) {
    const formats = customVideoFormats.value.split(',').map(f => f.trim().toLowerCase())
    formats.forEach(f => {
      if (f && !filterConfig.value.video.formats.includes(f)) {
        filterConfig.value.video.formats.push(f)
      }
    })
    customVideoFormats.value = ''
  }
}

function handleCustomFileFormats() {
  if (customFileFormats.value) {
    const formats = customFileFormats.value.split(',').map(f => f.trim().toLowerCase())
    formats.forEach(f => {
      if (f && !filterConfig.value.file.otherFormats.includes(f)) {
        filterConfig.value.file.otherFormats.push(f)
      }
    })
    customFileFormats.value = ''
  }
}

function handleReset() {
  filterConfig.value = JSON.parse(JSON.stringify(defaultFilterConfig))
}
</script>

<style lang="scss" scoped>
.resource-filter-config {
  .filter-section {
    padding: 10px 0;

    .unit {
      margin-left: 8px;
      color: #909399;
    }

    .form-tip {
      margin-left: 10px;
      color: #909399;
      font-size: 12px;
    }
  }

  .filter-summary {
    .summary-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      font-weight: 500;
    }

    .summary-content {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 10px;
      background-color: #f5f7fa;
      border-radius: 4px;
      min-height: 60px;

      .summary-tag {
        margin: 0;
      }
    }
  }
}
</style>

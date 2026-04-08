<template>
  <div class="target-type-selector">
    <div class="type-cards">
      <div
        v-for="type in targetTypes"
        :key="type.value"
        class="type-card"
        :class="{ active: selectedTypes.includes(type.value) }"
        @click="toggleType(type.value)"
      >
        <div class="type-icon">
          <el-icon :size="32">
            <component :is="type.icon" />
          </el-icon>
        </div>
        <div class="type-info">
          <div class="type-name">{{ type.label }}</div>
          <div class="type-desc">{{ type.description }}</div>
        </div>
        <div class="type-check" v-if="selectedTypes.includes(type.value)">
          <el-icon><Check /></el-icon>
        </div>
      </div>
    </div>

    <el-divider content-position="left">详细配置</el-divider>

    <div class="type-configs">
      <el-collapse v-model="activeConfigs">
        <el-collapse-item
          v-for="type in selectedTypeConfigs"
          :key="type.value"
          :name="type.value"
        >
          <template #title>
            <div class="config-title">
              <el-icon><component :is="type.icon" /></el-icon>
              <span>{{ type.label }}配置</span>
            </div>
          </template>

          <div class="config-content">
            <template v-if="type.value === 'image'">
              <el-form-item label="下载图片">
                <el-switch v-model="config.image.download" />
              </el-form-item>
              <el-form-item label="保留原图">
                <el-switch v-model="config.image.keepOriginal" />
              </el-form-item>
              <el-form-item label="转换格式">
                <el-select v-model="config.image.convertFormat" placeholder="不转换" clearable>
                  <el-option label="转为 JPG" value="jpg" />
                  <el-option label="转为 PNG" value="png" />
                  <el-option label="转为 WebP" value="webp" />
                </el-select>
              </el-form-item>
              <el-form-item label="压缩质量">
                <el-slider v-model="config.image.quality" :min="1" :max="100" :step="1" show-input />
              </el-form-item>
              <el-form-item label="添加水印">
                <el-switch v-model="config.image.watermark.enabled" />
              </el-form-item>
              <el-form-item v-if="config.image.watermark.enabled" label="水印文字">
                <el-input v-model="config.image.watermark.text" placeholder="请输入水印文字" />
              </el-form-item>
            </template>

            <template v-if="type.value === 'video'">
              <el-form-item label="下载视频">
                <el-switch v-model="config.video.download" />
              </el-form-item>
              <el-form-item label="提取音频">
                <el-switch v-model="config.video.extractAudio" />
              </el-form-item>
              <el-form-item label="生成缩略图">
                <el-switch v-model="config.video.generateThumbnail" />
              </el-form-item>
              <el-form-item label="最大时长(秒)">
                <el-input-number v-model="config.video.maxDuration" :min="0" :max="36000" />
              </el-form-item>
              <el-form-item label="分辨率限制">
                <el-select v-model="config.video.maxResolution" placeholder="不限制" clearable>
                  <el-option label="480p" value="480p" />
                  <el-option label="720p" value="720p" />
                  <el-option label="1080p" value="1080p" />
                  <el-option label="4K" value="4k" />
                </el-select>
              </el-form-item>
            </template>

            <template v-if="type.value === 'text'">
              <el-form-item label="提取正文">
                <el-switch v-model="config.text.extractMain" />
              </el-form-item>
              <el-form-item label="去除HTML标签">
                <el-switch v-model="config.text.stripHtml" />
              </el-form-item>
              <el-form-item label="去除空白字符">
                <el-switch v-model="config.text.stripWhitespace" />
              </el-form-item>
              <el-form-item label="最小字数">
                <el-input-number v-model="config.text.minLength" :min="0" :max="100000" />
              </el-form-item>
              <el-form-item label="保存格式">
                <el-radio-group v-model="config.text.saveFormat">
                  <el-radio value="txt">TXT</el-radio>
                  <el-radio value="md">Markdown</el-radio>
                  <el-radio value="html">HTML</el-radio>
                </el-radio-group>
              </el-form-item>
            </template>

            <template v-if="type.value === 'link'">
              <el-form-item label="提取内链">
                <el-switch v-model="config.link.includeInternal" />
              </el-form-item>
              <el-form-item label="提取外链">
                <el-switch v-model="config.link.includeExternal" />
              </el-form-item>
              <el-form-item label="验证链接有效性">
                <el-switch v-model="config.link.validateUrl" />
              </el-form-item>
              <el-form-item label="提取锚文本">
                <el-switch v-model="config.link.extractAnchorText" />
              </el-form-item>
              <el-form-item label="保存格式">
                <el-radio-group v-model="config.link.saveFormat">
                  <el-radio value="list">列表</el-radio>
                  <el-radio value="csv">CSV</el-radio>
                  <el-radio value="json">JSON</el-radio>
                </el-radio-group>
              </el-form-item>
            </template>

            <template v-if="type.value === 'file'">
              <el-form-item label="下载文件">
                <el-switch v-model="config.file.download" />
              </el-form-item>
              <el-form-item label="保留原始文件名">
                <el-switch v-model="config.file.keepOriginalName" />
              </el-form-item>
              <el-form-item label="重命名规则">
                <el-input
                  v-model="config.file.renamePattern"
                  placeholder="如: {timestamp}_{random}.{ext}"
                  :disabled="config.file.keepOriginalName"
                />
              </el-form-item>
              <el-form-item label="解压压缩包">
                <el-switch v-model="config.file.extractArchive" />
              </el-form-item>
              <el-form-item label="计算文件哈希">
                <el-checkbox-group v-model="config.file.computeHash">
                  <el-checkbox value="md5">MD5</el-checkbox>
                  <el-checkbox value="sha1">SHA1</el-checkbox>
                  <el-checkbox value="sha256">SHA256</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </template>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  Check, 
  Picture, 
  VideoCamera, 
  Document, 
  Link, 
  Folder 
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => ['image']
  },
  configValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'update:configValue'])

const targetTypes = [
  { 
    value: 'image', 
    label: '图片', 
    icon: Picture,
    description: 'JPG、PNG、GIF、WebP等图片资源'
  },
  { 
    value: 'video', 
    label: '视频', 
    icon: VideoCamera,
    description: 'MP4、WebM、AVI等视频资源'
  },
  { 
    value: 'text', 
    label: '文本', 
    icon: Document,
    description: '页面文本内容和文章'
  },
  { 
    value: 'link', 
    label: '链接', 
    icon: Link,
    description: '页面中的超链接'
  },
  { 
    value: 'file', 
    label: '文件', 
    icon: Folder,
    description: 'PDF、DOC、ZIP等文件'
  }
]

const selectedTypes = ref([...props.modelValue])
const activeConfigs = ref([...props.modelValue])

const defaultConfig = {
  image: {
    download: true,
    keepOriginal: true,
    convertFormat: '',
    quality: 85,
    watermark: {
      enabled: false,
      text: ''
    }
  },
  video: {
    download: true,
    extractAudio: false,
    generateThumbnail: true,
    maxDuration: 0,
    maxResolution: ''
  },
  text: {
    extractMain: true,
    stripHtml: true,
    stripWhitespace: true,
    minLength: 0,
    saveFormat: 'txt'
  },
  link: {
    includeInternal: true,
    includeExternal: true,
    validateUrl: false,
    extractAnchorText: true,
    saveFormat: 'list'
  },
  file: {
    download: true,
    keepOriginalName: true,
    renamePattern: '',
    extractArchive: false,
    computeHash: ['md5']
  }
}

const config = ref({
  ...defaultConfig,
  ...props.configValue
})

const selectedTypeConfigs = computed(() => {
  return targetTypes.filter(type => selectedTypes.value.includes(type.value))
})

watch(selectedTypes, (val) => {
  emit('update:modelValue', val)
}, { deep: true })

watch(config, (val) => {
  emit('update:configValue', val)
}, { deep: true })

watch(() => props.modelValue, (val) => {
  selectedTypes.value = [...val]
}, { deep: true })

watch(() => props.configValue, (val) => {
  config.value = { ...defaultConfig, ...val }
}, { deep: true })

function toggleType(typeValue) {
  const index = selectedTypes.value.indexOf(typeValue)
  if (index > -1) {
    if (selectedTypes.value.length > 1) {
      selectedTypes.value.splice(index, 1)
    }
  } else {
    selectedTypes.value.push(typeValue)
    if (!activeConfigs.value.includes(typeValue)) {
      activeConfigs.value.push(typeValue)
    }
  }
}
</script>

<style lang="scss" scoped>
.target-type-selector {
  .type-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;

    .type-card {
      position: relative;
      display: flex;
      align-items: center;
      padding: 16px;
      border: 2px solid #e4e7ed;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
      }

      &.active {
        border-color: #409eff;
        background-color: #ecf5ff;

        .type-icon {
          color: #409eff;
        }
      }

      .type-icon {
        flex-shrink: 0;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #606266;
        margin-right: 12px;
      }

      .type-info {
        flex: 1;

        .type-name {
          font-size: 16px;
          font-weight: 500;
          color: #303133;
          margin-bottom: 4px;
        }

        .type-desc {
          font-size: 12px;
          color: #909399;
          line-height: 1.4;
        }
      }

      .type-check {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #409eff;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }

  .type-configs {
    .config-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
    }

    .config-content {
      padding: 10px 0;
    }
  }
}
</style>

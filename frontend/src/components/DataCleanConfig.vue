<template>
  <div class="data-clean-config">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>数据清洗配置</span>
          <el-button type="primary" link @click="resetToDefault">
            <el-icon><RefreshRight /></el-icon>
            重置为默认
          </el-button>
        </div>
      </template>

      <el-form label-width="140px" label-position="left">
        <el-divider content-position="left">基础清洗</el-divider>

        <el-form-item label="去除HTML标签">
          <el-switch v-model="config.removeHtmlTags" />
          <span class="form-tip">移除文本中的HTML标签</span>
        </el-form-item>

        <el-form-item label="去除空白字符">
          <el-switch v-model="config.removeWhitespace" />
          <span class="form-tip">移除多余的空格、换行符等</span>
        </el-form-item>

        <el-form-item label="去除特殊字符">
          <el-switch v-model="config.removeSpecialChars" />
          <span class="form-tip">移除非字母数字的字符</span>
        </el-form-item>

        <el-form-item label="转换为小写">
          <el-switch v-model="config.toLowerCase" />
          <span class="form-tip">将所有文本转换为小写</span>
        </el-form-item>

        <el-form-item label="去除重复项">
          <el-switch v-model="config.removeDuplicates" />
          <span class="form-tip">移除重复的数据项</span>
        </el-form-item>

        <el-divider content-position="left">URL清洗</el-divider>

        <el-form-item label="URL去重">
          <el-switch v-model="config.urlDeduplication" />
          <span class="form-tip">对URL进行去重处理</span>
        </el-form-item>

        <el-form-item label="URL规范化">
          <el-switch v-model="config.urlNormalize" />
          <span class="form-tip">规范化URL格式</span>
        </el-form-item>

        <el-form-item label="过滤URL参数">
          <el-switch v-model="config.filterUrlParams" />
          <el-select
            v-if="config.filterUrlParams"
            v-model="config.preservedParams"
            multiple
            filterable
            allow-create
            placeholder="保留的参数名"
            class="param-select"
          >
            <el-option label="id" value="id" />
            <el-option label="page" value="page" />
            <el-option label="size" value="size" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">图片清洗</el-divider>

        <el-form-item label="过滤小图片">
          <el-switch v-model="config.filterSmallImages" />
          <div v-if="config.filterSmallImages" class="size-inputs">
            <el-input-number
              v-model="config.minImageWidth"
              :min="1"
              :max="10000"
              placeholder="最小宽度"
            />
            <span class="separator">×</span>
            <el-input-number
              v-model="config.minImageHeight"
              :min="1"
              :max="10000"
              placeholder="最小高度"
            />
            <span class="unit">像素</span>
          </div>
        </el-form-item>

        <el-form-item label="过滤图片格式">
          <el-switch v-model="config.filterImageFormats" />
          <el-checkbox-group v-if="config.filterImageFormats" v-model="config.allowedFormats">
            <el-checkbox value="jpg">JPG</el-checkbox>
            <el-checkbox value="jpeg">JPEG</el-checkbox>
            <el-checkbox value="png">PNG</el-checkbox>
            <el-checkbox value="gif">GIF</el-checkbox>
            <el-checkbox value="webp">WebP</el-checkbox>
            <el-checkbox value="svg">SVG</el-checkbox>
            <el-checkbox value="bmp">BMP</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="过滤无效图片">
          <el-switch v-model="config.filterInvalidImages" />
          <span class="form-tip">过滤无法访问或损坏的图片</span>
        </el-form-item>

        <el-divider content-position="left">文本清洗</el-divider>

        <el-form-item label="最小文本长度">
          <el-switch v-model="config.enableMinTextLength" />
          <el-input-number
            v-if="config.enableMinTextLength"
            v-model="config.minTextLength"
            :min="1"
            :max="10000"
          />
          <span class="form-tip" v-if="config.enableMinTextLength">字符</span>
        </el-form-item>

        <el-form-item label="最大文本长度">
          <el-switch v-model="config.enableMaxTextLength" />
          <el-input-number
            v-if="config.enableMaxTextLength"
            v-model="config.maxTextLength"
            :min="1"
            :max="100000"
          />
          <span class="form-tip" v-if="config.enableMaxTextLength">字符，超出将被截断</span>
        </el-form-item>

        <el-form-item label="过滤关键词">
          <el-switch v-model="config.enableKeywordFilter" />
          <div v-if="config.enableKeywordFilter" class="keyword-section">
            <el-radio-group v-model="config.keywordFilterMode" class="filter-mode">
              <el-radio value="exclude">排除模式</el-radio>
              <el-radio value="include">包含模式</el-radio>
            </el-radio-group>
            <el-select
              v-model="config.filterKeywords"
              multiple
              filterable
              allow-create
              placeholder="输入关键词后回车添加"
              class="keyword-select"
            />
          </div>
        </el-form-item>

        <el-divider content-position="left">自定义清洗函数</el-divider>

        <el-form-item label="启用自定义函数">
          <el-switch v-model="config.enableCustomFunction" />
        </el-form-item>

        <div v-if="config.enableCustomFunction" class="custom-function-section">
          <el-form-item label="清洗函数">
            <el-select v-model="config.selectedFunction" placeholder="选择预设函数">
              <el-option label="去除HTML实体" value="decodeHtmlEntities" />
              <el-option label="提取数字" value="extractNumbers" />
              <el-option label="提取邮箱" value="extractEmails" />
              <el-option label="提取URL" value="extractUrls" />
              <el-option label="去除表情符号" value="removeEmojis" />
              <el-option label="中文繁简转换" value="chineseConvert" />
            </el-select>
          </el-form-item>

          <el-form-item label="自定义代码">
            <div class="code-editor">
              <el-input
                v-model="config.customFunctionCode"
                type="textarea"
                :rows="8"
                placeholder="输入自定义Python清洗函数代码，例如：
def clean(data):
    # data 是提取到的原始数据
    # 返回清洗后的数据
    return data.strip()"
              />
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="small" @click="testCustomFunction">
              测试函数
            </el-button>
          </el-form-item>
        </div>
      </el-form>
    </el-card>

    <el-dialog v-model="testDialogVisible" title="测试清洗函数" width="500px">
      <el-form>
        <el-form-item label="测试数据">
          <el-input
            v-model="testInput"
            type="textarea"
            :rows="3"
            placeholder="输入测试数据"
          />
        </el-form-item>
        <el-form-item label="输出结果">
          <el-input
            v-model="testOutput"
            type="textarea"
            :rows="3"
            readonly
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="runTest">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const defaultConfig = {
  removeHtmlTags: true,
  removeWhitespace: true,
  removeSpecialChars: false,
  toLowerCase: false,
  removeDuplicates: true,
  urlDeduplication: true,
  urlNormalize: true,
  filterUrlParams: false,
  preservedParams: [],
  filterSmallImages: false,
  minImageWidth: 100,
  minImageHeight: 100,
  filterImageFormats: false,
  allowedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
  filterInvalidImages: false,
  enableMinTextLength: false,
  minTextLength: 10,
  enableMaxTextLength: false,
  maxTextLength: 10000,
  enableKeywordFilter: false,
  keywordFilterMode: 'exclude',
  filterKeywords: [],
  enableCustomFunction: false,
  selectedFunction: '',
  customFunctionCode: ''
}

const config = reactive({ ...defaultConfig, ...props.modelValue })

const testDialogVisible = ref(false)
const testInput = ref('')
const testOutput = ref('')

watch(config, (val) => {
  emit('update:modelValue', { ...val })
}, { deep: true })

watch(() => props.modelValue, (val) => {
  Object.assign(config, { ...defaultConfig, ...val })
}, { deep: true })

function resetToDefault() {
  Object.assign(config, defaultConfig)
  ElMessage.success('已重置为默认配置')
}

function testCustomFunction() {
  testDialogVisible.value = true
  testInput.value = ''
  testOutput.value = ''
}

function runTest() {
  if (!testInput.value) {
    ElMessage.warning('请输入测试数据')
    return
  }

  try {
    let result = testInput.value
    
    if (config.removeHtmlTags) {
      result = result.replace(/<[^>]*>/g, '')
    }
    
    if (config.removeWhitespace) {
      result = result.replace(/\s+/g, ' ').trim()
    }
    
    if (config.toLowerCase) {
      result = result.toLowerCase()
    }
    
    testOutput.value = result
    ElMessage.success('测试完成')
  } catch (error) {
    testOutput.value = `错误: ${error.message}`
    ElMessage.error('执行失败')
  }
}
</script>

<style lang="scss" scoped>
.data-clean-config {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .form-tip {
    margin-left: 10px;
    color: #909399;
    font-size: 12px;
  }

  .size-inputs {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 5px;

    .separator {
      color: #606266;
    }

    .unit {
      color: #909399;
      font-size: 12px;
    }
  }

  .param-select,
  .keyword-select {
    width: 100%;
    margin-top: 5px;
  }

  .keyword-section {
    margin-top: 5px;

    .filter-mode {
      margin-bottom: 10px;
    }
  }

  .custom-function-section {
    background: #f5f7fa;
    padding: 15px;
    border-radius: 4px;
    margin-top: 10px;

    .code-editor {
      :deep(.el-textarea__inner) {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
      }
    }
  }
}
</style>

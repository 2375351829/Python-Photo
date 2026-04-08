<template>
  <div class="rule-config">
    <div class="smart-extract-section" v-if="showPreview && url">
      <el-button type="primary" @click="handleSmartExtract" :loading="smartExtractLoading">
        <el-icon><MagicStick /></el-icon>
        智能识别
      </el-button>
      <span class="tip">自动分析页面并推荐提取规则</span>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="rule-tabs">
      <el-tab-pane label="CSS选择器" name="css">
        <div class="rule-section">
          <div class="rule-item" v-for="(rule, index) in cssRules" :key="index">
            <el-row :gutter="10" align="middle">
              <el-col :span="6">
                <el-input v-model="rule.name" placeholder="规则名称" />
              </el-col>
              <el-col :span="14">
                <el-input v-model="rule.selector" placeholder="CSS选择器，如: .content img" />
              </el-col>
              <el-col :span="4">
                <el-tooltip content="提取属性（可选）" placement="top">
                  <el-input v-model="rule.attribute" placeholder="属性" size="small" />
                </el-tooltip>
              </el-col>
              <el-col :span="2">
                <el-button type="danger" link @click="removeRule('css', index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" link @click="addRule('css')">
            <el-icon><Plus /></el-icon> 添加规则
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="XPath规则" name="xpath">
        <div class="rule-section">
          <div class="rule-item" v-for="(rule, index) in xpathRules" :key="index">
            <el-row :gutter="10" align="middle">
              <el-col :span="6">
                <el-input v-model="rule.name" placeholder="规则名称" />
              </el-col>
              <el-col :span="16">
                <el-input v-model="rule.selector" placeholder="XPath表达式，如: //div[@class='content']//img/@src" />
              </el-col>
              <el-col :span="2">
                <el-button type="danger" link @click="removeRule('xpath', index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" link @click="addRule('xpath')">
            <el-icon><Plus /></el-icon> 添加规则
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="正则表达式" name="regex">
        <div class="rule-section">
          <div class="rule-item" v-for="(rule, index) in regexRules" :key="index">
            <el-row :gutter="10" align="middle">
              <el-col :span="6">
                <el-input v-model="rule.name" placeholder="规则名称" />
              </el-col>
              <el-col :span="16">
                <el-input v-model="rule.pattern" placeholder="正则表达式，如: https?://[^\s]+\.(jpg|png|gif)" />
              </el-col>
              <el-col :span="2">
                <el-button type="danger" link @click="removeRule('regex', index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" link @click="addRule('regex')">
            <el-icon><Plus /></el-icon> 添加规则
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="JSON路径" name="json">
        <div class="rule-section">
          <div class="rule-item" v-for="(rule, index) in jsonRules" :key="index">
            <el-row :gutter="10" align="middle">
              <el-col :span="6">
                <el-input v-model="rule.name" placeholder="规则名称" />
              </el-col>
              <el-col :span="16">
                <el-input v-model="rule.path" placeholder="JSON路径，如: data.items[*].image_url" />
              </el-col>
              <el-col :span="2">
                <el-button type="danger" link @click="removeRule('json', index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" link @click="addRule('json')">
            <el-icon><Plus /></el-icon> 添加规则
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="preview-section" v-if="showPreview">
      <el-divider />
      <div class="preview-header">
        <span>预览结果</span>
        <el-button type="primary" size="small" @click="handlePreview" :loading="previewLoading">
          执行预览
        </el-button>
      </div>
      <div class="preview-result" v-if="previewResult.length > 0">
        <el-table :data="previewResult" size="small" max-height="300">
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)" size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="值" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link v-if="isUrl(row.value)" :href="row.value" target="_blank" type="primary">
                {{ truncateUrl(row.value) }}
              </el-link>
              <span v-else>{{ truncateText(row.value, 100) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="rule_name" label="规则" width="120" />
        </el-table>
        <div class="preview-summary">
          共匹配到 <strong>{{ previewResult.length }}</strong> 条结果
        </div>
      </div>
      <el-empty v-else-if="!previewLoading" description="暂无预览结果，请配置规则后点击预览" :image-size="60" />
    </div>

    <el-dialog v-model="smartExtractDialogVisible" title="智能识别结果" width="700px">
      <div class="smart-extract-result" v-if="smartExtractResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="识别状态">
            <el-tag :type="smartExtractResult.success ? 'success' : 'danger'">
              {{ smartExtractResult.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度">
            <el-progress :percentage="Math.round(smartExtractResult.confidence * 100)" :stroke-width="10" />
          </el-descriptions-item>
          <el-descriptions-item label="响应类型">
            <el-tag>{{ smartExtractResult.is_json_response ? 'JSON' : 'HTML' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="标题" v-if="smartExtractResult.title">
            {{ smartExtractResult.title }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="extracted-content" v-if="smartExtractResult.content">
          <h4>提取的正文预览：</h4>
          <p class="content-preview">{{ smartExtractResult.content }}</p>
        </div>

        <div class="extracted-images" v-if="smartExtractResult.images && smartExtractResult.images.length > 0">
          <h4>提取的图片 ({{ smartExtractResult.images.length }}张)：</h4>
          <div class="image-grid">
            <el-image
              v-for="(img, index) in smartExtractResult.images.slice(0, 6)"
              :key="index"
              :src="img"
              :preview-src-list="smartExtractResult.images"
              fit="cover"
              class="preview-image"
            />
          </div>
        </div>

        <div class="suggested-rules" v-if="hasSuggestedRules">
          <h4>推荐的提取规则：</h4>
          <div class="rule-suggestions">
            <div v-for="(rules, type) in smartExtractResult.suggested_rules" :key="type" class="rule-group">
              <div v-for="(rule, index) in rules" :key="index" class="rule-suggestion-item">
                <el-card shadow="hover">
                  <div class="suggestion-header">
                    <span class="rule-name">{{ rule.name }}</span>
                    <el-tag size="small">{{ type.toUpperCase() }}</el-tag>
                  </div>
                  <div class="rule-value">
                    <code>{{ rule.selector || rule.path || rule.pattern }}</code>
                  </div>
                  <div class="rule-desc" v-if="rule.description">{{ rule.description }}</div>
                  <el-button type="primary" size="small" @click="applySuggestedRule(type, rule)">
                    应用此规则
                  </el-button>
                </el-card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Delete, Plus, MagicStick } from '@element-plus/icons-vue'
import { previewRules, smartExtract } from '@/api/task'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  url: {
    type: String,
    default: ''
  },
  showPreview: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const activeTab = ref('css')
const previewLoading = ref(false)
const previewResult = ref([])
const smartExtractLoading = ref(false)
const smartExtractDialogVisible = ref(false)
const smartExtractResult = ref(null)

const cssRules = ref(props.modelValue.css || [])
const xpathRules = ref(props.modelValue.xpath || [])
const regexRules = ref(props.modelValue.regex || [])
const jsonRules = ref(props.modelValue.json || [])

const rules = computed(() => ({
  css: cssRules.value,
  xpath: xpathRules.value,
  regex: regexRules.value,
  json: jsonRules.value
}))

const hasSuggestedRules = computed(() => {
  if (!smartExtractResult.value?.suggested_rules) return false
  return Object.values(smartExtractResult.value.suggested_rules).some(arr => arr && arr.length > 0)
})

watch(rules, (val) => {
  emit('update:modelValue', val)
}, { deep: true })

watch(() => props.modelValue, (val) => {
  cssRules.value = val.css || []
  xpathRules.value = val.xpath || []
  regexRules.value = val.regex || []
  jsonRules.value = val.json || []
}, { deep: true })

function addRule(type) {
  const newRule = type === 'regex' 
    ? { name: '', pattern: '' }
    : type === 'json'
    ? { name: '', path: '' }
    : { name: '', selector: '', attribute: '' }
  
  switch (type) {
    case 'css':
      cssRules.value.push(newRule)
      break
    case 'xpath':
      xpathRules.value.push(newRule)
      break
    case 'regex':
      regexRules.value.push(newRule)
      break
    case 'json':
      jsonRules.value.push(newRule)
      break
  }
}

function removeRule(type, index) {
  switch (type) {
    case 'css':
      cssRules.value.splice(index, 1)
      break
    case 'xpath':
      xpathRules.value.splice(index, 1)
      break
    case 'regex':
      regexRules.value.splice(index, 1)
      break
    case 'json':
      jsonRules.value.splice(index, 1)
      break
  }
}

async function handlePreview() {
  if (!props.url) {
    ElMessage.warning('请先输入目标URL')
    return
  }

  const hasRules = cssRules.value.some(r => r.selector) ||
                   xpathRules.value.some(r => r.selector) ||
                   regexRules.value.some(r => r.pattern) ||
                   jsonRules.value.some(r => r.path)

  if (!hasRules) {
    ElMessage.warning('请至少配置一条规则')
    return
  }

  previewLoading.value = true
  try {
    const res = await previewRules({
      url: props.url,
      rules: rules.value
    })
    previewResult.value = res.data?.matched_resources || []
    if (previewResult.value.length === 0) {
      ElMessage.info('未匹配到任何结果')
    } else {
      ElMessage.success(`成功匹配到 ${previewResult.value.length} 条结果`)
    }
  } catch (error) {
    console.error('预览失败:', error)
    previewResult.value = []
    ElMessage.error('预览失败，请检查规则是否正确')
  } finally {
    previewLoading.value = false
  }
}

async function handleSmartExtract() {
  if (!props.url) {
    ElMessage.warning('请先输入目标URL')
    return
  }

  smartExtractLoading.value = true
  try {
    const res = await smartExtract({ url: props.url })
    smartExtractResult.value = res
    smartExtractDialogVisible.value = true
    
    if (res.success) {
      ElMessage.success('智能识别完成')
    } else {
      ElMessage.warning(res.message || '识别失败')
    }
  } catch (error) {
    console.error('智能识别失败:', error)
    ElMessage.error('智能识别失败')
  } finally {
    smartExtractLoading.value = false
  }
}

function applySuggestedRule(type, rule) {
  const newRule = type === 'regex'
    ? { name: rule.name, pattern: rule.pattern }
    : type === 'json'
    ? { name: rule.name, path: rule.path }
    : { name: rule.name, selector: rule.selector || rule.path }

  switch (type) {
    case 'css':
      cssRules.value.push(newRule)
      activeTab.value = 'css'
      break
    case 'xpath':
      xpathRules.value.push(newRule)
      activeTab.value = 'xpath'
      break
    case 'regex':
      regexRules.value.push(newRule)
      activeTab.value = 'regex'
      break
    case 'json':
      jsonRules.value.push(newRule)
      activeTab.value = 'json'
      break
  }
  
  ElMessage.success('规则已应用')
  smartExtractDialogVisible.value = false
}

function getTypeTagType(type) {
  const typeMap = {
    image: 'success',
    video: 'warning',
    link: 'primary',
    text: 'info',
    json_value: '',
    regex_match: 'danger'
  }
  return typeMap[type] || ''
}

function isUrl(value) {
  if (!value) return false
  return value.startsWith('http://') || value.startsWith('https://')
}

function truncateUrl(url) {
  if (!url) return ''
  return url.length > 60 ? url.substring(0, 60) + '...' : url
}

function truncateText(text, maxLength) {
  if (!text) return ''
  const str = String(text)
  return str.length > maxLength ? str.substring(0, maxLength) + '...' : str
}
</script>

<style lang="scss" scoped>
.rule-config {
  .smart-extract-section {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;

    .tip {
      color: #909399;
      font-size: 13px;
    }
  }

  .rule-tabs {
    margin-bottom: 15px;
  }

  .rule-section {
    .rule-item {
      margin-bottom: 10px;
    }
  }

  .preview-section {
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .preview-result {
      background-color: #f5f7fa;
      border-radius: 4px;
      padding: 10px;

      .preview-summary {
        margin-top: 10px;
        text-align: right;
        color: #606266;
        font-size: 13px;
      }
    }
  }

  .smart-extract-result {
    .extracted-content {
      margin-top: 15px;

      h4 {
        margin-bottom: 8px;
        color: #303133;
      }

      .content-preview {
        background: #f5f7fa;
        padding: 10px;
        border-radius: 4px;
        font-size: 13px;
        line-height: 1.6;
        color: #606266;
        max-height: 100px;
        overflow-y: auto;
      }
    }

    .extracted-images {
      margin-top: 15px;

      h4 {
        margin-bottom: 8px;
        color: #303133;
      }

      .image-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;

        .preview-image {
          width: 80px;
          height: 80px;
          border-radius: 4px;
        }
      }
    }

    .suggested-rules {
      margin-top: 20px;

      h4 {
        margin-bottom: 10px;
        color: #303133;
      }

      .rule-suggestions {
        max-height: 300px;
        overflow-y: auto;

        .rule-group {
          margin-bottom: 10px;
        }

        .rule-suggestion-item {
          margin-bottom: 10px;

          .el-card {
            :deep(.el-card__body) {
              padding: 12px;
            }
          }

          .suggestion-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;

            .rule-name {
              font-weight: 500;
              color: #303133;
            }
          }

          .rule-value {
            margin-bottom: 8px;

            code {
              background: #f5f7fa;
              padding: 4px 8px;
              border-radius: 4px;
              font-size: 12px;
              color: #409eff;
              word-break: break-all;
            }
          }

          .rule-desc {
            font-size: 12px;
            color: #909399;
            margin-bottom: 8px;
          }
        }
      }
    }
  }
}
</style>

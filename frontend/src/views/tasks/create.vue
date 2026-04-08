<template>
  <div class="task-create-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑爬虫任务' : '创建爬虫任务' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="task-form"
      >
        <el-divider content-position="left">基本信息</el-divider>
        
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入任务名称" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="目标URL" prop="url">
          <el-input v-model="formData.url" placeholder="请输入要爬取的网站URL" clearable>
            <template #prepend>
              <el-select v-model="formData.urlProtocol" style="width: 90px">
                <el-option label="https://" value="https://" />
                <el-option label="http://" value="http://" />
              </el-select>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="目标类型" prop="targetTypes">
          <el-checkbox-group v-model="formData.targetTypes">
            <el-checkbox value="image">图片</el-checkbox>
            <el-checkbox value="video">视频</el-checkbox>
            <el-checkbox value="text">文本</el-checkbox>
            <el-checkbox value="link">链接</el-checkbox>
            <el-checkbox value="file">文件</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-divider content-position="left">爬取规则配置</el-divider>

        <RuleConfig v-model="formData.rules" :url="fullUrl" :show-preview="true" />

        <el-divider content-position="left">数据清洗配置</el-divider>

        <DataCleanConfig v-model="formData.dataCleaning" />

        <el-divider content-position="left">爬取参数</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="爬取深度" prop="depth">
              <el-input-number v-model="formData.depth" :min="1" :max="10" />
              <span class="form-tip">页面爬取的深度层级</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大结果数" prop="maxResults">
              <el-input-number v-model="formData.maxResults" :min="1" :max="100000" />
              <span class="form-tip">最多爬取的结果数量</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="请求间隔" prop="requestInterval">
              <el-input-number v-model="formData.requestInterval" :min="0" :max="60000" :step="100" />
              <span class="form-tip">毫秒，防止请求过快</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="超时时间" prop="timeout">
              <el-input-number v-model="formData.timeout" :min="1000" :max="120000" :step="1000" />
              <span class="form-tip">毫秒，请求超时时间</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="文件格式" prop="fileFormats">
          <el-checkbox-group v-model="formData.fileFormats">
            <el-checkbox value="jpg">JPG</el-checkbox>
            <el-checkbox value="jpeg">JPEG</el-checkbox>
            <el-checkbox value="png">PNG</el-checkbox>
            <el-checkbox value="gif">GIF</el-checkbox>
            <el-checkbox value="webp">WebP</el-checkbox>
            <el-checkbox value="svg">SVG</el-checkbox>
            <el-checkbox value="mp4">MP4</el-checkbox>
            <el-checkbox value="pdf">PDF</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="最小文件大小" prop="minFileSize">
          <el-input v-model="formData.minFileSize" placeholder="如: 1024 (字节)" />
          <span class="form-tip">过滤过小的文件，单位：字节</span>
        </el-form-item>

        <el-form-item label="保存路径" prop="savePath">
          <el-input v-model="formData.savePath" placeholder="文件保存路径，如: /data/crawls/task1" />
        </el-form-item>

        <el-divider content-position="left">调度设置</el-divider>

        <el-form-item label="执行方式" prop="scheduleType">
          <el-radio-group v-model="formData.scheduleType">
            <el-radio value="immediate">立即执行</el-radio>
            <el-radio value="scheduled">定时执行</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="formData.scheduleType === 'scheduled'" label="Cron表达式" prop="cronExpression">
          <el-input v-model="formData.cronExpression" placeholder="如: 0 0 2 * * ? (每天凌晨2点执行)">
            <template #append>
              <el-popover placement="top" :width="400" trigger="click">
                <template #reference>
                  <el-button>帮助</el-button>
                </template>
                <div class="cron-help">
                  <p><strong>Cron表达式格式：</strong></p>
                  <p>秒 分 时 日 月 周</p>
                  <el-table :data="cronExamples" size="small">
                    <el-table-column prop="expression" label="表达式" width="150" />
                    <el-table-column prop="description" label="说明" />
                  </el-table>
                </div>
              </el-popover>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="调试模式" prop="debugMode">
          <el-switch v-model="formData.debugMode" />
          <span class="form-tip">开启后将输出详细日志</span>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建任务' }}
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
          <el-button v-if="!isEdit" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import RuleConfig from '@/components/RuleConfig.vue'
import DataCleanConfig from '@/components/DataCleanConfig.vue'
import { createTask, updateTask, getTask } from '@/api/task'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const loading = ref(false)

const isEdit = computed(() => !!route.params.id)

const formData = reactive({
  name: '',
  url: '',
  urlProtocol: 'https://',
  targetTypes: ['image'],
  description: '',
  rules: {
    css: [],
    xpath: [],
    regex: [],
    json: []
  },
  dataCleaning: {
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
  },
  depth: 2,
  maxResults: 1000,
  requestInterval: 500,
  timeout: 30000,
  fileFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
  minFileSize: '',
  savePath: '',
  scheduleType: 'immediate',
  cronExpression: '',
  debugMode: false
})

const fullUrl = computed(() => {
  if (!formData.url) return ''
  if (formData.url.startsWith('http://') || formData.url.startsWith('https://')) {
    return formData.url
  }
  return formData.urlProtocol + formData.url
})

const rules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入目标URL', trigger: 'blur' }
  ],
  targetTypes: [
    { type: 'array', required: true, message: '请至少选择一个目标类型', trigger: 'change' }
  ],
  depth: [
    { required: true, message: '请设置爬取深度', trigger: 'change' }
  ],
  maxResults: [
    { required: true, message: '请设置最大结果数', trigger: 'change' }
  ]
}

const cronExamples = [
  { expression: '0 0 2 * * ?', description: '每天凌晨2点执行' },
  { expression: '0 0 */6 * * ?', description: '每6小时执行一次' },
  { expression: '0 0 0 * * MON', description: '每周一凌晨执行' },
  { expression: '0 0 0 1 * ?', description: '每月1号凌晨执行' },
  { expression: '0 30 10 * * ?', description: '每天10:30执行' }
]

async function loadTaskData() {
  if (!isEdit.value) return
  
  try {
    loading.value = true
    const res = await getTask(route.params.id)
    const task = res.data
    
    Object.keys(formData).forEach(key => {
      if (task[key] !== undefined) {
        if (key === 'url') {
          const url = task.url
          if (url.startsWith('https://')) {
            formData.urlProtocol = 'https://'
            formData.url = url.replace('https://', '')
          } else if (url.startsWith('http://')) {
            formData.urlProtocol = 'http://'
            formData.url = url.replace('http://', '')
          } else {
            formData.url = url
          }
        } else {
          formData[key] = task[key]
        }
      }
    })
  } catch (error) {
    console.error('加载任务数据失败:', error)
    ElMessage.error('加载任务数据失败')
    router.back()
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const submitData = {
      ...formData,
      url: fullUrl.value
    }
    
    if (isEdit.value) {
      await updateTask(route.params.id, submitData)
      ElMessage.success('任务更新成功')
    } else {
      await createTask(submitData)
      ElMessage.success('任务创建成功')
    }
    router.push('/tasks')
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.back()
}

function handleReset() {
  formRef.value.resetFields()
  formData.rules = {
    css: [],
    xpath: [],
    regex: [],
    json: []
  }
  formData.dataCleaning = {
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
}

onMounted(() => {
  loadTaskData()
})
</script>

<style lang="scss" scoped>
.task-create-container {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .task-form {
    max-width: 900px;

    .form-tip {
      margin-left: 10px;
      color: #909399;
      font-size: 12px;
    }
  }

  .cron-help {
    p {
      margin: 5px 0;
      
      strong {
        color: #409eff;
      }
    }
  }
}
</style>

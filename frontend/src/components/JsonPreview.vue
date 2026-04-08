<template>
  <div class="json-preview">
    <div class="json-toolbar">
      <el-button size="small" @click="copyJson">复制</el-button>
      <el-button size="small" @click="expandAll">全部展开</el-button>
      <el-button size="small" @click="collapseAll">全部折叠</el-button>
    </div>
    
    <div class="json-content" ref="jsonContent">
      <pre><code v-html="highlightedJson"></code></pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  data: {
    type: [Object, Array, String, Number, Boolean],
    required: true
  }
})

const expandedPaths = ref(new Set())

const jsonString = computed(() => {
  if (typeof props.data === 'string') {
    try {
      return JSON.stringify(JSON.parse(props.data), null, 2)
    } catch {
      return props.data
    }
  }
  return JSON.stringify(props.data, null, 2)
})

const highlightedJson = computed(() => {
  return syntaxHighlight(jsonString.value)
})

const syntaxHighlight = (json) => {
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'number'
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'key'
        } else {
          cls = 'string'
        }
      } else if (/true|false/.test(match)) {
        cls = 'boolean'
      } else if (/null/.test(match)) {
        cls = 'null'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}

const copyJson = async () => {
  try {
    await navigator.clipboard.writeText(jsonString.value)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

const expandAll = () => {
  ElMessage.info('全部展开')
}

const collapseAll = () => {
  ElMessage.info('全部折叠')
}
</script>

<style scoped>
.json-preview {
  background: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
}

.json-toolbar {
  padding: 10px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.json-content {
  max-height: 500px;
  overflow: auto;
  padding: 15px;
}

.json-content pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.json-content :deep(.key) {
  color: #9cdcfe;
}

.json-content :deep(.string) {
  color: #ce9178;
}

.json-content :deep(.number) {
  color: #b5cea8;
}

.json-content :deep(.boolean) {
  color: #569cd6;
}

.json-content :deep(.null) {
  color: #569cd6;
}
</style>

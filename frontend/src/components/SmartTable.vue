<template>
  <div class="smart-table">
    <div class="table-header">
      <el-input
        v-model="searchText"
        placeholder="搜索数据..."
        prefix-icon="Search"
        clearable
        style="width: 300px"
      />
      <div class="column-config">
        <el-dropdown>
          <el-button>
            列配置 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-checkbox-group v-model="visibleColumns">
                <el-dropdown-item v-for="col in allColumns" :key="col.prop">
                  <el-checkbox :value="col.prop">{{ col.label }}</el-checkbox>
                </el-dropdown-item>
              </el-checkbox-group>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <el-table
      :data="filteredData"
      border
      stripe
      style="width: 100%"
      @sort-change="handleSortChange"
    >
      <el-table-column
        v-for="col in displayColumns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :sortable="col.sortable ? 'custom' : false"
        :width="col.width"
        :formatter="col.formatter"
      >
        <template #default="{ row }">
          <template v-if="isObject(row[col.prop])">
            <el-button
              size="small"
              @click="showNestedData(row[col.prop], col.label)"
            >
              查看详情
            </el-button>
          </template>
          <template v-else-if="isArray(row[col.prop])">
            <el-tag>{{ row[col.prop].length }} 项</el-tag>
            <el-button
              size="small"
              link
              @click="showNestedData(row[col.prop], col.label)"
            >
              查看
            </el-button>
          </template>
          <template v-else>
            {{ formatValue(row[col.prop], col) }}
          </template>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <el-dialog v-model="nestedDialogVisible" :title="nestedTitle" width="60%">
      <json-preview :data="nestedData" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import JsonPreview from './JsonPreview.vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  }
})

const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const visibleColumns = ref([])
const nestedDialogVisible = ref(false)
const nestedData = ref(null)
const nestedTitle = ref('')
const sortProp = ref('')
const sortOrder = ref('')

const allColumns = computed(() => {
  if (props.columns.length > 0) return props.columns
  
  if (props.data.length > 0) {
    const firstRow = props.data[0]
    return Object.keys(firstRow).map(key => ({
      prop: key,
      label: formatKeyToLabel(key),
      sortable: true
    }))
  }
  return []
})

const displayColumns = computed(() => {
  if (visibleColumns.value.length === 0) return allColumns.value
  return allColumns.value.filter(col => visibleColumns.value.includes(col.prop))
})

const filteredData = computed(() => {
  let data = [...props.data]
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    data = data.filter(row => {
      return Object.values(row).some(val => 
        String(val).toLowerCase().includes(search)
      )
    })
  }
  
  if (sortProp.value && sortOrder.value) {
    data.sort((a, b) => {
      const aVal = a[sortProp.value]
      const bVal = b[sortProp.value]
      if (aVal < bVal) return sortOrder.value === 'ascending' ? -1 : 1
      if (aVal > bVal) return sortOrder.value === 'ascending' ? 1 : -1
      return 0
    })
  }
  
  const start = (currentPage.value - 1) * pageSize.value
  return data.slice(start, start + pageSize.value)
})

const total = computed(() => props.data.length)

const formatKeyToLabel = (key) => {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

const formatValue = (value, col) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') {
    if (col.type === 'date') {
      return new Date(value).toLocaleString()
    }
    return value.toLocaleString()
  }
  return value
}

const isObject = (val) => {
  return val && typeof val === 'object' && !Array.isArray(val)
}

const isArray = (val) => {
  return Array.isArray(val)
}

const showNestedData = (data, title) => {
  nestedData.value = data
  nestedTitle.value = title
  nestedDialogVisible.value = true
}

const handleSortChange = ({ prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

watch(() => props.columns, (cols) => {
  if (cols.length > 0) {
    visibleColumns.value = cols.map(c => c.prop)
  }
}, { immediate: true })
</script>

<style scoped>
.smart-table {
  width: 100%;
}

.table-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>

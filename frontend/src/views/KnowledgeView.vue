<template>
  <div class="knowledge-container">
    <div class="knowledge-header">
      <h2>📚 知识库管理</h2>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索知识..."
          style="width: 300px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="showAddDialog" :icon="Plus">
          添加知识
        </el-button>
      </div>
    </div>

    <div class="knowledge-content">
      <el-table
        :data="knowledgeList"
        v-loading="loading"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="question" label="问题" min-width="200" />
        <el-table-column prop="answer" label="答案" min-width="300" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.category" type="success">{{ row.category }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editKnowledge(row)" :icon="Edit">
              编辑
            </el-button>
            <el-popconfirm
              title="确定要删除这条知识吗？"
              @confirm="deleteKnowledge(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger" :icon="Delete">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
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
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="问题" prop="question">
          <el-input
            v-model="formData.question"
            placeholder="请输入问题"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        <el-form-item label="答案" prop="answer">
          <el-input
            v-model="formData.answer"
            placeholder="请输入答案"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="formData.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input
            v-model="keywordsInput"
            placeholder="多个关键词用逗号分隔"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio :label="0">草稿</el-radio>
            <el-radio :label="1">发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const knowledgeList = ref([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const dialogTitle = ref('添加知识')
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const formData = ref({
  question: '',
  answer: '',
  category: '',
  keywords: [],
  status: 1
})

const keywordsInput = ref('')

const formRules = {
  question: [{ required: true, message: '请输入问题', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入答案', trigger: 'blur' }]
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const fetchKnowledgeList = async () => {
  loading.value = true
  try {
    const response = await knowledgeAPI.getList({
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
      keyword: searchKeyword.value || undefined
    })
    knowledgeList.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取知识库列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchKnowledgeList()
}

const handlePageChange = () => {
  fetchKnowledgeList()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchKnowledgeList()
}

const showAddDialog = () => {
  isEdit.value = false
  dialogTitle.value = '添加知识'
  dialogVisible.value = true
}

const editKnowledge = (row) => {
  isEdit.value = true
  editId.value = row.id
  dialogTitle.value = '编辑知识'
  formData.value = {
    question: row.question,
    answer: row.answer,
    category: row.category || '',
    keywords: row.keywords || [],
    status: row.status
  }
  keywordsInput.value = (row.keywords || []).join(', ')
  dialogVisible.value = true
}

const resetForm = () => {
  formData.value = {
    question: '',
    answer: '',
    category: '',
    keywords: [],
    status: 1
  }
  keywordsInput.value = ''
  formRef.value?.resetFields()
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 处理关键词
    const keywords = keywordsInput.value
      ? keywordsInput.value.split(/[,，]/).map(k => k.trim()).filter(k => k)
      : []
    
    const data = {
      ...formData.value,
      keywords
    }
    
    submitting.value = true
    
    try {
      if (isEdit.value) {
        await knowledgeAPI.update(editId.value, data)
        ElMessage.success('更新成功')
      } else {
        await knowledgeAPI.create(data)
        ElMessage.success('添加成功')
      }
      
      dialogVisible.value = false
      fetchKnowledgeList()
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '添加失败')
      console.error(error)
    } finally {
      submitting.value = false
    }
  })
}

const deleteKnowledge = async (id) => {
  try {
    await knowledgeAPI.delete(id)
    ElMessage.success('删除成功')
    fetchKnowledgeList()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

onMounted(() => {
  fetchKnowledgeList()
})
</script>

<style scoped>
.knowledge-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: white;
}

.knowledge-header {
  padding: 20px 30px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.knowledge-content {
  flex: 1;
  padding: 20px 30px;
  overflow: auto;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background: #f5f7fa;
  font-weight: 600;
}
</style>


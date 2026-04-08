<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>页面不存在</h2>
      <p>抱歉，您访问的页面不存在或已被删除</p>
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
.not-found-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;

  .not-found-content {
    text-align: center;

    h1 {
      font-size: 120px;
      color: #409eff;
      margin: 0;
      line-height: 1;
    }

    h2 {
      font-size: 24px;
      color: #303133;
      margin: 20px 0 10px;
    }

    p {
      color: #909399;
      margin-bottom: 30px;
    }
  }
}
</style>

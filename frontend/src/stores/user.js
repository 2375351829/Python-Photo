import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, logout as logoutApi, getUserInfo } from '@/api/auth'
import router from '@/router'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'token'
const USER_INFO_KEY = 'userInfo'

export const useUserStore = defineStore('user', () => {
  const token = ref('')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const userId = computed(() => userInfo.value?.id || null)
  const email = computed(() => userInfo.value?.email || '')
  const avatar = computed(() => userInfo.value?.avatar || '')

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function setUserInfo(info) {
    userInfo.value = info
    if (info) {
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(info))
    } else {
      localStorage.removeItem(USER_INFO_KEY)
    }
  }

  function clearAuth() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_INFO_KEY)
  }

  function initFromStorage() {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    const storedUserInfo = localStorage.getItem(USER_INFO_KEY)

    if (storedToken) {
      token.value = storedToken
    }

    if (storedUserInfo) {
      try {
        userInfo.value = JSON.parse(storedUserInfo)
      } catch (e) {
        console.error('解析用户信息失败:', e)
        userInfo.value = null
      }
    }
  }

  async function login(loginData) {
    try {
      const res = await loginApi(loginData)
      setToken(res.access_token)
      setUserInfo(res.user)
      ElMessage.success('登录成功')
      return res
    } catch (error) {
      throw error
    }
  }

  async function register(userData) {
    try {
      const res = await registerApi(userData)
      ElMessage.success('注册成功')
      return res
    } catch (error) {
      throw error
    }
  }

  async function logout() {
    try {
      await logoutApi()
    } catch (error) {
      console.error('登出接口调用失败:', error)
    } finally {
      clearAuth()
      ElMessage.success('已退出登录')
      router.push('/login')
    }
  }

  async function fetchUserInfo() {
    try {
      const res = await getUserInfo()
      setUserInfo(res)
      return res
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    userId,
    email,
    avatar,
    setToken,
    setUserInfo,
    clearAuth,
    initFromStorage,
    login,
    register,
    logout,
    fetchUserInfo
  }
})

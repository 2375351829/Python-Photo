import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/register/index.vue'),
    meta: {
      title: '注册',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/home',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/home/index.vue'),
        meta: {
          title: '首页',
          requiresAuth: true
        }
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/views/tasks/index.vue'),
        meta: {
          title: '任务管理',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/create',
        name: 'TaskCreate',
        component: () => import('@/views/tasks/create.vue'),
        meta: {
          title: '创建任务',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/:id/edit',
        name: 'TaskEdit',
        component: () => import('@/views/tasks/create.vue'),
        meta: {
          title: '编辑任务',
          requiresAuth: true
        }
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/tasks/detail.vue'),
        meta: {
          title: '任务详情',
          requiresAuth: true
        }
      },
      {
        path: 'images',
        name: 'ImageList',
        component: () => import('@/views/images/index.vue'),
        meta: {
          title: '图片管理',
          requiresAuth: true
        }
      },
      {
        path: 'resources',
        name: 'ResourceList',
        component: () => import('@/views/resources/index.vue'),
        meta: {
          title: '资源监控',
          requiresAuth: true
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 图片爬虫管理平台` : '图片爬虫管理平台'
  
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !token) {
    ElMessage.warning('请先登录')
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next({ path: '/' })
  } else {
    next()
  }
})

export default router

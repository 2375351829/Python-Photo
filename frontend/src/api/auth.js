import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export function register(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/user',
    method: 'get'
  })
}

export function updateUserInfo(data) {
  return request({
    url: '/auth/user',
    method: 'put',
    data
  })
}

export function changePassword(data) {
  return request({
    url: '/auth/password',
    method: 'put',
    data
  })
}

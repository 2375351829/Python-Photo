import request from '@/utils/request'

export function getTasks(params) {
  return request({
    url: '/tasks',
    method: 'get',
    params
  })
}

export function getTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'get'
  })
}

export function createTask(data) {
  return request({
    url: '/tasks',
    method: 'post',
    data
  })
}

export function updateTask(id, data) {
  return request({
    url: `/tasks/${id}`,
    method: 'put',
    data
  })
}

export function deleteTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'delete'
  })
}

export function executeTask(id) {
  return request({
    url: `/tasks/${id}/execute`,
    method: 'post'
  })
}

export function previewRules(data) {
  return request({
    url: '/tasks/preview',
    method: 'post',
    data
  })
}

export function smartExtract(data) {
  return request({
    url: '/tasks/smart-extract',
    method: 'post',
    data
  })
}

export function getTaskExecutions(id, params) {
  return request({
    url: `/tasks/${id}/executions`,
    method: 'get',
    params
  })
}

export function getTaskResults(id, params) {
  return request({
    url: `/tasks/${id}/results`,
    method: 'get',
    params
  })
}

export function stopTask(id) {
  return request({
    url: `/tasks/${id}/stop`,
    method: 'post'
  })
}

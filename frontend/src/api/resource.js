import request from '@/utils/request'

export function getResources(params) {
  return request({
    url: '/resources',
    method: 'get',
    params
  })
}

export function getResource(id) {
  return request({
    url: `/resources/${id}`,
    method: 'get'
  })
}

export function getResourceStats(params) {
  return request({
    url: '/resources/stats',
    method: 'get',
    params
  })
}

export function getResourceTypes() {
  return request({
    url: '/resources/types',
    method: 'get'
  })
}

export function getResourceDomains() {
  return request({
    url: '/resources/domains',
    method: 'get'
  })
}

export function filterResources(data, params) {
  return request({
    url: '/resources/filter',
    method: 'post',
    data,
    params
  })
}

export function replayRequest(data) {
  return request({
    url: '/resources/replay',
    method: 'post',
    data
  })
}

export function captureApiRequests(html) {
  return request({
    url: '/resources/capture-api',
    method: 'post',
    data: { html }
  })
}

export function deleteResource(id) {
  return request({
    url: `/resources/${id}`,
    method: 'delete'
  })
}

export function deleteTaskResources(taskId) {
  return request({
    url: `/resources/task/${taskId}`,
    method: 'delete'
  })
}

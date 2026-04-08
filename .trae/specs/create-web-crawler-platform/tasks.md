# Tasks

## Phase 1: 项目初始化与基础架构

- [x] Task 1: 创建项目目录结构
  - [x] SubTask 1.1: 创建后端目录结构 (backend/app, backend/tests, backend/scripts)
  - [x] SubTask 1.2: 创建前端目录结构 (frontend/src, frontend/public)
  - [x] SubTask 1.3: 创建文档目录 (docs/)
  - [x] SubTask 1.4: 创建配置文件 (.env.example, requirements.txt, package.json)

- [x] Task 2: 配置后端开发环境
  - [x] SubTask 2.1: 创建Python依赖文件 requirements.txt
  - [x] SubTask 2.2: 创建FastAPI应用入口 main.py
  - [x] SubTask 2.3: 配置CORS和中间件
  - [x] SubTask 2.4: 创建环境配置模块 config.py

- [x] Task 3: 配置前端开发环境
  - [x] SubTask 3.1: 初始化Vue 3项目 (使用Vite)
  - [x] SubTask 3.2: 安装Element Plus组件库
  - [x] SubTask 3.3: 配置Axios请求拦截器
  - [x] SubTask 3.4: 配置Vue Router路由

## Phase 2: 数据库设计与模型

- [x] Task 4: 设计并实现数据库模型
  - [x] SubTask 4.1: 创建用户模型 (User: id, username, email, password_hash, role, created_at)
  - [x] SubTask 4.2: 创建爬虫任务模型 (CrawlerTask: id, name, url, target_types, rules, schedule, status, debug_mode, user_id, created_at)
  - [x] SubTask 4.3: 创建任务执行日志模型 (TaskLog: id, task_id, status, start_time, end_time, error_message, debug_info)
  - [x] SubTask 4.4: 创建爬取结果模型 (CrawlResult: id, task_id, resource_type, data, file_path, created_at)
  - [x] SubTask 4.5: 创建资源拦截记录模型 (InterceptedResource: id, task_id, url, method, status_code, resource_type, size, duration, headers)
  - [x] SubTask 4.6: 创建调试报告模型 (DebugReport: id, task_id, request_logs, resource_stats, errors, warnings, created_at)
  - [x] SubTask 4.7: 创建数据库初始化脚本

- [x] Task 5: 实现数据库连接与迁移
  - [x] SubTask 5.1: 配置SQLAlchemy连接
  - [x] SubTask 5.2: 创建数据库会话管理
  - [x] SubTask 5.3: 实现Alembic迁移配置

## Phase 3: 用户认证模块

- [x] Task 6: 实现后端认证API
  - [x] SubTask 6.1: 创建用户注册接口 POST /api/auth/register
  - [x] SubTask 6.2: 创建用户登录接口 POST /api/auth/login
  - [x] SubTask 6.3: 实现JWT Token生成与验证
  - [x] SubTask 6.4: 创建用户信息接口 GET /api/auth/me
  - [x] SubTask 6.5: 实现密码加密 (bcrypt)

- [x] Task 7: 实现前端认证功能
  - [x] SubTask 7.1: 创建登录页面组件
  - [x] SubTask 7.2: 创建注册页面组件
  - [x] SubTask 7.3: 实现Token存储与管理 (localStorage)
  - [x] SubTask 7.4: 实现路由守卫
  - [x] SubTask 7.5: 创建用户状态管理 (Pinia)

## Phase 4: 爬虫任务管理模块

- [x] Task 8: 实现后端任务管理API
  - [x] SubTask 8.1: 创建任务列表接口 GET /api/tasks
  - [x] SubTask 8.2: 创建任务详情接口 GET /api/tasks/{id}
  - [x] SubTask 8.3: 创建新建任务接口 POST /api/tasks
  - [x] SubTask 8.4: 创建更新任务接口 PUT /api/tasks/{id}
  - [x] SubTask 8.5: 创建删除任务接口 DELETE /api/tasks/{id}
  - [x] SubTask 8.6: 实现URL验证功能

- [x] Task 9: 实现前端任务管理界面
  - [x] SubTask 9.1: 创建任务列表页面
  - [x] SubTask 9.2: 创建任务创建/编辑表单
  - [x] SubTask 9.3: 实现任务配置面板（URL、规则、频率）
  - [x] SubTask 9.4: 实现任务删除确认对话框

## Phase 5: 联网智能识别模块

- [x] Task 10: 实现爬虫核心引擎
  - [x] SubTask 10.1: 创建爬虫基础类 (BaseCrawler)
  - [x] SubTask 10.2: 实现HTTP请求封装 (requests/aiohttp)
  - [x] SubTask 10.3: 实现HTML解析器 (BeautifulSoup)
  - [x] SubTask 10.4: 实现CSS选择器提取
  - [x] SubTask 10.5: 实现XPath提取
  - [x] SubTask 10.6: 实现正则表达式提取

- [x] Task 11: 实现智能识别功能
  - [x] SubTask 11.1: 实现自动内容区域识别
  - [x] SubTask 11.2: 实现标题自动提取
  - [x] SubTask 11.3: 实现正文自动提取
  - [x] SubTask 11.4: 实现图片链接提取
  - [x] SubTask 11.5: 创建规则预览接口 POST /api/tasks/preview

- [x] Task 12: 实现前端规则配置界面
  - [x] SubTask 12.1: 创建规则配置表单
  - [x] SubTask 12.2: 实现规则预览功能
  - [x] SubTask 12.3: 创建数据清洗配置面板

## Phase 5.5: 爬取目标类型选择模块

- [x] Task 12.5: 实现爬取目标类型选择功能
  - [x] SubTask 12.5.1: 创建目标类型选择组件（图片、视频、文本、链接、文件）
  - [x] SubTask 12.5.2: 实现图片资源识别器（img标签、背景图片、srcset）
  - [x] SubTask 12.5.3: 实现视频资源识别器（video标签、视频链接、iframe嵌入）
  - [x] SubTask 12.5.4: 实现文本内容提取器（正文、段落、标题）
  - [x] SubTask 12.5.5: 实现链接资源提取器（内部链接、外部链接、锚文本）
  - [x] SubTask 12.5.6: 实现文件资源识别器（下载链接、文件类型检测）

- [x] Task 12.6: 实现资源过滤配置
  - [x] SubTask 12.6.1: 创建图片格式过滤配置（jpg, png, gif, webp等）
  - [x] SubTask 12.6.2: 创建图片尺寸过滤配置（最小宽度、最小高度）
  - [x] SubTask 12.6.3: 创建视频格式过滤配置（mp4, webm, avi等）
  - [x] SubTask 12.6.4: 创建文件类型过滤配置（pdf, doc, zip等）
  - [x] SubTask 12.6.5: 创建文件大小限制配置

## Phase 5.6: 服务资源识别与拦截模块

- [x] Task 12.7: 实现HTTP请求拦截器
  - [x] SubTask 12.7.1: 创建请求拦截中间件
  - [x] SubTask 12.7.2: 实现请求信息记录（URL、方法、头部、参数）
  - [x] SubTask 12.7.3: 实现响应信息记录（状态码、头部、大小、时间）
  - [x] SubTask 12.7.4: 创建资源类型自动识别（HTML、CSS、JS、图片、API等）

- [x] Task 12.8: 实现资源过滤功能
  - [x] SubTask 12.8.1: 创建URL模式过滤配置（正则表达式）
  - [x] SubTask 12.8.2: 创建资源类型过滤配置
  - [x] SubTask 12.8.3: 创建域名过滤配置（黑名单/白名单）
  - [x] SubTask 12.8.4: 实现API请求捕获（XHR/Fetch）
  - [x] SubTask 12.8.5: 创建API请求重放功能

- [x] Task 12.9: 实现前端资源监控界面
  - [x] SubTask 12.9.1: 创建资源拦截列表页面
  - [x] SubTask 12.9.2: 创建资源详情查看弹窗
  - [x] SubTask 12.9.3: 创建资源统计图表（按类型、域名分布）
  - [x] SubTask 12.9.4: 创建资源过滤配置面板

## Phase 5.7: 调试模式模块

- [x] Task 12.10: 实现调试模式核心功能
  - [x] SubTask 12.10.1: 创建调试模式开关配置
  - [x] SubTask 12.10.2: 实现详细日志输出（请求、响应、匹配结果）
  - [x] SubTask 12.10.3: 实现断点设置功能
  - [x] SubTask 12.10.4: 实现单步执行功能
  - [x] SubTask 12.10.5: 创建变量状态查看功能

- [x] Task 12.11: 实现调试报告生成
  - [x] SubTask 12.11.1: 创建请求响应记录汇总
  - [x] SubTask 12.11.2: 创建资源加载统计报告
  - [x] SubTask 12.11.3: 创建错误和警告汇总
  - [x] SubTask 12.11.4: 创建调试报告导出功能（JSON格式）

- [x] Task 12.12: 实现前端调试界面
  - [x] SubTask 12.12.1: 创建调试模式开关组件
  - [x] SubTask 12.12.2: 创建实时日志输出面板
  - [x] SubTask 12.12.3: 创建断点设置界面
  - [x] SubTask 12.12.4: 创建调试报告查看页面

## Phase 6: 任务调度系统

- [x] Task 13: 配置Celery任务队列
  - [x] SubTask 13.1: 配置Celery与Redis连接
  - [x] SubTask 13.2: 创建Celery Worker配置
  - [x] SubTask 13.3: 实现任务队列管理

- [x] Task 14: 实现任务调度功能
  - [x] SubTask 14.1: 创建定时任务调度器 (Celery Beat)
  - [x] SubTask 14.2: 实现Cron表达式解析
  - [x] SubTask 14.3: 创建手动触发接口 POST /api/tasks/{id}/execute
  - [x] SubTask 14.4: 实现并发控制逻辑
  - [x] SubTask 14.5: 实现任务状态更新

- [x] Task 15: 实现前端调度管理界面
  - [x] SubTask 15.1: 创建调度配置表单
  - [x] SubTask 15.2: 实现立即执行按钮
  - [x] SubTask 15.3: 实现任务状态实时显示

## Phase 7: 结果展示与导出模块

- [x] Task 16: 实现后端结果API
  - [x] SubTask 16.1: 创建结果列表接口 GET /api/results
  - [x] SubTask 16.2: 创建结果详情接口 GET /api/results/{id}
  - [x] SubTask 16.3: 创建CSV导出接口 GET /api/results/export/csv
  - [x] SubTask 16.4: 创建JSON导出接口 GET /api/results/export/json
  - [x] SubTask 16.5: 实现分页和筛选功能

- [x] Task 17: 实现前端结果展示界面
  - [x] SubTask 17.1: 创建结果列表页面
  - [x] SubTask 17.2: 创建结果详情弹窗
  - [x] SubTask 17.3: 实现数据筛选和搜索
  - [x] SubTask 17.4: 实现导出按钮和格式选择

- [x] Task 18: 实现数据可视化
  - [x] SubTask 18.1: 集成ECharts图表库
  - [x] SubTask 18.2: 创建任务执行趋势图
  - [x] SubTask 18.3: 创建数据量统计图
  - [x] SubTask 18.4: 创建仪表盘页面

## Phase 7.5: JSON自动解析与智能表格展示模块

- [x] Task 18.5: 实现JSON自动检测与解析
  - [x] SubTask 18.5.1: 创建JSON格式自动检测器
  - [x] SubTask 18.5.2: 实现JSON结构解析器（对象、数组、嵌套结构）
  - [x] SubTask 18.5.3: 实现字段路径和类型信息记录
  - [x] SubTask 18.5.4: 创建JSON结构树生成器

- [x] Task 18.6: 实现JSON结构分析
  - [x] SubTask 18.6.1: 实现字段名称自动识别
  - [x] SubTask 18.6.2: 实现字段数据类型推断（字符串、数字、布尔、日期、嵌套对象）
  - [x] SubTask 18.6.3: 实现字段出现频率统计
  - [x] SubTask 18.6.4: 创建JSON结构分析API GET /api/json/analyze

- [x] Task 18.7: 实现智能表格生成
  - [x] SubTask 18.7.1: 创建键名转换器（驼峰转空格、下划线转空格）
  - [x] SubTask 18.7.2: 实现中英文列名映射配置
  - [x] SubTask 18.7.3: 实现嵌套对象展开/折叠处理
  - [x] SubTask 18.7.4: 创建智能表格生成API POST /api/json/table

- [x] Task 18.8: 实现网页内容匹配
  - [x] SubTask 18.8.1: 创建JSON字段与网页元素匹配算法
  - [x] SubTask 18.8.2: 实现数据来源高亮显示
  - [x] SubTask 18.8.3: 创建字段映射配置接口
  - [x] SubTask 18.8.4: 实现映射规则保存与加载

- [x] Task 18.9: 实现数据翻译与格式化
  - [x] SubTask 18.9.1: 创建字段值翻译配置（状态码转文字）
  - [x] SubTask 18.9.2: 实现日期格式化显示
  - [x] SubTask 18.9.3: 实现数字格式化（千分位、小数位）
  - [x] SubTask 18.9.4: 实现布尔值转"是/否"显示

- [x] Task 18.10: 实现前端JSON表格组件
  - [x] SubTask 18.10.1: 创建智能表格组件（支持列排序、筛选、调整）
  - [x] SubTask 18.10.2: 创建嵌套数据展开/折叠组件
  - [x] SubTask 18.10.3: 创建JSON结构树视图组件
  - [x] SubTask 18.10.4: 创建JSON预览组件（语法高亮）
  - [x] SubTask 18.10.5: 创建列名映射配置界面
  - [x] SubTask 18.10.6: 创建数据翻译配置界面

## Phase 8: 错误处理与监控

- [x] Task 19: 实现错误处理机制
  - [x] SubTask 19.1: 创建全局异常处理器
  - [x] SubTask 19.2: 实现爬虫重试逻辑
  - [x] SubTask 19.3: 创建错误日志记录
  - [x] SubTask 19.4: 实现失败通知功能

- [x] Task 20: 实现日志系统
  - [x] SubTask 20.1: 配置Python logging
  - [x] SubTask 20.2: 创建日志API GET /api/logs
  - [x] SubTask 20.3: 实现前端日志查看界面
  - [x] SubTask 20.4: 实现日志级别过滤

- [x] Task 21: 实现实时状态推送
  - [x] SubTask 21.1: 配置WebSocket连接
  - [x] SubTask 21.2: 实现任务状态推送
  - [x] SubTask 21.3: 前端WebSocket集成

## Phase 9: 性能优化

- [x] Task 22: 实现请求频率控制
  - [x] SubTask 22.1: 创建请求延迟配置
  - [x] SubTask 22.2: 实现robots.txt解析
  - [x] SubTask 22.3: 创建速率限制中间件

- [x] Task 23: 实现资源管理
  - [x] SubTask 23.1: 实现内存使用监控
  - [x] SubTask 23.2: 实现断点续爬功能
  - [x] SubTask 23.3: 优化数据库查询

## Phase 10: 文档与部署

- [x] Task 24: 编写项目文档
  - [x] SubTask 24.1: 编写数据库设计文档
  - [x] SubTask 24.2: 编写API接口文档 (自动生成Swagger)
  - [x] SubTask 24.3: 编写部署指南
  - [x] SubTask 24.4: 编写使用说明

- [x] Task 25: 创建部署配置
  - [x] SubTask 25.1: 创建Dockerfile
  - [x] SubTask 25.2: 创建docker-compose.yml
  - [x] SubTask 25.3: 创建启动脚本

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 2
- Task 5 depends on Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 3, Task 6
- Task 8 depends on Task 5
- Task 9 depends on Task 3, Task 8
- Task 10 depends on Task 2
- Task 11 depends on Task 10
- Task 12 depends on Task 9, Task 11
- Task 12.5 depends on Task 10, Task 9
- Task 12.6 depends on Task 12.5
- Task 12.7 depends on Task 10
- Task 12.8 depends on Task 12.7
- Task 12.9 depends on Task 3, Task 12.7
- Task 12.10 depends on Task 10, Task 12.7
- Task 12.11 depends on Task 12.10
- Task 12.12 depends on Task 3, Task 12.10
- Task 13 depends on Task 2
- Task 14 depends on Task 10, Task 13
- Task 15 depends on Task 9, Task 14
- Task 16 depends on Task 5
- Task 17 depends on Task 3, Task 16
- Task 18 depends on Task 17
- Task 18.5 depends on Task 10
- Task 18.6 depends on Task 18.5
- Task 18.7 depends on Task 18.6
- Task 18.8 depends on Task 18.5, Task 11
- Task 18.9 depends on Task 18.7
- Task 18.10 depends on Task 3, Task 18.7, Task 18.9
- Task 19 depends on Task 10
- Task 20 depends on Task 2
- Task 21 depends on Task 2
- Task 22 depends on Task 10
- Task 23 depends on Task 10
- Task 24 depends on Task 1-23
- Task 25 depends on Task 24

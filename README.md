# CI管理平台 产品文档

> 版本：v3.0.0 | 更新日期：2026-04-25

## 一、产品概述

CI管理平台是一个面向CI（持续集成）测试团队的管理系统，提供测试执行监控、失败用例分析、历史归档追踪、工程配置管理和权限控制等功能。

### 技术架构

| 层级 | 技术栈 |
|------|--------|
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts + Pinia |
| 后端 | FastAPI + SQLAlchemy + APScheduler + SQLite |
| 数据库 | SQLite 双库设计（主库 + 归档库） |

### 核心价值

- **实时监控**：自动接收CI上报数据，实时展示工程运行状态
- **高效分析**：内联编辑、一键标记、自动关联，加速失败用例的根因定位
- **历史追踪**：自动归档失败用例，支持连续失败天数追踪和概率失败标记
- **灵活配置**：CSV批量导入/导出、产品版本级别保留天数配置
- **权限管控**：游客可浏览、操作需登录、管理功能需管理员权限

---

## 二、功能模块

### 2.1 仪表盘

| 功能 | 说明 |
|------|------|
| 统计卡片 | 总工程数、失败工程数、失败用例数、平均分析进展 |
| 失败率分布图 | 饼图展示平均失败率 vs 通过率 |
| 分析进展趋势图 | 折线图展示近5天的分析进展趋势 |

### 2.2 工程列表

| 功能 | 说明 |
|------|------|
| 统一查询 | 合并工程表和工程配置表数据，统一展示 |
| 多维筛选 | 按特性、状态（成功/失败/Lost）、工程名、责任人、PL筛选 |
| 内联编辑 | 点击即可编辑失败原因、责任人、PL，失焦或回车保存 |
| 新增工程 | 弹窗输入工程名、PL、责任人 |
| 删除工程 | 确认后同时删除工程表和工程配置表中的记录 |
| 工程详情跳转 | 点击工程名进入用例分析页面 |
| 分页 | 支持10/20/50条/页 |

### 2.3 工程详情（失败用例分析）

| 功能 | 说明 |
|------|------|
| 工程概览 | 状态、责任人、PL、总用例、失败用例、失败率、分析进展 |
| 用例列表 | 展示用例名、进展状态、根因分析、推送时间、责任人、源码问题、DTS单号 |
| 进展状态切换 | 点击状态标签直接切换（已完成/待分析） |
| 根因内联编辑 | 点击编辑根因，填写后自动标记为"已完成" |
| 责任人内联编辑 | 点击编辑责任人 |
| DTS单号 | 仅源码问题时可编辑，自动生成DTS链接 |
| 编辑弹窗 | 完整编辑用例的所有字段 |
| 多维筛选 | 按用例名、进展状态、责任人筛选 |

### 2.4 工程配置

| 功能 | 说明 |
|------|------|
| 统一查询 | 使用与工程列表相同的统一接口 |
| 新增配置 | 输入工程名、PL、责任人 |
| CSV批量导入 | 上传CSV文件批量导入工程配置（表头：工程,PL,责任人） |
| CSV导出 | 导出当前产品版本的工程配置为CSV文件 |
| 内联编辑 | 点击即可编辑PL、责任人 |
| 删除配置 | 确认后同时删除工程配置表和工程表中的记录 |

### 2.5 历史归档

| 功能 | 说明 |
|------|------|
| 页签切换 | 失败归档 / 概率失败 |
| 多维筛选 | 按特性、工程名、用例名、PL、分析状态、连续成功天数范围筛选 |
| 统计卡片 | 总归档记录、平均连续失败天数、未分析数 |
| 保留天数配置 | 产品版本级别的已修复用例保留天数（仅管理员可编辑） |
| 分析状态切换 | 点击状态标签直接切换（已分析/未分析） |
| 概率失败标记 | 复选框直接标记/取消概率失败 |
| 人工清理 | 清理已分析且连续成功天数 >= 保留天数的归档记录（需清理权限） |
| 执行历史 | 查看某用例的历史执行记录（日期、工程、状态、失败原因） |

### 2.6 权限管理（仅管理员可见）

| 功能 | 说明 |
|------|------|
| 新增用户 | 输入用户名创建 |
| 清理权限开关 | 管理员可切换用户的清理权限 |
| 删除用户 | 不能删除管理员自身 |
| 删除所有用户 | 仅管理员可操作，删除后自动登出 |
| 数据库备份 | 物理备份SQLite数据库文件 |
| 导出版本数据 | 导出指定产品版本的所有数据为JSON |

---

## 三、权限体系

### 3.1 用户角色

| 角色 | 说明 | 典型操作 |
|------|------|----------|
| 游客 | 未登录用户，可直接浏览所有页面 | 查看工程列表、归档数据、仪表盘 |
| 普通用户 | 已登录非管理员 | 编辑工程/用例数据、填写根因分析 |
| 清理权限用户 | 拥有归档清理权限 | 普通用户权限 + 人工清理归档 |
| 管理员 | 系统管理员 | 全部权限：用户管理、编辑保留天数、数据库备份、导出数据 |

### 3.2 权限控制机制

| 场景 | 行为 |
|------|------|
| 游客浏览页面 | 正常展示，无需登录 |
| 游客操作需权限的功能 | 弹出登录对话框，输入管理员账号登录后继续操作 |
| 非管理员访问权限管理 | 菜单不可见，URL直接访问被重定向到仪表盘 |
| 非管理员编辑保留天数 | 保留天数为只读，无编辑图标 |
| 非清理权限用户点击人工清理 | 按钮禁用 |

### 3.3 鉴权方式

- 无密码鉴权：仅需用户名即可登录/注册
- Token机制：Bearer Token，24小时过期
- 首个用户自动成为管理员

---

## 四、数据模型

### 4.1 主库（ci.db）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| projects | 工程表 | product_name, version, project_name, status, owner, pl, failure_reason, 统计字段 |
| test_cases | 测试用例表 | project_id(FK), test_name, status, is_analyzed, failure_reason, owner, pl, dts_ticket |
| users | 用户表 | username, is_admin, can_cleanup |
| features | 特性表 | product_name, version, feature_name |
| project_feature_mappings | 工程-特性映射表 | project_id, feature_id |
| project_configs | 工程配置表 | product_name, version, project_name, pl, owner |
| product_version_configs | 产品版本配置表 | product_name, version, retention_days |

### 4.2 归档库（ci_archive.db）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| archived_failures | 归档失败记录 | product_name, version, project_name, test_name, consecutive_days, consecutive_success_days, is_analyzed, is_probabilistic |
| test_case_execution_history | 用例执行历史 | execution_date, status, failure_reason |

### 4.3 双表同步机制

Project表（CI运行时数据）和ProjectConfig表（人工配置数据）通过以下规则保持同步：

- 创建任一表记录时，自动在对方表创建/更新对应记录
- 更新owner/pl时同步更新两表
- 删除时同步删除两表记录
- 查询时通过统一接口合并两表数据，owner/pl优先取Project的值

---

## 五、定时任务

| 任务 | 执行时间 | 功能 |
|------|----------|------|
| 归档任务 | 每天凌晨 2:50 | 将昨天的失败用例归档到归档库，计算连续失败天数 |
| 状态重置 | 每天凌晨 3:00 | 将所有工程状态重置为"lost"，等待当天CI重新上报 |

---

## 六、CI上报接口

### 上报方式

| 方式 | 说明 |
|------|------|
| log_url（推荐） | 提供日志ZIP下载URL，后端自动下载解压并解析result_*.xml |
| test_name（兼容） | 直接提供单个用例名和状态 |
| 同时提供 | 优先使用XML中的所有用例，忽略test_name |

### 上报参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| test_project_name | string | 是 | 工程名 |
| version | string | 是 | 版本（格式："产品名 版本号"） |
| test_name | string | 否 | 用例名（兼容旧版） |
| group_id | string | 是 | 组ID |
| project_id | string | 是 | 项目ID |
| record_id | string | 是 | 记录ID |
| subrecord_id | string | 是 | 子记录ID |
| status | string | 否 | 状态 |
| timestamp | datetime | 否 | 时间戳 |
| log_url | string | 否 | 日志ZIP下载URL |

---

## 七、API接口清单

### 工程管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /unified-projects | 统一工程查询（合并两表） |
| GET | /products | 获取产品版本列表 |
| GET | /products/{name}/versions/{ver}/summary | 仪表盘汇总 |
| GET | /products/{name}/versions/{ver}/projects | 工程列表 |
| GET | /projects/{id} | 工程详情 |
| POST | /projects | 创建工程 |
| PATCH | /projects/{id} | 更新工程 |
| DELETE | /projects/{id} | 删除工程 |

### 测试用例

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /test-cases | 用例列表 |
| PATCH | /test-cases/{id} | 更新用例 |
| POST | /test-cases/analyze | 分析用例 |

### 归档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /archive/failures | 归档失败列表 |
| GET | /archive/probabilistic-failures | 概率失败列表 |
| PATCH | /archive/failures/{id} | 更新归档记录 |
| DELETE | /archive/failures/cleanup | 人工清理归档 |
| GET | /archive/execution-history | 用例执行历史 |

### 工程配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /project-configs | 工程配置列表 |
| POST | /project-configs | 创建工程配置 |
| PATCH | /project-configs/{id} | 更新工程配置 |
| DELETE | /project-configs/{id} | 删除工程配置 |
| POST | /project-configs/upload | CSV批量导入 |
| GET | /project-configs/download | CSV导出 |

### 产品版本配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /product-version-config | 获取保留天数配置 |
| PATCH | /product-version-config | 更新保留天数配置 |

### 特性管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /features | 特性列表 |
| POST | /features | 创建特性 |
| PATCH | /features/{id} | 更新特性 |
| DELETE | /features/{id} | 删除特性 |
| POST | /features/bind | 绑定工程到特性 |
| POST | /features/unbind | 解绑工程与特性 |
| GET | /features/projects/{id} | 获取特性下的工程 |

### 认证与用户

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 用户登录 |
| POST | /auth/logout | 用户登出 |
| POST | /auth/register | 用户注册 |
| GET | /auth/check | 检查是否需要初始化 |
| GET | /auth/me | 获取当前用户信息 |
| GET | /auth/users | 用户列表 |
| POST | /auth/users | 创建用户 |
| PATCH | /auth/users/{id} | 更新用户权限 |
| DELETE | /auth/users/{id} | 删除用户 |
| DELETE | /auth/users | 删除所有用户 |

### 备份与管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /backup/info | 获取备份信息 |
| POST | /backup/export | 导出版本数据 |
| POST | /backup/db-backup | 物理备份数据库 |
| POST | /admin/trigger-archive | 手动触发归档任务 |

### CI上报

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /reports | CI测试结果上报 |

---

## 八、业务流程

### 8.1 日常CI流程

```
CI系统执行测试
  → POST /reports 上报测试结果
  → 后端解析XML，创建/更新工程和用例
  → 重新计算工程统计（失败率、分析进展）
  → 前端实时展示最新状态
```

### 8.2 失败分析流程

```
工程师查看工程列表（按失败状态筛选）
  → 进入工程详情，查看失败用例
  → 点击进展状态标签切换为"已完成"
  → 或填写根因分析（自动标记已完成）
  → 或通过编辑弹窗完整编辑
  → 分析进展百分比自动更新
```

### 8.3 归档清理流程

```
每日凌晨2:50 自动归档昨天的失败用例
  → 计算连续失败天数和连续成功天数
  → 写入归档库

管理员/清理权限用户手动清理
  → 读取产品版本的保留天数配置
  → 清理条件：已分析 且 连续成功天数 >= 保留天数
  → 删除匹配的归档记录
```

### 8.4 权限操作流程

```
游客浏览页面（无需登录）
  → 操作需权限的功能（如编辑保留天数）
  → 后端返回401
  → 弹出登录对话框
  → 输入管理员账号登录
  → 操作自动完成
```

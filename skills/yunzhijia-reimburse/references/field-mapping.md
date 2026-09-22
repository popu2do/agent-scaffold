# 云之家报销审批单明细组件 (DetailField) 字段映射规范

云之家（Kingdee CloudFlow）日常费用报销审批单明细表使用 Vue 2 组件 `DetailField` 维护，其核心数据存储于 `v.values` 响应式数组中。

## 核心字段对照表

| 字段编码 | 控件类型 (type) | 业务名称 | 数据结构示例 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `Da_0` | `dateWidget` | 发生日期 | `1715731200000` | 毫秒时间戳（当日 00:00:00） |
| `iw_0` | `apiIntegrationWidget` | 费用类型 | `[{"id": "3", "name": "加班交通费", "number": "08.01"}]` | 数组对象，需包含 id、name、number |
| `iw_1` | `apiIntegrationWidget` | 研发项目 | `[{"id": "52", "name": "PROJ-NAME", "number": "PROJ-CODE"}]` | 项目主数据，优先从已有行继承 |
| `iw_2` | `apiIntegrationWidget` | 费用承担部门 | `[{"id": "2", "name": "部门名称", "number": "002"}]` | 部门主数据，优先从已有行继承 |
| `Te_4` | `textWidget` | 事由 | `"加班打车费"` | 纯字符串，字数受表单规则限制 |
| `Mo_1` | `moneyWidget` | 专票税额(元) | `""` 或 `"12.34"` | 普票留空字符串 |
| `Mo_2` | `moneyWidget` | 预留金额列 | `""` | 默认空字符串 |
| `Mo_0` | `moneyWidget` | 金额 | `"35.50"` | 必填，金额字符串格式 |
| `Rd_0` | `relatedWidget` | 自采验收流程/关联单据 | `[]` 或关联对象数组 | 无关联时传空数组 |
| `Ta_1` | `textAreaWidget` | 备注说明 | `""` 或 `"备注信息"` | 可选字符串 |
| `_id_` | 内部键 | 行唯一标识 | `"1052568234"` | 随机生成数字字符串 |
| `extendDataMap` | 内部映射 | 扩展数据 | `{}` | 默认空对象 |

## 联动触发方法

注入新行至 `v.values` 之后，必须依次调用以下方法使表单完成响应式更新：
1. `v.triggerValueChangeEvent(v.values)`：触发组件的变更事件，通知外层表单重新收集字段值。
2. `v.calcArithmetic()`：驱动金额小计、表单级金额合计（`#Ac_0`）与中文大写总额重新计算。
3. `v.closePanel()`：关闭可能因触发新增而自动弹出的右侧明细编辑抽屉。

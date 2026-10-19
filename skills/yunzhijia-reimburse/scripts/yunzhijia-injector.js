/**
 * 云之家日常报销表单底层数据注入引擎 (完全脱敏版)
 *
 * 兼容模式:
 * 1. OpenCLI (browser exec / eval)
 * 2. 浏览器开发者工具控制台 (F12 Console)
 *
 * @param {Array<Object>} newItems - 待注入明细列表 [{ date: 'YYYY-MM-DD', amount: '12.34', typeObj: { id, name, number }, reason?: string, project?: Object, dept?: Object }]
 * @param {Object} [fallbackConfig] - 可选的默认配置 { defaultProject: { id, name, number }, defaultDepartment: { id, name, number } }
 * @returns {Object} 结构化执行报告
 */
(function runYunzhijiaInjector(newItems, fallbackConfig) {
  // 1. 定位云之家审批表单所在 Document (支持多层 Iframe 嵌套结构)
  let targetDoc = document;
  const iframes = Array.from(document.querySelectorAll('iframe'));
  for (const f of iframes) {
    try {
      if (f.contentDocument && f.contentDocument.querySelector('#Dd_0')) {
        targetDoc = f.contentDocument;
        break;
      }
    } catch (e) {
      // 跨域 iframe 安全保护
    }
  }

  const dd = targetDoc.querySelector('#Dd_0');
  if (!dd || !dd.__vue__) {
    return {
      success: false,
      error: 'NOT_FOUND_OR_NOT_READY',
      message: '未找到报销明细表容器 (#Dd_0) 或 Vue 实例。请确保当前处于云之家报销单页面。'
    };
  }

  const v = dd.__vue__;
  if (!Array.isArray(v.values)) {
    return {
      success: false,
      error: 'INVALID_VUE_MODEL',
      message: 'Vue 组件内部 values 数据结构异常'
    };
  }

  // 2. 动态上下文继承策略
  // 若表格已有行，自动从首行/已有行继承项目与部门信息，实现零硬编码归属对齐
  let inheritedProj = fallbackConfig?.defaultProject || null;
  let inheritedDept = fallbackConfig?.defaultDepartment || null;

  if (v.values.length > 0) {
    const sampleRow = v.values[0];
    if (Array.isArray(sampleRow.iw_1) && sampleRow.iw_1.length > 0) {
      inheritedProj = sampleRow.iw_1[0];
    }
    if (Array.isArray(sampleRow.iw_2) && sampleRow.iw_2.length > 0) {
      inheritedDept = sampleRow.iw_2[0];
    }
  }

  if (!inheritedProj || !inheritedDept) {
    return {
      success: false,
      error: 'MISSING_PROJECT_OR_DEPT',
      message: '未获取到项目或部门信息：报销单当前为空且未提供默认配置。请先在报销单中录入第一行或在配置中指定。'
    };
  }

  // 3. 批量生成并追加明细行
  // 费用类型主数据只能来自调用方或配置，脚本不提供任何内置默认值。先整体校验再写入，
  // 避免中途遇到不完整条目时留下只追加了一半的表单。
  const items = Array.isArray(newItems) ? newItems : [];
  if (!items.length) {
    return {
      success: false,
      error: 'EMPTY_PAYLOAD',
      message: '载荷为空：请传入待注入明细数组，每项包含 date、amount 与 typeObj { id, name, number }。'
    };
  }
  const missingTypeAt = items.findIndex((item) => !item || !item.typeObj || !item.typeObj.id || !item.typeObj.number);
  if (missingTypeAt >= 0) {
    return {
      success: false,
      error: 'MISSING_EXPENSE_TYPE',
      message: `明细项第 ${missingTypeAt + 1} 条缺少费用类型主数据：请为每一项传入 typeObj { id, name, number }，或在生成载荷前按配置补齐。`
    };
  }

  for (const item of items) {
    const typeObj = item.typeObj;
    const dateMs = item.date ? new Date(item.date + ' 00:00:00').getTime() : Date.now();
    const projObj = item.project || inheritedProj;
    const deptObj = item.dept || inheritedDept;

    const row = {
      Da_0: dateMs,
      Mo_0: String(item.amount || '0'),
      Mo_1: item.tax || '',
      Mo_2: '',
      Rd_0: item.relatedFlows || [],
      Ta_1: item.remark || '',
      Te_4: item.reason || '',
      _id_: String(Math.floor(Math.random() * 1e9 + 1e9)),
      extendDataMap: {},
      iw_0: [typeObj],
      iw_1: [projObj],
      iw_2: [deptObj]
    };
    v.values.push(row);
  }

  // 4. 触发响应式联动更新与重算
  if (typeof v.triggerValueChangeEvent === 'function') {
    v.triggerValueChangeEvent(v.values);
  }
  if (typeof v.calcArithmetic === 'function') {
    v.calcArithmetic();
  }
  if (typeof v.closePanel === 'function') {
    v.closePanel();
  }

  // 5. 生成执行结果摘要
  const ac0 = targetDoc.querySelector('#Ac_0');
  return {
    success: true,
    addedCount: items.length,
    totalRows: v.values.length,
    totalAmountSummary: ac0 ? ac0.innerText.trim() : null
  };
})(ITEMS_PAYLOAD, CONFIG_PAYLOAD);

# 测试编写模式

<test_structure>
**本项目只有两层测试**：
- ✅ **单元测试**：测试单个类/函数，完全Mock外部依赖
- ✅ **集成测试**：测试多个模块协作，Mock设备/文件系统
- ❌ **不包含E2E测试**：E2E需要真实设备和UI交互，无法在CI/CD中自动化

```
tests/
├── unit/              # 单元测试
│   └── test_*.py
└── integration/       # 集成测试
    └── test_*_integration.py
```
</test_structure>

<test_template>
```python
def test_功能描述_场景描述():
    """测试：[功能描述] - [场景描述]

    验收标准：[对应的验收标准编号]
    """
    # Arrange（准备）
    # 准备测试数据和环境

    # Act（执行）
    # 执行被测试的功能

    # Assert（断言）
    # 验证结果是否符合预期
```
</test_template>

<coverage_requirements>
- ✅ 功能点：每个功能点至少1个测试
- ✅ 边界条件：每个边界条件至少1个测试
- ✅ 异常场景：每个异常场景至少1个测试
- ✅ 测试命名：清晰描述测试目的
- ✅ 测试文档：每个测试包含 docstring
- ❌ 禁止编写E2E测试：不要创建 tests/e2e/ 目录或 *_e2e.py 文件
</coverage_requirements>

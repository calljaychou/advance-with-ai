# 06 TypeScript 与命名

## 1. 命名约定

| 对象 | 规则 | 示例 |
| --- | --- | --- |
| React 组件与组件目录 | PascalCase | `OrderTable.tsx`、`OrderEditModal/` |
| Hook | `use` 前缀 + camelCase | `useOrderList.ts` |
| 工具函数 | camelCase，动词描述行为 | `formatOrderAmount` |
| 常量 | 能表达语义的名称；真正不可变的模块级常量可用大写下划线 | `ORDER_STATUS_MAP`、`orderStatusOptions` |
| Props 类型 | `<ComponentName>Props` | `OrderTableProps` |
| styled-components 组件 | 体现组件语义 | `OrderTableContainer`，不用 `Wrapper1` |

## 2. 类型组织

- Props 类型优先放在组件同级 `types.ts`，或组件文件中。
- 页面级 Props、DTO 衍生类型、表单值、视图模型放页面 `types.ts`。
- 跨模块共享的类型放 `src/types/`。
- 仅作为类型使用的依赖**必须**通过 `import type` 引入。
- 禁止无必要地使用 `any`；接口响应、表单值、表格行和路由状态应定义明确类型。

## 3. 模块引用

- 跨目录引用优先使用 `@/` 别名（`@/` → `src/`）。
- 同目录内部文件使用相对路径。
- 不直接修改 OpenAPI 生成的 `src/api/generated/` 文件；需要新增接口时改后端注解后重新执行 `npm run openapi`。

## 4. 相关文档

- 目录职责：[01-工程与目录.md](01-工程与目录.md)
- 检查清单：[07-命令与检查清单.md](07-命令与检查清单.md)

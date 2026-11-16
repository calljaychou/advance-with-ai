# 管理后台开发文档

本文档适用于 `${PROJECT_NAME}-ui/vite-react-page` 管理后台 React 工程。为控制单文件体积与阅读成本，按主题拆分为以下分册，本页为入口与总索引。

## 分册索引

| 分册 | 内容 | 何时读 |
| --- | --- | --- |
| [01-工程与目录.md](01-工程与目录.md) | 技术栈、开发优先级、完整目录结构、各目录职责约束 | 首次进入工程、新增目录或不确定代码放哪时 |
| [02-独立页面与路由.md](02-独立页面与路由.md) | MultiPageAutoPlugin 构建入口、`routes.tsx` 本地调试路由、关联页面 SPA 组织 | 新增独立页面、页面打不开、路由不生效时 |
| [03-页面与组件设计.md](03-页面与组件设计.md) | 推荐页面结构、`App.tsx` 职责边界、组件单一职责、各文件职责 | 设计页面结构、拆分组件时 |
| [04-公共组件与Hook.md](04-公共组件与Hook.md) | 可复用公共组件清单、公共 Hook 清单、上提时机 | 写任何页面/组件前必查 |
| [05-样式规范.md](05-样式规范.md) | Tailwind / styled-components 优先级、样式文件拆分、Ant Design 覆盖 | 写样式时 |
| [06-TypeScript与命名.md](06-TypeScript与命名.md) | 命名约定、类型组织、`import type`、`@/` 别名、`any` 约束 | 定义类型或命名时 |
| [07-命令与检查清单.md](07-命令与检查清单.md) | 常用命令、包管理器、多端适配边界、提交前检查清单 | 执行命令、提交前 |

## 快速开始

```shell
cd ${PROJECT_NAME}-ui/vite-react-page
npm run dev        # 启动开发环境
npm run openapi    # 后端接口就绪后生成 SDK
```

详细命令见 [07-命令与检查清单.md](07-命令与检查清单.md)。

## 硬性底线（摘自各分册，不一致时以分册为准）

1. 生成文件 `src/api/generated/` 不得手动修改，只能通过 `npm run openapi` 重新生成。
2. 新增独立页面必须同时登记构建入口 `src/pages/<页面目录>/main.tsx` 与本地调试路由 `src/router/routes.tsx`，缺一不可。
3. 一个独立页面目录只保留一个 `main.tsx`，关联页面通过该页面的 `router` 组织为 SPA。
4. 一个组件文件只定义一个 React 组件。
5. 不同页面、不同组件的 styled-components 必须放入各自独立的样式文件。
6. 不做多媒体适配：不写 `@media`，不使用 `sm:` / `md:` / `lg:` / `xl:` / `2xl:` 等响应式断点前缀。
7. 开发新能力前必须依次检查 `src/components/`、`src/hooks/`、`src/utils/`、`src/types/`、`src/api/`，能复用不得重复实现。
8. 命令必须在 `${PROJECT_NAME}-ui/vite-react-page` 目录内执行，不得在仓库根目录或消费端工程执行。

## 与其他文档的关系

- 面向 AI Agent 的强制判定条件：[docs/rules/管理后台开发规则.md](../rules/管理后台开发规则.md)
- 前端两端通用约定：[docs/rules/前端通用约定.md](../rules/前端通用约定.md)
- 消费端文档：[docs/client/README.md](../client/README.md)

## 维护约定

- 新增主题：在 `docs/admin/` 下建 `NN-主题.md` 并在本页登记，编号递增。
- 修改规则：先改分册，再检查 `docs/rules/管理后台开发规则.md` 与根 `AGENTS.md` 是否需要同步，避免出现两套说法。
- 本页只放索引与底线，不放具体实现细节。

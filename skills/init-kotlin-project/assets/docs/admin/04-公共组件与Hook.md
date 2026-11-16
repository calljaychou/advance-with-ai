# 04 公共组件与 Hook

开发任何页面前必须检查 `src/components/` 与 `src/hooks/`。本文件只列清单与选型；使用时**必须直接阅读组件/Hook 的 Props 类型与当前实现**，不要根据名称猜测行为。

## 1. 公共组件 `src/components/`

已有公共组件能够满足需求时必须优先使用；存在少量通用差异时，优先为公共组件增加兼容配置，并确认不会破坏既有调用方。仅与单一业务强相关的组件保留在页面目录。

| 组件 | 主要职责 | 优先使用场景 |
| --- | --- | --- |
| `Action` | 为操作节点组合 Button 和 Popconfirm | 表格操作列中的按钮、二次确认操作 |
| `AsyncButton` | 自动维护异步点击操作的 loading 状态 | 提交、导出、同步等异步按钮 |
| `AutoActions` | 展示有限数量的操作项，并将超出项收纳到 Popover | 表格操作列按钮较多的场景 |
| `CustomModal` | 统一 Modal、Form 提交和确认 loading | 新增、编辑、确认类弹窗 |
| `DropFolderUpload` | 拖拽文件或文件夹、递归提取图片并上传 | 批量图片和文件夹图片上传 |
| `FormItem` | 表单字段组件集合 | 表单内的专用字段控件，见第 2 节 |
| `LazyLoad` / `createLazyLoad` | 为 React 懒加载组件提供统一 Suspense Loading | 路由懒加载和大型模块按需加载 |
| `Loading` | 统一页面或区域加载反馈 | Suspense fallback、页面加载占位 |
| `MapPickerModal` | 地图选点弹窗，在 `TencentMapPicker` 之上补省市区编码回填与必填校验 | 需要"选点 + 省市区"一起回填的场景 |
| `Search` | 通过配置生成查询表单，支持查询、重置和自定义字段 | 列表页筛选条件区域 |
| `Template` | 渲染嵌套路由的 `Outlet` | 需要纯路由分组的父级节点 |
| `TencentMapPicker` | 腾讯地图选点界面组件（共享选点交互） | 只需要坐标选点、由调用方自行处理业务转换 |
| `UploadImage` | 图片上传、大小校验和预览 | 单张或多张普通图片上传 |
| `UploadSorter` | 图片上传、预览、删除和拖拽排序 | 需要调整图片顺序的上传场景 |

### 2. FormItem 子组件

`src/components/FormItem/` 下按控件拆分为独立目录，新增表单字段前先确认能否复用：

| 子组件 | 职责 |
| --- | --- |
| `FormDesc` | 表单项的说明/描述文案 |
| `RegionCascaderField` | 省市区级联选择，值为 `RegionValue`（编码 + 名称快照），支持配置可选层级 |
| `SelectGoodsField` | 商品选择，内部复用 `CustomModal/SelectGoodsModal` |
| `SelectImgField` | 图片选择字段 |
| `WangEditorField` | 富文本编辑（WangEditor），配 `RichRender` 做安全渲染与图片上传 |

## 3. 公共 Hook `src/hooks/`

开发请求、列表、弹窗和事件逻辑前必须检查 `src/hooks/`。禁止在每个页面重复编写 loading、分页、请求取消、弹窗挂载和事件解绑等通用逻辑。

| Hook | 主要职责 | 优先使用场景 |
| --- | --- | --- |
| `useConfigurableEffect` | 控制首次执行、仅执行一次及消费路由 state 的 Effect | 需要跳过首次执行或读取一次性路由状态 |
| `useEventListener` | 注册并自动清理 Window、Document 或元素事件 | resize、scroll、keydown 等原生事件监听 |
| `useFetchList` | 管理列表请求、分页、搜索条件、loading 和列表更新 | 后台分页列表页 |
| `useModal` | 在统一 Provider 环境中挂载弹窗并返回 Promise 化打开方法 | 命令式打开新增、编辑、详情弹窗 |
| `useRequest` | 管理通用异步请求、loading、结果和取消请求 | 非列表接口请求或页面初始化请求 |
| `useSubEvent` / `dispatchSubEvents` | 提供带清理机制的跨组件事件订阅与派发 | 无直接父子 Props 链路的局部事件协作 |

## 4. 上提时机

页面私有 Hook 应放在对应页面的 `hooks/` 中。只有逻辑与具体业务无关、接口稳定且预计会被多个页面使用时，才上提到 `src/hooks/`。组件同理，见 [03-页面与组件设计.md](03-页面与组件设计.md) 第 5 节。

## 5. 修改公共能力的约束

- 公共组件新增通用能力后，必须保持既有 Props 的兼容性。
- 不得为单一页面需求修改公共组件的默认行为；如确需变更，先确认所有既有调用方。
- UI 基础能力优先使用 Ant Design，不重复封装功能相同的基础组件。

## 6. 相关文档

- 页面结构：[03-页面与组件设计.md](03-页面与组件设计.md)
- 样式组织：[05-样式规范.md](05-样式规范.md)

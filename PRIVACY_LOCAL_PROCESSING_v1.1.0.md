# MD Converter v1.1.0 — Privacy / Local Processing Statement

## 1. 产品声明（冻结定位）

产品 About 界面与安装包宣传语中的定位是本 RC 的权威声明：

```text
Turn Markdown into polished Word documents — locally, privately, and without a subscription.
Processing: Local, on this computer
Account required: No
Document upload: Not required for normal conversion
```

## 2. 正常转换的行为

- Markdown 解析、AST 处理、渲染与 DOCX 生成全部在**本机**完成。
- **不需要账号**，**不需要订阅**。
- **不上传文档**：正常转换路径不需要把文档内容发送到任何服务器。
- P12-09 的有界观测：产品进程在启动与一次真实转换期间**没有建立远程 TCP
  连接**（`Doc/V2/Implementation/P12-09/WP-P12-09-06_PRIVACY_LOCALITY_RELEASE_INTEGRITY.md`）。
  这是有界观测记录，不是渗透测试结论。

## 3. 本地留存的数据

| 数据 | 位置 | 说明 |
| --- | --- | --- |
| 输入 / 输出文档 | 用户选择的本地路径 | 完全由用户控制 |
| GUI 设置（记住的文件夹等） | 本机用户偏好（HKCU） | 仅本机，不含文档内容 |
| 安装的程序文件 | `%LOCALAPPDATA%\Programs\MD_Converter` | 卸载时移除 |

卸载**不会删除**用户文档；GUI 设置按设计保留（见
`INSTALLATION_GUIDE_v1.1.0.md` §6）。

## 4. 唯一的网络相关例外（可选路径）

仅当文档包含 **Mermaid** 图且使用方安装了 `[mermaid]` 可选依赖时，渲染需要从
pinned CDN 加载脚本（`https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`）。
此路径不涉及把文档上传到服务器；未安装该可选依赖时不使用这一路径。
Word COM（TOC 页码刷新）只调用本机已安装的 Microsoft Word。

## 5. 未引入的能力（RC 冻结边界）

本 RC **没有**遥测、账号系统、云上传、自动更新或后台联网服务。P12-10 未新增
任何产品语义或架构变更（见 `Doc/V2/Implementation/P12-10/P12-10_CLOSURE_EVIDENCE.md`）。

## 6. 许可与第三方

- 许可条款：`EULA.txt`（Proprietary Single-User License）。
- 第三方组件与许可证：`THIRD_PARTY_NOTICES.txt`。

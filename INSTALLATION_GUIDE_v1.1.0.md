# MD Converter v1.1.0 Installation Guide（Windows 安装包）

| 项目 | 值 |
| --- | --- |
| Release | v1.1.0（Release Candidate `MD Converter v1.1.0 RC1`） |
| 安装包 | `MD_Converter_v1.1.0_Setup.exe` |
| 安装包大小 | 51,109,717 bytes |
| 安装包 SHA-256 | `EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF` |
| 目标平台 | Windows 10 / 11（x64） |
| 安装范围 | 当前用户（`%LOCALAPPDATA%\Programs\MD_Converter`），无需管理员权限 |
| 是否需要 Python | **不需要**（安装包自带运行时） |

> 这是 **Windows 安装包**的安装指南。wheel/sdist 的 Python 安装方式见
> `INSTALLATION_GUIDE_v1.0.0.md`。

---

## 1. 前置条件

- Windows 10 / 11 x64。
- 无需管理员权限、无需 Python、无需网络。
- Microsoft Word 可选：安装 Word 时 TOC 页码可自动刷新；未安装 Word 时文档
  仍然生成，页码在 Word 中按 F9 刷新。

## 2. 校验安装包（推荐）

```powershell
Get-FileHash .\MD_Converter_v1.1.0_Setup.exe -Algorithm SHA256
```

结果应为：

```text
EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF
```

## 3. 安装

1. 双击 `MD_Converter_v1.1.0_Setup.exe`。
2. 首次运行若出现 SmartScreen 提示，选择 “更多信息 → 仍要运行”
   （安装包未代码签名，见 `KNOWN_ISSUES_v1.1.0.md` §6）。
3. 按向导完成安装；默认安装到
   `%LOCALAPPDATA%\Programs\MD_Converter`。
4. 从开始菜单启动 **MD Converter**。

静默安装（可选，供自动化使用）：

```powershell
Start-Process .\MD_Converter_v1.1.0_Setup.exe `
  -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait
```

## 4. 安装后的位置

| 项目 | 位置 |
| --- | --- |
| 程序 | `%LOCALAPPDATA%\Programs\MD_Converter\MD_Converter.exe` |
| 许可证 / 第三方声明 | 同上目录下的 `EULA.txt`、`THIRD_PARTY_NOTICES.txt` |
| 开始菜单 | `MD Converter`、`MD Converter - Input Folder`、`MD Converter - Output Folder`、`Uninstall MD Converter` |
| 卸载信息 | `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\MDConverter.Quansheng2022_is1` |

安装不会创建 Windows 服务、不会设置开机自启、不需要联网。

## 5. 基本使用

1. 启动 **MD Converter**。
2. 选择或拖入 `.md` 文件（Markdown 文件在本机转换）。
3. 选择输出文件夹（默认使用文档目录下的 `MD_Converter\output`）。
4. 点击 **Convert**；完成后可用 **Open Document** 直接打开生成的 `.docx`，
   用 **Open Folder** 打开输出目录。

## 6. 卸载

- 方式一：开始菜单 → `Uninstall MD Converter`。
- 方式二：Windows 设置 → 应用 → 已安装的应用 → `MD Converter 1.1.0` → 卸载。

静默卸载：

```powershell
& "$env:LOCALAPPDATA\Programs\MD_Converter\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

卸载行为（P12-08 / P12-09 已验证）：

```text
程序目录、卸载注册表项、开始菜单项被移除
用户文档（含已转换的 .docx）保留
GUI 设置（HKCU 偏好）保留
与本产品无关的文件不被删除
```

## 7. 故障排查

| 现象 | 处理 |
| --- | --- |
| SmartScreen 阻止运行 | “更多信息 → 仍要运行”（安装包未签名） |
| TOC 页码为未刷新状态 | 在 Word 中按 F9 刷新域 |
| 图形尺寸被缩放 | 见 `KNOWN_ISSUES_v1.1.0.md` §3（按有效内容区适配） |

## 8. 相关文件

```text
RELEASE_NOTES_v1.1.0.md                 发布说明
KNOWN_ISSUES_v1.1.0.md                  已知问题 / 已接受限制
PRIVACY_LOCAL_PROCESSING_v1.1.0.md      本地处理与隐私声明
EULA.txt                                最终用户许可协议
THIRD_PARTY_NOTICES.txt                 第三方组件声明
```

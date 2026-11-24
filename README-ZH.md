# Action tools - Github Action 巧用小脚本

[![License: AGPL-3.0](https://img.shields.io/github/license/lingyicute/action-tools?color=blue)](./LICENSE)
![Downloader](https://github.com/lingyicute/Action-tools/actions/workflows/downloader.yml/badge.svg)
![Payload Dump](https://github.com/lingyicute/Action-tools/actions/workflows/payload-dumper.yml/badge.svg)
![Tar.gz decompresser](https://github.com/lingyicute/Action-tools/actions/workflows/tar-gz-decompresser.yml/badge.svg)
![Tar.gz to Zip](https://github.com/lingyicute/Action-tools/actions/workflows/tar-gz-to-zip.yml/badge.svg)
![APKM to APK](https://github.com/lingyicute/Action-tools/actions/workflows/apkm.yml/badge.svg)
![System Test](https://github.com/lingyicute/Action-tools/actions/workflows/test-system.yml/badge.svg)

一个基于 GitHub Actions 的小工具集合 —— 从链接下载文件、解包 Android OTA 的 `payload.bin`、解压或转换 `.tar.gz` 压缩包、把 `.apkm` 合并成单个 APK、查看 Runner 环境信息。全部在浏览器里完成，本地无需安装任何东西。

**[中文]** · [English](./README.md)

## 特性

- 🚀 **零安装、零配置** —— 全部运行在 GitHub 官方 `ubuntu-latest` Runner 上
- 🔗 **粘贴链接即用** —— 输入下载链接，然后从 Release 或 Artifacts 取回结果
- ✂️ **大文件自动分割** —— Downloader 会把 ≥ 2GiB 的文件自动切成 2046MiB 的分片，绕开 GitHub 单文件大小限制
- 🤖 **全部手动触发** —— 不点 *Run workflow* 就不会消耗任何 Actions 时长

## 工具一览

| 工具 | 说明 | 输入 | 输出 |
| --- | --- | --- | --- |
| ⬇️ [Downloader 下载器](#️-downloader-下载器) | 下载任意直链文件并发布到 Release（≥ 2GiB 自动分割） | `LINK` | Release + Artifact |
| 📦 [Payload Dumper 解包](#-payload-dumper-解包) | 从 Android OTA `payload.bin` 中提取指定分区（支持 URL / zip） | `LINK`、`PART` | Artifact `imgs` |
| 🗜️ [Tar.gz Decompresser 解压](#️-targz-decompresser-解压) | 下载并解压 `.tar.gz`，把所有文件平铺到同一目录 | `LINK` | Release |
| 🔄 [Tar.gz to Zip 转换](#-targz-to-zip-转换) | 将 `.tar.gz` 压缩包转换为 `.zip`（移除符号链接） | `LINK` | Release `repacked.zip` |
| 📱 [APKM to APK 合并](#-apkm-to-apk-合并) | 把 `.apkm` 分包合并成单个 APK（可选 zipalign + 签名） | `apkm_url` 及选项 | Release `run-<run_number>` + Artifact |
| 💻 [System Test 系统测试](#-system-test-系统测试) | 打印 Actions Runner 的硬件 / 系统信息 | — | 运行日志 |

## 快速上手

1. **Fork** 本仓库（或使用你自己的副本）。
2. 打开仓库的 **Actions** 页面。
3. 在左侧边栏选择需要的工作流。
4. 点击 **Run workflow**，填写输入参数后确认运行。
5. 到 **Releases** 页面或该次运行的 **Artifacts** 中下载结果。

## 工具详情

### ⬇️ Downloader 下载器

用 `wget` 从任意直链下载文件，并发布为 GitHub Release（`downloader-<run_number>`），同时上传一份 Artifact（`Downloaded-File`）作为备份。

**≥ 2GiB** 的文件会自动按 **2046MiB** 分割，以绕开 GitHub 的单文件大小限制。

| 输入 | 说明 | 必填 |
| --- | --- | --- |
| `LINK` | 文件的直链地址 | ✅ |

> [!TIP]
> 如果文件被分割了，请下载**所有** `.part` 分片后在本地合并：
>
> ```bash
> # Linux / macOS
> cat down.part* > down
> ```
>
> ```bat
> rem Windows (cmd)
> copy /b down.part* down
> ```

### 📦 Payload Dumper 解包

使用 [5ec1cff/payload-dumper](https://github.com/5ec1cff/payload-dumper) 从 Android OTA 的 `payload.bin` 中提取分区。该分支支持直接从 **URL** 或 **zip 压缩包**流式解包，无需先下载整个 OTA 包 —— 特别适合提取 `boot`、`init_boot`、`vbmeta` 这类小分区。

| 输入 | 说明 | 必填 |
| --- | --- | --- |
| `LINK` | `payload.bin` 的地址，或包含它的 OTA zip 地址 | ✅ |
| `PART` | 要提取的分区名，逗号分隔（如 `boot,vendor`） | ✅ |

提取出的 `.img` 文件会作为 Artifact **`imgs`** 上传。

> [!NOTE]
> `system` 等大分区可能超过 Artifact 的 2GiB 限制。建议只提取小分区，或先用 **Downloader** 下载完整文件后在本地处理。

### 🗜️ Tar.gz Decompresser 解压

下载 `.tar.gz` 压缩包并解压，**拍平目录结构**（所有文件移动到同一层目录；遇到同名文件会改名为 `foo.1.ext`，不会互相覆盖），然后发布到名为 `targz-d-<run_number>` 的 Release。

| 输入 | 说明 | 必填 |
| --- | --- | --- |
| `LINK` | `.tar.gz` 文件的直链地址 | ✅ |

### 🔄 Tar.gz to Zip 转换

下载 `.tar.gz` 压缩包并解压，删除其中的**符号链接**，重新打包为 `repacked.zip`，发布到名为 `targz-to-zip-<run_number>` 的 Release。

适用于目标只接受 `.zip` 格式、或压缩包内符号链接会导致问题的场景。

| 输入 | 说明 | 必填 |
| --- | --- | --- |
| `LINK` | `.tar.gz` 文件的直链地址 | ✅ |

### 📱 APKM to APK 合并

下载 `.apkm` 包（base + 多个 split APK），用 [REAndroid/APKEditor](https://github.com/REAndroid/APKEditor) 合并成一个独立 APK，可选 zipalign 与签名，然后发布到名为 `run-<run_number>` 的 Release，并上传一份 Artifact。

| 输入 | 说明 | 必填 |
| --- | --- | --- |
| `apkm_url` | `.apkm` 文件的直链地址 | ✅ |
| `output_name` | 输出文件名前缀（默认 `app`） | |
| `sign_apk` | 合并后 zipalign + 签名（默认开启）。未签名的 APK 无法安装 | |
| `extract_native_libs` | `extractNativeLibs` 模式：`manifest`（默认）/ `none` / `true` / `false` | |
| `apkeditor_version` | APKEditor 的 release tag，如 `V1.4.3`（留空为最新版） | |

> [!NOTE]
> 配置了仓库 Secrets `KEYSTORE_BASE64`、`KEYSTORE_PASSWORD`、`KEY_ALIAS`（可选 `KEY_PASSWORD`）时使用你自己的密钥签名；否则每次运行临时生成一个调试密钥，产物无法覆盖安装官方应用。

### 💻 System Test 系统测试

打印 GitHub Actions Runner 的系统信息：`lscpu`、`whoami`、`id`、`uname -a`、`free -h`、`df -h`、`tree /home` 以及 `neofetch`。用来查看 Runner 当前的硬件配置很方便。无需任何输入。

## 注意事项

- 所有工作流均为手动触发（`workflow_dispatch`）。
- GitHub 限制 Artifact / Release 中单个文件不超过 2GiB，Downloader 通过自动分割规避该限制。
- Artifact 超过保留期（默认 90 天）后会过期，Release 则永久保留。
- 请合理使用 Runner 资源，并遵守 [GitHub 服务条款](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)。

## 致谢

- [5ec1cff/payload-dumper](https://github.com/5ec1cff/payload-dumper)
- [REAndroid/APKEditor](https://github.com/REAndroid/APKEditor)

## 许可证

[AGPL-3.0](./LICENSE) © [lingyicute](https://github.com/lingyicute) 2023-2026

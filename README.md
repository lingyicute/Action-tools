# Action-tools

[![License: AGPL-3.0](https://img.shields.io/github/license/lingyicute/action-tools?color=blue)](./LICENSE)
![Downloader](https://github.com/lingyicute/Action-tools/actions/workflows/downloader.yml/badge.svg)
![Payload Dump](https://github.com/lingyicute/Action-tools/actions/workflows/payload-dumper.yml/badge.svg)
![Tar.gz decompresser](https://github.com/lingyicute/Action-tools/actions/workflows/tar-gz-decompresser.yml/badge.svg)
![Tar.gz to Zip](https://github.com/lingyicute/Action-tools/actions/workflows/tar-gz-to-zip.yml/badge.svg)
![System Test](https://github.com/lingyicute/Action-tools/actions/workflows/test-system.yml/badge.svg)

A collection of handy tools powered by GitHub Actions — download files from a link, dump partitions from Android OTA `payload.bin`, extract or convert `.tar.gz` archives, and inspect the runner environment. Everything runs in your browser; nothing to install locally.

**[中文](./README-ZH.md)** · [English]

## Highlights

- 🚀 **Zero setup** — everything runs on GitHub-hosted `ubuntu-latest` runners
- 🔗 **Link in, file out** — paste a URL, pick up the result from a Release or the run's Artifacts
- ✂️ **Auto file splitting** — the Downloader splits files ≥ 2GiB into 2046MiB parts, working around GitHub's per-file size limit
- 🤖 **Fully manual** — nothing consumes Actions minutes until you click *Run workflow*

## Tools at a glance

| Tool | What it does | Inputs | Output |
| --- | --- | --- | --- |
| ⬇️ [Downloader](#️-downloader) | Downloads any direct file link and publishes it to a Release (auto-splits at ≥ 2GiB) | `LINK` | Release + Artifact |
| 📦 [Payload Dumper](#-payload-dumper) | Extracts selected partitions from an Android OTA `payload.bin` (URL / zip supported) | `LINK`, `PART` | Artifact `imgs` |
| 🗜️ [Tar.gz Decompresser](#️-targz-decompresser) | Downloads and extracts a `.tar.gz`, flattening all files into one directory | `LINK` | Release |
| 🔄 [Tar.gz to Zip](#-targz-to-zip) | Converts a `.tar.gz` archive into a `.zip` (symlinks removed) | `LINK` | Release `repacked.zip` |
| 💻 [System Test](#-system-test) | Prints hardware / OS info of the Actions runner | — | Run logs |

## Getting started

1. **Fork** this repository (or use your own copy).
2. Open the **Actions** tab.
3. Select a workflow in the left sidebar.
4. Click **Run workflow**, fill in the inputs, and confirm.
5. Grab the results from the **Releases** page or the run's **Artifacts**.

## Tools

### ⬇️ Downloader

Downloads a file from any direct link via `wget` and publishes it as a GitHub Release (`downloader-<run_number>`), with an Artifact (`Downloaded-File`) as backup.

Files **≥ 2GiB** are automatically split into **2046MiB** parts to stay within GitHub's per-file limits.

| Input | Description | Required |
| --- | --- | --- |
| `LINK` | Direct URL of the file to download | ✅ |

> [!TIP]
> If the file was split, download **all** `.part` files and merge them locally:
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

### 📦 Payload Dumper

Extracts partitions from an Android OTA `payload.bin` using [5ec1cff/payload-dumper](https://github.com/5ec1cff/payload-dumper). This fork can stream directly from a **URL** or a **zip archive**, so you don't need to download the whole OTA package first — ideal for grabbing small partitions like `boot`, `init_boot`, or `vbmeta`.

| Input | Description | Required |
| --- | --- | --- |
| `LINK` | URL of `payload.bin`, or of the OTA zip containing it | ✅ |
| `PART` | Partitions to extract, comma-separated (e.g. `boot,vendor`) | ✅ |

Extracted `.img` files are uploaded as Artifact **`imgs`**.

> [!NOTE]
> Large partitions (e.g. `system`) may exceed the 2GiB artifact limit. Prefer small partitions, or use the **Downloader** first and process locally.

### 🗜️ Tar.gz Decompresser

Downloads a `.tar.gz` archive, extracts it, **flattens the directory structure** (all files are moved into a single directory), and publishes the files to a Release named `targz-d-<run_number>`.

| Input | Description | Required |
| --- | --- | --- |
| `LINK` | Direct URL of the `.tar.gz` file | ✅ |

### 🔄 Tar.gz to Zip

Downloads a `.tar.gz` archive, extracts it, removes **symlinks**, repacks everything into `repacked.zip`, and publishes it to a Release named `targz-to-zip-<run_number>`.

Handy when the destination only accepts `.zip`, or when symlinks inside the archive cause problems.

| Input | Description | Required |
| --- | --- | --- |
| `LINK` | Direct URL of the `.tar.gz` file | ✅ |

### 💻 System Test

Prints system information about the GitHub Actions runner: `lscpu`, `whoami`, `id`, `uname -a`, `free -h`, `df -h`, `tree /home`, and `neofetch`. Useful for checking the runner's current hardware specs. No inputs needed.

## Notes

- All workflows are triggered manually (`workflow_dispatch`).
- GitHub limits single files in Artifacts / Releases to 2GiB; the Downloader works around this with automatic splitting.
- Artifacts expire after the retention period (90 days by default) — Releases persist.
- Please use runner resources responsibly and in accordance with the [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).

## Credits

- [5ec1cff/payload-dumper](https://github.com/5ec1cff/payload-dumper)

## License

[AGPL-3.0](./LICENSE) © [lingyicute](https://github.com/lingyicute) 2023-2026

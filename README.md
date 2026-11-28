# E-Paper Photo Frame | 墨水屏电子相册

面向群晖 DSM7、Home Assistant 和手机离线电子拍立得的局域网照片平台。照片默认留在本地。

## 工作原理

只读照片目录 → EXIF/裁切/抖动 → 屏幕专用编码 → 完整帧校验 → 传输 → 刷新确认。提交、设备确认与物理显示必须区分。固件侧规划将板卡 HAL、屏幕、通信、供电、应用模式和可选功能解耦；断连保留旧图。

## 当前进度

- Python 图像转换、通用三/四色编码、照片目录、HTTP 预览、基础 WebUI、Docker 已有原型。
- 上一基准提交 729c351 的 Python 3.11/3.12 各 28 项测试及 Docker smoke 均通过：[Python CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46103850019)、[Docker CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46103850122)。
- 新增配置规划器、12 个测试方法和参数化配置 CI。新提交的 CI 结果以 [Actions](https://github.com/doa2011/epaper-photo-frame/actions) 为准。
- 尚无可刷写固件、实机认证、手机 App 或正式 HA 集成。配置产物是 JSON，不是固件。

上一轮 6538193 的 [Python CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46127946524) 两个版本各 40 项通过，[配置 CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46127946451) 12 项通过，[Docker CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46127946478) 通过（已查 jobs 日志）。本轮新增首个无源候选配置及回归测试，结果待 Actions。

## nRF52840 首选便携固件路线

用户确认 nRF52840 为首选，先从 PCA10056 DK + GDEM0397F81 (SSD2677) 开始。新增真实屏幕诊断编译 CI，包含 GDEM0397F81、GDEY116F51 (SSD2677) 和 GDEM0213B74 (SSD1680)，基于 GxEPD2 1.6.7，结果待 Actions。诊断不含 BLE/NFC、无源取电或完整图像传输；不发布未核对许可证与刷写布局的二进制。详细构建命令、引脚、限制见 [nRF52840 编译验证](docs/NRF52840.md)。正式统一通信固件继续评估 Nordic NCS/Zephyr；保留 ST25DV、TN2115S2、TN2115H 等备用路线，及 NAS/HA 原有功能。

基准 780dd72 已重新核实：配置 13 项、Python 3.11/3.12 各 41 项通过、Docker smoke 通过（[配置 CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46135803419)、[Python CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46135803404)、[Docker CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46135803412)）。

## 配置组合（候选，非硬件支持承诺）

| 模式预设 | 主控候选 | 屏幕候选 | 通信 | 供电 |
|---|---|---|---|---|
| frame-usb | ESP32-S3 | GDEY116F51 | Wi-Fi + BLE | USB |
| polaroid-ble | nRF52840 | 通用 400×300 | BLE | 电池 |
| polaroid-hybrid | nRF52840 | 通用 400×300 | NFC 唤醒 + BLE | 电池 |
| polaroid-tn2115s2 | TN2115S2 | GDEM0397F81 800×480 | NFC | 无源 |
| polaroid-passive | 专用无源 NFC 设备 | 通用 200×200 | NFC | 无源 |

候选主控能力表见 firmware_config.py。TLSR8258/8359、EFR32BG22/MG21/MG22、CH592、DA14531、ESP32/C3/C6、nRF52832 等仅为规划选项；未验证具体板卡、引脚、存储、工具链及通信协议。内置 NFC Tag 不等于无源屏幕供电。OpenEPaperLink 和免刷原厂价签将作为独立协议适配层，未实现。所有屏幕候选见 device_profiles.py；小屏通用规格不代表实际驱动。四色容量只是按行对齐的理论值。

## 如何生成配置

Python 3.11/3.12，项目目录执行：

```sh
python -m pip install -r requirements.txt
python firmware_config.py --preset frame-usb
python firmware_config.py --preset polaroid-tn2115s2 --output nfc-plan.json
python firmware_config.py --preset polaroid-hybrid --output manifest.json
python -m unittest discover -s tests -v
```

自定义 config.json 示例：

```json
{"chip":"esp32-s3","panel":"gdey097f91","mode":"hybrid","power":"usb","transports":["wifi","ble"],"features":["http","timer"]}
```

```sh
python firmware_config.py --config config.json --output manifest.json
```

配置器拒绝当前能力模型中不兼容的选择，例如 BLE-only 主控选择 Wi-Fi、无源 NFC 选择定时轮播、未选 Wi-Fi 却选 MQTT。即使校验通过，buildable 仍为 false：尚需真实板卡资源、GPIO、电气兼容和可复现工具链验证。固件烧录地址及备份恢复流程待具体目标实现后提供，不应使用配置清单刷机。

Actions 的 Firmware configuration plan 工作流在工作流进入默认分支且支持手动触发后可选择预设或自定义 JSON。现有研发分支 push/PR 自动校验，生成 manifest.json 和 SHA256SUMS，均非固件。暂不需要合并主线。

## NAS 与 HA

[DSM7 Docker 部署及验收](docs/DSM7.md)。HA 服务、BLE/NFC 手机写入、设备队列和轮播仍待开发。

## 硬件证据

[首个无源 NFC 目标与验证清单](docs/NFC.md)：TN2115S2 + GDEM0397F81，仅配置候选，尚无可刷固件。

用户报告 TLSR8359、JD79665，照片提示 GD25Q16E（2 MiB）。实际 FPC、GPIO、Flash 布局、色数未验证。SSD2677 的 960×672、960×640、960×680 候选屏幕需分别核实初始化、BUSY、映射、扫描方向和供电。参考 [ATC_TLSR_Paper](https://github.com/atc1441/ATC_TLSR_Paper)、[GxEPD2](https://github.com/ZinggJM/GxEPD2)、[hass-ble-esl](https://github.com/eigger/hass-ble-esl)。复用前检查许可。没有实机测试。

研发仅在 feature 分支进行，不自动合并。[PR #1](https://github.com/doa2011/epaper-photo-frame/pull/1)。


2026-11-28：首轮 nRF52840 矩阵在 DFU 打包阶段缺少 `adafruit-nrfutil`，见 [CI](https://github.com/doa2011/epaper-photo-frame/actions/runs/46142082395)。修复固定 Python 3.11 与 adafruit-nrfutil 0.5.3.post16，待 CI 验证；尚无实机结果。

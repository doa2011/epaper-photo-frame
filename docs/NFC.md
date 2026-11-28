# 首个无源 NFC 目标

TN2115S2 + GDEM0397F81（SSD2677，800×480，四色 96,000 字节）。用户已找到屏幕；FPC7750 仍待实物核对。

- [上游自定义固件固定版本](https://github.com/atc1441/Waveshare_NFC_E-Paper_Display_custom_firmware/tree/bb674f342ef5257d54eaec4801f3b5fa3be37175/Custom_firmware)：ARM GCC、CMSIS、32KB Flash / 8KB RAM、软件 SPI。尚无完整 NFC SDK；flash/gdbserver 残留 nRF52832 配置，禁止直接执行。根 GPL-3.0 与子工程 MPL-2.0 文件级许可须逐项确认。
- [屏幕参考驱动](https://github.com/ZinggJM/GxEPD2/blob/master/src/epd4c/GxEPD2_397c_GDEM0397F81.cpp)：BUSY 低有效，0x10 写帧，初始化 gate 680 而非可见 480；须与厂家参考程序核对。不得直接复用旧 2.13 寸 9-bit SPI。
- [屏幕厂家](https://www.good-display.com/product/577.html)；[无源开发方案](https://www.chivotech.com/index.php/zh/2020/03/21/nfc1/)；完整 SDK 与授权待取得。

## 验证顺序

1. Linux ARM GCC 编译最小固件，记录 ELF/BIN、尺寸和许可，暂不烧录。
2. 核实 FPC、电源及 GPIO，外供电验证四色色条与流式写帧；AVDD33/18 不作为屏幕电源。
3. 验证 NFC 分块、CRC、完整帧后刷新、掉电恢复；8KB RAM 不缓存完整 96KB 帧。
4. 实测手机取电、刷新峰值及低压保护，核实 HARV/VCAP 参考电路。

替代候选：TN2115H + ST25DV + STM32（射频耦合和功率待验证）；NTAG 5 Link + MCU + 储能（功率不足直接驱动的风险）。不能视为已验证方案。

当前仅配置及离线编码测试；未编译 TN2115S2 固件、未验证 NFC 协议、未实机刷新。配置命令：

`python firmware_config.py --preset polaroid-tn2115s2 --output nfc-plan.json`

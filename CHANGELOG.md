# Changelog / 研发记录

## 2026-11-28 — 5W Qi 底座与超级电容终端电源架构

- 新增三 PCB 分工：PCB-A nRF52840 + GDEM0397F81/SSD2677；PCB-B BQ51013B + LTC4041 + 超级电容；PCB-C USB-C + 1S 21700 + BQ25895 + TPS2121 + Qi TX。
- 终端不装锂电池，超级电容定义为脱座短时 BLE 收图/一次刷新缓冲，不承诺数小时便携。
- 保留 nRF52840 SWDIO/SWDCLK/RESET/GND/VTref。
- 整理 GDEM0397F81 的 24-pin FPC 初步网络映射、4-wire SPI、BUSY_N/RST_N、VPP 风险和连接器方向待确认事项。
- 新增候选 LCSC 料号：BQ51013BRHLR C55663、LTC4041EUFD C3151895、BQ25895RTWR C80200、TUSB320IRWBR C80170、TPS2121RUXR C485916、STM32C011F6P6TR C7021404、AP63203WU-7 C780769、MBR0530T1G C82046、FH12-24S-0.5SH(55) C202112。
- 修正底座电源拓扑：USB 5V 与 BQ25895 OTG 5V 通过 TPS2121 选择；BQ25895 PMID 仅作为 OTG 备用输入，不直接当作充电模式下的外部负载电源。
- 资料来源：Good Display GDEM0397F81 产品页与规格下载页、Solomon SSD2677 Rev 1.0、TI/ADI 数据手册、Microchip 5W Qi A11 参考设计、LCSC 器件目录。
- PR：[Document 5W Qi dock and supercapacitor portable power architecture](https://github.com/doa2011/epaper-photo-frame/pull/2)（草稿，未合并）。
- 文档：[三 PCB 电源架构](docs/hardware/qi-supercap-3pcb-architecture.md)。
- README：[项目入口](README.md)。

### 验证状态

- 软件 CI：既有 PR #1 的 Docker smoke job 运行成功（[Actions run 46145593703](https://github.com/doa2011/epaper-photo-frame/actions/runs/46145593703)）；包括 Compose/build、health、API/容器限制和真实照片转换步骤。
- 本次 PR #2：仅文档/README/研发记录变更，草稿 PR 未触发 CI。
- 电源拓扑：完成数据手册级方案核对，尚未画完整原理图、未做 SPICE/实测。
- GDEM0397F81/SSD2677：有厂家规格页和用户排线定义，尚未制作驱动板或实机刷新。
- Qi 接收/发射、超级电容容量、FOD、热设计：全部待样机验证。

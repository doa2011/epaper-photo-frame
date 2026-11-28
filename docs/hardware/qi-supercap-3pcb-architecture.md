# 5W Qi 底座 + 超级电容便携终端：三 PCB 电源架构

> 状态：**工程方案 / 候选器件**。不是已完成原理图、PCB 或实机验证。当前设计目标为 GDEM0397F81（3.97 英寸、800×480、黑白红黄、SSD2677）。打样前必须以 Good Display 提供的该型号完整规格书和 FPC 实物复核针脚、连接器接触面及电源参数。

## 1. 已确认的产品边界

- 底座：USB-C 5V/3A 输入，内置 1S 锂电池；USB 接入时给 Qi 发射端供电并给底座电池充电，USB 拔出后由底座电池继续给 Qi 发射端供电。
- 终端：不装锂电池；使用 5W Qi 接收和超级电容 UPS。
- 模式：自动检测。放到底座进入轮播；取出后关闭轮播，保留当前墨水屏画面，并在超级电容余量允许时完成一次 BLE 接收/照片刷新，然后休眠。
- 主控：nRF52840 模组，保留 SWDIO、SWDCLK、RESET、GND、VTref 调试/救援接口。
- 屏幕：GDEM0397F81，800×480，4 色，24-pin / 0.5 mm FPC，SSD2677。

**便携能力边界：**超级电容不是锂电池。第一版定义为“脱座短时工作/完成一次传图与刷新”，不承诺长时间随身显示。若以后要求数小时便携，需增加电池版本的 PCB-B 或替换电源板；PCB-A 和传图协议不变。

## 2. 三块 PCB 分工

### PCB-A：显示与主控板

职责：
- Raytac MDBT50Q-1MV2（nRF52840）或经验证的等效 nRF52840 模组。
- 3.3V 电源、SWD 调试焊盘/接口、复位键和测试点。
- SSD2677 屏幕 FPC 接口及其外部功率电路（Q1、L1、D1-D3、电容网络）。
- SPI、BUSY、RESET、DC、CS、BS 等信号连接。
- 预留 NFC 天线匹配/连接位置；NFC 天线不得与 Qi 接收线圈共用。

电源路径：
5V_SYS (PCB-B) → AP63203WU-7 3.3V/2A → nRF52840 + 屏幕逻辑/驱动电路

SSD2677 是显示模组侧的 COG/COF 裸晶驱动方案，不应把它当作普通 QFN 芯片直接加到 JLC SMT BOM。PCB-A 实际需要制造的是主控、FPC 和 SSD2677 应用电路。SSD2677 规格书给出的芯片订购形态为 Gold Bump Die；其应用电路给出外部 Q1、47 µH 电感、3 个肖特基二极管及电容网络。

### PCB-B：Qi 接收 + 超级电容 UPS

职责：
- 5W Qi 接收线圈、铁氧体片和匹配网络。
- BQ51013BRHLR 将 Qi 接收能量整流/调节为 5V。
- LTC4041 给超级电容充电，并在 Qi 输入消失时无缝切换为超级电容升压供电。
- 输出稳定的 5V_SYS 给 PCB-A。
- 输出 RX_POWER_FAIL / POWER_GOOD 状态给 nRF52840；可选增加霍尔传感器输入以确认物理入座。

电源路径：
Qi RX coil → BQ51013BRHLR (5V) → LTC4041 → 5V_SYS → PCB-A
LTC4041 ↔ 2 × 2.7V supercapacitors (series)

建议首版从 **2 × 10F / 2.7V** 低 ESR 超级电容开始（串联等效 5F）；空间允许、希望增加脱座工作时间时改为 **2 × 20F / 2.7V**（串联等效 10F）。LTC4041 内置双电容均衡，仍应选同型号、同批次电容，并实测单体电压、ESR、漏电和温升。超级电容采用外购件/手焊或单独压接，不假设 JLC 常规贴片库存有合适的大容量型号。

建议先将 LTC4041 充电电流设在约 0.3–0.5A 范围，并给系统负载留余量；BQ51013B 接收端能力约为 5V/1A 级，不能按 LTC4041 自身 2.5A 的能力直接设置充电电流。

### PCB-C：底座 USB-C + 电池 + Qi 发射

职责：
- USB-C 5V/3A 输入和 Type-C CC 电流能力识别。
- BQ25895 单节锂电池充电/电源路径管理及电池模式下的 5V OTG。
- TPS2121 双路电源 MUX，USB 优先，断电时切换到 BQ25895 OTG。
- 1S 21700 电池（建议 4000–5000mAh、高放电能力、带保护/NTC）。
- 5V Qi 发射控制器、功率级、匹配网络和发射线圈。
- 底座电池、USB 输入、Qi 发射状态测试点。

电源路径：
- USB-C 5V → TPS2121 IN1（USB 优先），同时连接 BQ25895 VBUS 给电池充电；
- 1S 21700 ↔ BQ25895 BAT；
- BQ25895 在无 VBUS 时启用 OTG，PMID 提供 5V → TPS2121 IN2；
- TPS2121 OUT → 5V_TX → Qi 发射级。

USB 插入时 TPS2121 选择 IN1，Qi TX 由 USB 直接供电，BQ25895 按剩余输入功率给电池充电；USB 拔出后，BQ25895 在 OTG 已配置的条件下从电池产生 5V，TPS2121 切到 IN2。PMID 只作为 BQ25895 的 OTG 5V 源接入 MUX 的备用输入，不作为充电模式下的外部负载电源；未选中的输入由 TPS2121 隔离。TPS2121 支持 2.8–22V 双输入、反向电流阻断和典型 5µs 切换，限流值需按 Qi TX 实测输入电流设置。

BQ25895 支持单节锂电池充电、电源路径管理及最高约 3.1A 的 5V 升压/OTG 输出。其 OTG_CONFIG、OTG 引脚和输入检测状态必须按数据手册配置。TUSB320 读取 USB-C 电源宣告的电流能力，底座控制 MCU 再按“Qi 发射输入电流 + 电池充电电流 + 转换损耗”设置 BQ25895 的输入/充电限流；5V/3A 适配器是首版目标，若只检测到 1.5A 或默认电流，应降低充电电流，必要时暂停充电。

**Qi 发射级首版建议：**优先使用经过验证的 5W Qi BPP A11 发射模块，或按 Microchip 5W 参考设计实现。Microchip 公开资料确认该方案为 5V USB-C 输入、5W BPP、标称 70%+ 传输效率，并有基于功率效率的 FOD；设计文件需登录并接受其参考设计许可，不能把下载的设计文件直接当作开源资料分发。首版可先用成熟 TX 模块验证整机电源，再决定是否将 TX 功率级整合到 PCB-C。底座另设 STM32C011F6P6TR 小控制器，管理 TUSB320/BQ25895、检测 USB 状态和电池电量；TX 模块内部控制器独立运行。

## 3. 主要器件候选

| 位置 | 器件 | 作用 | LCSC 编号/采购状态 |
|---|---|---|---|
| PCB-A | Raytac MDBT50Q-1MV2 | nRF52840 BLE/NFC-A 模组，48 GPIO、1MB Flash、256KB RAM | 模组优先向 Raytac/授权渠道采购；JLC 库存/料号未锁定 |
| PCB-A | AP63203WU-7 | 5V→3.3V 同步降压，2A | **C780769** |
| PCB-A | FH12-24S-0.5SH(55) | 24P、0.5mm FPC ZIF，底接触 | **C202112**，仅为连接器候选；须核对面板触点朝向、FPC 厚度及 Pin-1 方向 |
| PCB-A | MBR0530T1G ×3 | SSD2677 外部升压/负压电路肖特基二极管 | **C82046** |
| PCB-A | 47µH 电感 | SSD2677 外部功率电路 | 候选 **C9934**（47µH、1.9A、Isat 2.44A，体积较大）；不要误用 C2454210，其目录规格仅约 200mA |
| PCB-A | Si1304BDL 或 NX3008NBK | SSD2677 外部 N-MOS | 按 SSD2677 规格书要求采购原厂/可追溯器件；LCSC 替代料需逐项核对 VDS、VGS(th)、RDS(on)，暂不锁定替代料 |
| PCB-A | 4.7µF/25V X7R ×若干、1µF/25V X7R、2.2Ω/0805/1% | SSD2677 外部电源电容和电流检测/驱动电阻 | 通用料；以该面板最终应用图为准 |
| PCB-B | BQ51013BRHLR | Qi 5W 接收，5V 稳压输出、Qi 通信及保护 | **C55663** |
| PCB-B | LTC4041EUFD#PBF | 超级电容充电/备用电源管理，单颗或两颗串联，内部均衡，2.5A 级充放电管理 | **C3151895** |
| PCB-B | 2 × 2.7V 10F 或 20F 低 ESR 超级电容 | 脱座短时储能 | 外购件；先测 ESR/漏电/体积，不按普通 JLC SMT 件处理 |
| PCB-B | 5W Qi RX 线圈 + 铁氧体片 | 无线接收 | 与 BQ51013B 匹配；不建议使用未知参数裸线圈 |
| PCB-C | BQ25895RTWR | 1S 锂电池充电、电源路径、5V OTG 升压 | **C80200** |
| PCB-C | TUSB320IRWBR | USB-C CC 检测、方向/电流能力识别 | **C80170** |\n| PCB-C | TPS2121RUXR | USB 5V / BQ25895 OTG 5V 双路电源 MUX，自动切换、反向电流阻断 | **C485916** |\n| PCB-C | STM32C011F6P6TR | 底座电源管理 MCU：读取 TUSB320、配置 BQ25895、管理 OTG/电池状态 | **C7021404** |
| PCB-C | 5W Qi TX A11 模块/控制器 | Qi 发射状态机、功率级、FOD | 首版优先成熟模块；Microchip 参考设计文件须接受其许可，不作为开源 BOM/源码分发 |
| PCB-C | 1S 21700 + NTC/保护 | 底座电池 | 电芯/保护包外购，按电芯规格设置充电电流 |
| PCB-C | 5W Qi TX 线圈、谐振电容、功率 MOS/驱动 | Qi 发射功率级 | 首版优先成熟模块或 Microchip A11 参考设计，不在缺少线圈参数时锁定料号 |

> LCSC 编号表示目录中可检索到对应器件，不代表下单当天必有库存，也不代表每个器件都属于 JLC 基础库/可免费贴装。大电容、线圈、电池、无线模块和特殊连接器可能需要自备料或手焊。

## 4. GDEM0397F81 面板接口初步映射

依据用户提供的排线定义，当前原理图网络名建议如下；最终必须再对照该型号完整规格书和实物 FPC 复核。

| FPC Pin | 面板信号 | PCB-A 连接/处理 |
|---:|---|---|
| 1 | NC | 不连接 |
| 2 | GDR | SSD2677 外部 MOSFET 驱动网络 |
| 3 | RESE | 电流检测/驱动控制网络 |
| 4 | NC | 不连接 |
| 5 | VDHR | 面板源驱动电源电容网络 |
| 6–7 | NC | 不连接（按用户当前排线定义） |
| 8 | BS | 下拉选择 4-wire SPI（以芯片规格书为准） |
| 9 | BUSY_N | nRF GPIO 输入；低电平忙、高电平空闲 |
| 10 | RST_N | nRF GPIO，低有效复位 |
| 11 | DC | nRF GPIO |
| 12 | CS_N | nRF SPI CS，低有效 |
| 13 | CLK | nRF SPI SCK |
| 14 | DATA | nRF SPI MOSI |
| 15 | VDDIO | 3.3V 接口逻辑电源 |
| 16 | VDD | 按面板规格书供电 |
| 17 | GND | 地 |
| 18 | VDDD | 按面板规格书供电 |
| 19 | VPP | OTP 相关；未获厂家确认前不接外部高压 |
| 20 | VDH(VSH) | 面板源驱动电压电容网络 |
| 21 | VGH | 正栅极驱动电压电容网络 |
| 22 | VDL(VSL) | 负源驱动电压电容网络 |
| 23 | VGL | 负栅极驱动电压电容网络 |
| 24 | VCOM | 公共电极电压电容网络 |

SSD2677 规格书规定 BS1=0 选择 4-wire SPI；BUSY_N 为低忙/高空闲，RST_N 低有效。首版固件应先用较低 SPI 时钟验证，再逐步提升，芯片规格书给出的最高 SPI 写入速率为 20MHz。

## 5. 超级电容容量估算

两颗相同电容串联时：
- 2 × 10F / 2.7V → 等效约 5F；
- 2 × 20F / 2.7V → 等效约 10F。

假设 LTC4041 将总电压充到 5.0V，系统在等效电容降到 3.0V 时停止工作：

E = 1/2 × C × (5.0² − 3.0²)

- 5F：约 40J；
- 10F：约 80J。

以上为理想储能，不是实测续航。若按 80% 可用效率估算，5F 在 0.2W 平均负载下约 160 秒，在 0.5W 下约 64 秒；实际时间会受电容 ESR、温度、漏电、LTC4041 欠压门限、Qi 接收功率和刷新瞬时电流影响。

GDEM0397F81 厂商页面标注典型功耗 66mW、深睡功耗 0.0012mW、全刷约 21 秒、快速刷新约 12 秒；这是屏幕参数，不等于整机 BLE 接收/主控/电源转换功耗。首轮先做 2×10F 原型并实测，如果脱座 BLE 传图加刷新不够，再升级 2×20F。

## 6. 自动模式状态机

1. **DOCKED**：Qi 接收 Power-Good 有效且（可选）霍尔传感器确认入座，启动轮播；LTC4041 给超级电容充电。
2. **DETACH_PENDING**：Qi 输入消失，先等待 100–500ms 去抖；若霍尔仍确认在座，判断为对位/发射异常，不立即切换。
3. **PORTABLE_SESSION**：停止轮播；读取超级电容余量；允许短时间 BLE 广播/配对和一次照片传输。
4. **REFRESHING**：确保整帧数据完整、校验通过后再刷新；等待 BUSY_N 回到空闲。
5. **LOW_ENERGY_SLEEP**：余量不足或会话超时，关闭 BLE/非必要外设，保存状态并进入低功耗；墨水屏保留最后画面。
6. **DOCKED**：重新检测到稳定 Qi 输入后恢复轮播并补充超级电容。

PFO/POWER_FAIL 和 Qi 接收状态建议接到 nRF GPIO；可选霍尔输入提供独立的物理入座判定。不能仅靠 5V 电压瞬时变化判断模式，否则 Qi 对位抖动可能导致模式来回切换。

## 7. PCB 布局与调试要求

- PCB-A：nRF52840 天线端放在板边，按模组手册留 RF keep-out；Qi 线圈、铁氧体、电池和金属结构远离天线。
- PCB-A：SSD2677 的 Q1/L1/D1-D3 和高压电容紧靠 FPC/驱动回路，缩短开关电流环路；高压波形网络远离 nRF 天线。
- PCB-B：Qi 接收线圈背面放匹配铁氧体；超级电容靠近 LTC4041，缩短大电流回路；预留电容单体测量点。
- PCB-C：Qi TX 线圈、谐振电容、功率 MOS 和电流检测按参考设计布局；线圈与底座电池、金属件之间留足空间。
- 三块板均预留 5V、3V3、GND、复位、关键电源状态测试点。
- PCB-A 必须保留 SWD：SWDIO、SWDCLK、RESET、GND、VTref（可另加 VDD）；推荐 1.27mm 2×3 或 Tag-Connect 测试焊盘。
- NFC 天线与 Qi 线圈分区，预留独立匹配网络和铁氧体；不与 Qi 线圈共用。

## 8. 制板前必须完成的验证

- [ ] 取得并核对 GDEM0397F81 完整规格书、机械图、FPC 触点朝向和 Pin-1 标记。
- [ ] 向 Good Display 确认该批 GDEM0397F81 的 SSD2677/FPL 许可适用范围，以及 VPP、VDDD、VDD、VCOM 的最终接法。
- [ ] 用实验板验证 SSD2677 SPI、BUSY 极性、复位时序、外部电源电路和波形。
- [ ] 测量整机待机、BLE 接收、全刷/快速刷新时的峰值电流与能量。
- [ ] 验证 BQ51013B + LTC4041 在 5W Qi 下的稳压、充电时间、断开切换、超级电容 ESR 和热表现。
- [ ] 验证 BQ25895 在 USB 输入和电池 OTG 两种状态下对 Qi TX 的供电与切换。
- [ ] 用金属异物、错位、温升和长时间运行测试 Qi FOD/保护。
- [ ] 完成 SWD 烧录、低电压掉电、断连保留旧图和自动模式回归。

## 9. 参考资料

- [Good Display GDEM0397F81 产品页与规格参数](https://www.good-display.com/product/577.html)
- [Solomon Systech SSD2677 Rev 1.0 数据手册（应用电路、引脚、SPI、FPL 使用限制）](https://files.waveshare.com/wiki/common/SSD2677_1.0.pdf)
- [Raytac MDBT50Q-1MV2 官方资料](https://www.raytac.com/product/ins.php?index_id=24)
- [TI BQ51013B 数据手册](https://www.ti.com/lit/ds/symlink/bq51013b.pdf)
- [ADI LTC4041 数据手册](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4041.pdf)
- [TI BQ25895 数据手册](https://www.ti.com/lit/ds/symlink/bq25895.pdf)
- [TI TUSB320 产品资料](https://www.ti.com/product/TUSB320)\n- [LCSC TPS2121RUXR C485916](https://www.lcsc.com/product-detail/C485916.html)\n- [LCSC STM32C011F6P6TR C7021404](https://www.lcsc.com/product-detail/C7021404.html)
- [Microchip 5W Qi A11 发射参考设计](https://www.microchip.com/en-us/tools-resources/reference-designs/qi-5w-wireless-transmitter-charger)
- [LCSC BQ51013BRHLR C55663](https://www.lcsc.com/product-detail/C55663.html)
- [LCSC LTC4041EUFD C3151895](https://www.lcsc.com/product-detail/C3151895.html)
- [LCSC BQ25895RTWR C80200](https://www.lcsc.com/product-detail/C80200.html)
- [LCSC AP63203WU-7 C780769](https://www.lcsc.com/product-detail/C780769.html)
- [LCSC TUSB320IRWBR C80170](https://www.lcsc.com/product-detail/C80170.html)
- [LCSC MBR0530T1G C82046](https://www.lcsc.com/product-detail/C82046.html)
- [LCSC 24P FPC 连接器 FH12-24S-0.5SH(55) C202112](https://www.lcsc.com/product-detail/C202112.html)

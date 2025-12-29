# 数据格式说明

本文档详细说明 `data/` 目录下所有数据文件的格式、内容和解析结果。

## 文件清单

| 文件名 | 大小 | 格式 | 数据量 | 说明 |
|--------|------|------|--------|------|
| `3_NavigationResultGNSS.dat` | 2.6 MB | ASCII Hex | 29,831 条 | GNSS 数据（附录1 GNSS帧） |
| `3_NavigationResult.dat` | 284 MB | ASCII Hex | 2,832,350 条 | IMU 原始数据（附录1 INS帧） |
| `3_NavigationResult_txt.dat` | 422 MB | 纯文本 | 2,833,904 条 | 解算结果（附录2格式） |
| `com15.txt` | 1.8 MB | NMEA文本 | 15,141 条 | 导航输出（1Hz） |
| `com16.txt` | 18 MB | NMEA文本 | 151,574 条 | 导航输出（10Hz） |

## 数据格式详解

### 1. GNSS 数据 (3_NavigationResultGNSS.dat)

**编码方式**: ASCII 十六进制字符串（每行一帧，换行符分隔）

**原始格式**: 附录1 - 十六进制混合帧的 GNSS 部分

**解析结果**:
- 总条数: 29,831 条
- 时间范围: 2025-10-29 04:29 ~ 08:26
- 频率: 1 Hz
- 数据完整性: 校验和验证通过

**数据结构** (每帧 46 字节):

| 字节序号 | 字段名称 | 字节数 | 数据类型 | 说明 |
|----------|----------|--------|----------|------|
| 1-2 | 帧头 | 2 | unsigned char | 0x99, 0x66 |
| 3 | 长度 | 1 | unsigned char | 0x2e (46字节) |
| 4-5 | 年 | 2 | unsigned short | 低字节序 |
| 6 | 月 | 1 | unsigned char | |
| 7 | 日 | 1 | unsigned char | |
| 8 | 时 | 1 | unsigned char | |
| 9 | 分 | 1 | unsigned char | |
| 10-13 | 微秒 | 4 | unsigned int | 低字节序 |
| 14-21 | 经度 | 8 | double | 低字节序，单位：度 |
| 22-29 | 纬度 | 8 | double | 低字节序，单位：度 |
| 30-33 | 高度 | 4 | float | 低字节序，单位：米 |
| 34-37 | 速度x | 4 | float | 低字节序，单位：m/s |
| 38-41 | 速度y | 4 | float | 低字节序，单位：m/s |
| 42-45 | 速度z | 4 | float | 低字节序，单位：m/s |
| 46 | 校验和 | 1 | unsigned char | 字节4-45求和取低8位 |

**示例数据**:
```
第一条: 经度 116.36158439°, 纬度 40.05318298°, 高度 32.24m
时间: 2025-10-29 04:29:43900000
速度: (0.00, 0.00, 0.00) m/s
```

### 2. IMU 原始数据 (3_NavigationResult.dat)

**编码方式**: ASCII 十六进制字符串（每行一帧，换行符分隔）

**原始格式**: 附录1 - INS 帧（52字节）

**解析结果**:
- 总条数: 2,832,350 条
- 时间范围: 2025-10-29 04:29 ~ 08:25
- 频率: 约 95 Hz
- 数据完整性: 校验和验证通过

**数据结构** (每帧 52 字节):

| 字节序号 | 字段名称 | 字节数 | 数据类型 | 说明 |
|----------|----------|--------|----------|------|
| 1-2 | 帧头 | 2 | unsigned char | 0x55, 0xaa |
| 3 | 长度 | 1 | unsigned char | 0x34 (52字节) |
| 4-27 | 陀螺仪 x,y,z | 3×8 | double | 低字节序，单位：rad/s |
| 28-51 | 加速度 x,y,z | 3×8 | double | 低字节序，单位：m/s² |
| 52 | 校验和 | 1 | unsigned char | 字节4-51求和取低8位 |

**示例数据**:
```
第一条:
陀螺仪 (rad/s): x=0.000100, y=-0.000020, z=0.000020
加速度 (m/s²): x=0.134000, y=0.136000, z=9.772000
```

### 3. 解算结果 (3_NavigationResult_txt.dat)

**编码方式**: 纯文本，空格分隔

**原始格式**: 附录2 - 解算结果文本格式

**解析结果**:
- 总条数: 2,833,904 条
- 时间范围: 2025-10-29 04:29 ~ 08:25
- 频率: 约 200 Hz
- 导航状态分布:
  - 纯惯导 (状态0): 260,772 条 (9.2%)
  - 松组合 (状态2): 2,573,132 条 (90.8%)

**数据结构** (每行 26 个字段):

| 序号 | 字段名称 | 数据类型 | 说明 |
|------|----------|----------|------|
| 1 | 年 | int | |
| 2 | 月 | int | |
| 3 | 日 | int | |
| 4 | 时 | int | |
| 5 | 分 | int | |
| 6 | 微秒 | int | |
| 7 | 导航状态 | int | 0:纯惯；2:松组合；3:对准；4:待机 |
| 8-16 | 组合导航信息 | float | 经纬高(3) + 速度xyz(3) + 姿态RPH(3) |
| 17-25 | 纯惯导信息 | float | 经纬高(3) + 速度xyz(3) + 姿态RPH(3) |
| 26 | 帧序号 | int | 0-199 循环 |

**字段详解**:
- **组合导航信息**: 经度、纬度、高度、速度x、速度y、速度z、横滚、航向、俯仰
- **纯惯导信息**: 经度、纬度、高度、速度x、速度y、速度z、横滚、航向、俯仰

**示例数据**:
```
2025 10 29 4 29 43900000 0 116.3616 40.0532 32.24  0.00 -0.00  0.29 -2.065 261.439  0.748 116.3616 40.0532 32.24  0.00 -0.00  0.29 -2.065 261.439  0.748 130
```

### 4. NMEA 导航输出 (com15.txt / com16.txt)

**格式**: NMEA/自定义 ASCII 协议

**帧头**: `$BDFPD,`

**字段说明**:
- 字段1: 协议头
- 字段2: GPS周
- 字段3: 时间戳（秒）
- 字段4-6: 姿态角（航向、俯仰、横滚）
- 字段7-8: 纬度、经度
- 字段9: 高度
- 字段10-12: 速度 (vx, vy, vz)

**示例**:
```
$BDFPD,2390,274479.330,355.74516,-1.10572,-2.15644,40.05316524,116.36160523,39.360,0.0019,-0.0003,0.0008,28,35,16,50*50
```

## 附录1：十六进制混合帧存储格式（原始说明）

数据以**低字节在前**存储，卫导有效时含卫导+惯导信息，卫导无效时仅存惯导信息。

### GNSS 帧 (46 字节)

| 字节序号 | 设备信息 | 数据名称 | 字节数 | 数据类型 | 说明 |
|----------|----------|----------|--------|----------|------|
| 1-2 | | 帧头 | 2 | unsigned char | 0x99, 0x66 |
| 3 | | 长度 | 1 | unsigned char | 0x2e |
| 4-5 | | 年 | 2 | unsigned short | |
| 6 | | 月 | 1 | unsigned char | |
| 7 | | 日 | 1 | unsigned char | |
| 8 | | 时 | 1 | unsigned char | |
| 9 | | 分 | 1 | unsigned char | |
| 10-13 | GNSS | 微秒 | 4 | unsigned int | |
| 14-21 | | 经度 | 8 | double | |
| 22-29 | | 纬度 | 8 | double | |
| 30-33 | | 高度 | 4 | float | |
| 34-37 | | 速度x | 4 | float | |
| 38-41 | | 速度y | 4 | float | |
| 42-45 | | 速度z | 4 | float | |
| 46 | | 校验和 | 1 | unsigned char | 4-45字节求和取低八位 |

### INS 帧 (52 字节)

| 字节序号 | 设备信息 | 数据名称 | 字节数 | 数据类型 | 说明 |
|----------|----------|----------|--------|----------|------|
| 1-2 | | 帧头 | 2 | unsigned char | 0x55, 0xaa |
| 3 | | 长度 | 1 | unsigned char | 0x34 |
| 4-27 | INS | IMU三轴陀螺仪输出 | 3×8 | double | 角增量累加值，低字节在前，单位：rad/s |
| 28-51 | | IMU三轴加速度输出 | 3×8 | double | 速度增量累加值，低字节在前，单位：m/s² |
| 52 | | 校验和 | 1 | unsigned char | 4-51求和取低八位 |

**说明**:
- `3_NavigationResultGNSS.dat` 包含 GNSS 帧（46字节）
- `3_NavigationResult.dat` 包含 INS 帧（52字节）
- 两者分别存储，未发现 GNSS+INS 混合帧（98字节）

## 附录2：解算数据存储格式（原始说明）

### 二进制格式 (160 字节)

| 序号 | 数据类型 | 数据名称 | 字节数 | 数据类型 | 说明 |
|------|----------|----------|--------|----------|------|
| 1 | 卫导时间信息 | 年 | 2 | unsigned short | |
| 2 | | 月 | 1 | unsigned char | |
| 3 | | 日 | 1 | unsigned char | |
| 4 | | 时 | 1 | unsigned char | |
| 5 | | 分 | 1 | unsigned char | |
| 6 | | 微秒 | 4 | unsigned int | |
| 7 | 组合导航信息 | 导航状态 | 1 | char | 0:纯惯；2:松组合；3:对准；4:待机 |
| 8 | | 经度 | 8 | double | |
| 9 | | 纬度 | 8 | double | |
| 10 | | 高度 | 8 | double | |
| 11 | | 速度x | 8 | double | |
| 12 | | 速度y | 8 | double | |
| 13 | | 速度z | 8 | double | |
| 14 | | 横滚 | 8 | double | |
| 15 | | 航向 | 8 | double | |
| 16 | | 俯仰 | 8 | double | |
| 17 | 纯惯导航信息 | 经度 | 8 | double | |
| 18 | | 纬度 | 8 | double | |
| 19 | | 高度 | 8 | double | |
| 20 | | 速度x | 8 | double | |
| 21 | | 速度y | 8 | double | |
| 22 | | 速度z | 8 | double | |
| 23 | | 横滚 | 8 | double | |
| 24 | | 航向 | 8 | double | |
| 25 | | 俯仰 | 8 | double | |
| 26 | | 帧序号 | 4 | int | 0-199 |

**注意**: `3_NavigationResult_txt.dat` 使用文本格式（空格分隔），对应上述二进制结构。

## 数据质量评估

1. **GNSS 数据** (3_NavigationResultGNSS.dat)
   - 数量: 29,831 条
   - 频率: 1 Hz
   - 质量: 校验和验证通过
   - 用途: GNSS 插值、轨迹可视化

2. **IMU 原始数据** (3_NavigationResult.dat)
   - 数量: 2,832,350 条
   - 频率: 约 95 Hz
   - 质量: 校验和验证通过
   - 用途: 时序同步、IMU 数据处理

3. **解算结果** (3_NavigationResult_txt.dat)
   - 数量: 2,833,904 条
   - 频率: 约 200 Hz
   - 用途: 组合导航 vs 纯惯导对比分析

## 解析器使用示例

### GNSS 数据解析

```python
from src.parsers.hex_parser import HexFrameParser

gnss_list, _ = HexFrameParser.parse_file('data/3_NavigationResultGNSS.dat')
print(f"GNSS 数据: {len(gnss_list)} 条")
print(f"第一条: 经度 {gnss_list[0].longitude:.8f}°")
```

### IMU 数据解析

```python
from src.parsers.ins_parser import INSFrameParser

imu_list = INSFrameParser.parse_file('data/3_NavigationResult.dat')
print(f"IMU 数据: {len(imu_list)} 条")
print(f"陀螺仪: ({imu_list[0].gyro_x}, {imu_list[0].gyro_y}, {imu_list[0].gyro_z})")
```

### 解算结果解析

```python
from src.parsers.result_text_parser import ResultTextParser

results = ResultTextParser.parse_file('data/3_NavigationResult_txt.dat')
print(f"解算结果: {len(results)} 条")
print(f"导航状态: {results[0].nav_status}")
```

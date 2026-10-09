# 京东云无线宝一代 RE-SP-01B 刷官方 OpenWrt 25.12 + 设为 AP 中继模式

完整刷机记录：从原厂 JDCOS 4.0.0 通过 U-Boot 强刷过渡固件 → 刷 Breed → 备份原厂 → 刷官方 OpenWrt 25.12 → 配成 AP 中继接入主路由。

> 本文档基于一台实机（MAC `DC:D8:7C:0D:2C:2E`、原厂 `JDCOS-4.0.0.r6645`）的完整操作整理，照做即可复现。

---

## 一、设备信息

| 项目 | 参数 |
|------|------|
| 型号 | 京东云无线宝 1 代（RE-SP-01B / JDBox Gen1） |
| SoC | 联发科 MT7621AT 双核 880MHz |
| 内存 | 512MB |
| 闪存 | 32MB NOR（Winbond）+ 内置 eMMC（32/64/128G 版本） |
| 网口 | 1×WAN（蓝）+ 2×LAN（黑），千兆 |
| 原厂固件 | JDCOS 4.0.0.r6645（已满足免拆强刷条件） |
| 原厂 MAC | DC:D8:7C:0D:2C:2E |

---

## 二、风险提示

- ⚠️ **刷机前务必在 Breed 里备份 eeprom（WiFi 校准）和 fullflash（整片）**。丢了原厂 WiFi 校准会导致无线信号变差且无法恢复。
- ⚠️ 备份文件含本机唯一的 MAC / 无线校准数据，**请勿上传到公开仓库**，自行本地保存即可。
- ⚠️ 本设备是 MT7621 + 32MB NOR，官方 OpenWrt 25.12 的 kernel+rootfs 都落在 NOR 上，eMMC 留作存储；不要用 openwrt-ai(Kwrt) 之类只给极简 sysupgrade 的第三方编译（实测无 LuCI、SSH 密码也对不上，刷完进不去管理）。

---

## 三、准备工作

- 一根网线（电脑直连京东云）
- 牙签 / 回形针（捅 RESET 小孔）
- 一台能手动设静态 IP 的电脑
- 固件（本仓库 `firmware/` 目录已附带，见下表）

---

## 四、固件清单（`firmware/`）

| 文件 | 大小（字节） | SHA256 | 用途 |
|------|------------|--------|------|
| `jdcloud-1-transitional.zip` | 18,761,643 | `7008f4b2353a17e07af3d2d12f1688464989d59c841221c20a21a809a70af61e` | 京东云一代 4.0 过渡固件（含 Breed 文件），U-Boot 强刷用 |
| `openwrt-25.12.5-initramfs-kernel.bin` | 8,190,856 | `f9cb560658451483b523d331f9473cf96db409db6ad08014a488848cf897e131` | 官方 OpenWrt 25.12.5 内存启动镜像（临时系统中转用） |
| `openwrt-25.12.5-squashfs-sysupgrade.bin` | 8,389,168 | `39da8c48e9f29355cd200a8b874e024735806792ba032a4ecdf86b9e89444640` | 官方 OpenWrt 25.12.5 升级包（写入闪存固化） |

> 过渡固件 zip 解压后含两个文件：
> - `Bootloader(京东云一代4.0原厂uboot).bin` —— 原厂 uboot，**本次不刷**
> - `JDC4.0.0.r6636_ssh(根目录含有breed文件).bin` —— 过渡固件本体，U-Boot 强刷这个（仓库内 `jd_trans.bin` 是它的副本）

---

## 五、刷机流程

### 第 1 步：U-Boot 恢复模式强刷过渡固件

1. 电脑网线接京东云 **WAN（蓝口）**。
2. 电脑网卡设静态 IP `192.168.68.2/24`（网关留空）。
3. 京东云断电 → 长按 RESET 通电进 U-Boot 恢复（或原厂系统自带恢复入口）→ 浏览器开 `http://192.168.68.1/`。
4. Choose File → 选 `jdcloud-1-transitional.zip` 解压出的过渡固件（或仓库内 `jd_trans.bin`）→ Upload。
5. 出现确认页 → **核对 MD5 / 大小 → 必须点 `Proceed`** 才真正刷写并重启（灯会快速闪烁，约 1~2 分钟）。

> 🔴 **关键坑**：U-Boot 恢复是**两步流程**（Upload → Confirm 页点 Proceed）。只传不点 Proceed = 没刷进去，灯不闪、设备一直停在恢复模式（肉眼很容易看漏）。

### 第 2 步：进过渡固件、刷 Breed

1. 重启后把网线换到 **LAN（黑口）**。
2. 电脑仍保持 `192.168.68.x` 同段（如 `192.168.68.2`）。
3. 浏览器 / SSH 进 `192.168.68.1`（过渡固件管理页或 SSH）。
4. SSH 登录：`root` / `admin`（过渡固件默认密码是 **admin**，不是 password）。
5. 执行：
   ```sh
   mtd write /breed-mt7621-jd-cloud-1.bin Bootloader
   ```
   （breed 文件在过渡固件根目录，`MTD_EXIT=0` 即成功）
6. 断电，长按 RESET 10 秒进 Breed。

### 第 3 步：Breed 备份原厂（保命步骤，必做）

1. 电脑网卡设 `192.168.1.100/24`，网线接 LAN 口（Breed 控制台在 `192.168.1.1`）。
2. 浏览器开 `http://192.168.1.1/`（Breed 1.1 r1337 控制台）。
3. 左侧「固件备份」→ 分别下载 **eeprom**（WiFi 校准，64KB）和 **fullflash**（整片 32MB）。
4. **本地妥善保存，切勿上传。**

### 第 4 步：Breed 刷官方 OpenWrt

> 🔴 **坑**：Breed「常规固件」模式直接传 `sysupgrade.bin` 会报 **「闪存布局无效」**。因为 Breed r1337（2021）不认新格式的 FIT 镜像。两种解法：

**方案 A（推荐）：内存启动中转**
1. Breed → 固件更新 → 顶部选「**内存启动**」→ 传 `openwrt-25.12.5-initramfs-kernel.bin` → 内存启动（仅跑在内存，不写闪存）。
2. 浏览器开 `http://192.168.1.1/` → 进 LuCI（此时是 RAM 临时系统，顶部黄条提示 recovery 模式）。
3. 系统 → 备份/升级 → 上传 `openwrt-25.12.5-squashfs-sysupgrade.bin` → **取消勾选「保留配置」** → 刷写。
4. 重启后即为正式固化的 OpenWrt。

**方案 B（兜底）：编程器固件整片刷**
将官方 sysupgrade 拼进「含 Breed 的 fullflash 备份」的 firmware 区（偏移 0x50000），用 Breed「固件更新 → **编程器固件**」整片刷。脚本思路见仓库 `scripts/`（需你用自己的 fullflash 备份生成，**不要上传备份**）。

### 第 5 步：首次配置（设密码、装中文）

1. 浏览器开 `http://192.168.1.1/` → 首次进 LuCI 强制设 **root 密码**（`<你的管理密码>`，本例设为 `password`，请务必改成强密码）。
2. 装中文语言包（OpenWrt 25.12 用 **apk**，不是 opkg）：
   ```sh
   apk update
   apk add luci-i18n-base-zh-cn
   ```
   系统 → 系统 → 语言与样式 → 选 中文(简体)。
3. 改 LAN 段：默认 `192.168.1.1` 通常和家里光猫同段冲突，建议先改成别的段（如 `192.168.5.1`）再接主路由。

### 第 6 步：设为 AP 中继模式（接入主路由）

适用：家里已有主路由（例：`192.168.3.1`），把京东云当 AP 挂上去扩展 WiFi / 有线口。

1. 把 LAN 接口改静态 `192.168.3.250/24`（用 `.250` 高位避开主路由 DHCP 池 100–249），网关 + DNS 都指向 `192.168.3.1`。
2. 关 DHCP 服务（`dhcp.lan.ignore=1`）。
3. 把 **wan 口也桥进 br-lan**（三口全桥，任意口接主路由都行，不怕 MT7621 网口顺序反）。
4. 京东云**任意口**（LAN1 / LAN2 / WAN 皆可）接主路由 LAN 口 → 即以 `192.168.3.250` 挂入家庭网络，管理地址 `http://192.168.3.250/`。

> 一键配置参考脚本：`scripts/configure_ap.py`（SSH 直连改 UCI，需改密码和网段）。

### 第 7 步：开启 WiFi（双频）

本机自带双频无线：`radio0` = 2.4G、`radio1` = 5G。OpenWrt 里**射频开关**（`radioN.disabled`）和 **SSID 接口开关**（`default_radioN.disabled`）是两个独立开关，**两层都要开**才会真正发出信号（只开射频、不开接口层 = 射频亮但搜不到 SSID）。

```sh
# 同时打开射频层 + SSID 接口层
uci set wireless.radio0.disabled='0'
uci set wireless.radio1.disabled='0'
uci set wireless.default_radio0.disabled='0'
uci set wireless.default_radio1.disabled='0'

# 2.4G：Speed / WPA2 / 密码 11.12.13.14.15
uci set wireless.default_radio0.ssid='Speed'
uci set wireless.default_radio0.encryption='psk2'
uci set wireless.default_radio0.key='11.12.13.14.15'

# 5G：Speed-5G / WPA2 / 同密码
uci set wireless.default_radio1.ssid='Speed-5G'
uci set wireless.default_radio1.encryption='psk2'
uci set wireless.default_radio1.key='11.12.13.14.15'

uci commit wireless
wifi reload
```

> 等约 5 秒后，手机应能搜到 `Speed`（2.4G）和 `Speed-5G`（5G）。可在「网络 → 无线」页确认两个接口状态为「已连接 / 已启用」。

### 第 8 步：挂载内置存储（eMMC 大分区）

本机是 MT7621 + **32MB NOR（跑系统）+ 内置 eMMC（约 55GB 闲置数据分区 `/dev/mmcblk0p4`）**。系统本身只用 NOR，那 55GB 完全空着，可格式化成 ext4 挂到 `/mnt/data` 当本地存储用。

```sh
# 1) 装 ext4 内核模块 + 自动挂载工具（OpenWrt 默认不带 ext4 模块）
apk update
apk add kmod-fs-ext4 block-mount
modprobe ext4

# 2) 首次格式化（会清空原京东云数据，仅首次执行一次）
mkfs.ext4 -F -L JD-DATA /dev/mmcblk0p4

# 3) 挂载
mkdir -p /mnt/data
mount /dev/mmcblk0p4 /mnt/data

# 4) 写 fstab，重启自动挂载
uci set fstab.data=mount
uci set fstab.data.target='/mnt/data'
uci set fstab.data.device='/dev/mmcblk0p4'
uci set fstab.data.fstype='ext4'
uci set fstab.data.options='rw,relatime'
uci set fstab.data.enabled='1'
uci set fstab.data.enabled_fsck='0'
uci commit fstab
/etc/init.d/fstab enable
block mount
```

> 🔴 **坑**：OpenWrt 默认**没加载 ext4 内核模块**，直接 `mount` 会报 `Invalid argument`。必须先 `apk add kmod-fs-ext4 block-mount` 并 `modprobe ext4`，否则挂载失败。装完 `df -h /mnt/data` 应能看到约 51GB 可用空间。

---

## 六、常见问题

- **进不去 192.168.1.1？** 先确认电脑 IP 同段、网线插对口、且设备是真进 Breed（断电顶 RESET 10 秒）。Breed 控制台在 `192.168.1.1`；原厂 U-Boot 恢复在 `192.168.68.1`（WAN 蓝口）。
- **后台 IP 到底是哪个？** U-Boot 恢复 = `192.168.68.1`（WAN 蓝口）；Breed = `192.168.1.1`；官方 OpenWrt 默认 = `192.168.1.1`。
- **Breed 报「闪存布局无效」？** 常规模式不认 FIT 格式 sysupgrade，改用「内存启动」中转（方案 A）。
- **刷完进不去、80/443 全关？** 多半刷了 openwrt-ai(Kwrt) 之类极简版（无 LuCI、SSH 密码非页面所写）。换官方 25.12 固件即可。
- **包管理器？** OpenWrt 25.12 用 `apk`（`apk update` / `apk add`），不是老版的 `opkg`。
- **WiFi 开了但搜不到 SSID？** OpenWrt 的「射频开关」和「SSID 接口开关」是两层，必须 `radioN.disabled` 和 `default_radioN.disabled` **都设 0** 才会发信号（见第 7 步）。
- **`mount /dev/mmcblk0p4` 报 `Invalid argument`？** 默认内核没带 ext4 模块，先 `apk add kmod-fs-ext4 block-mount` 并 `modprobe ext4`（见第 8 步）。

---

## 七、脚本说明（`scripts/`）

- `flash_breed.py`：SSH 进过渡固件执行 `mtd write` 刷 Breed（依赖 paramiko）。
- `configure_ap.py`：SSH 进 OpenWrt 改 UCI 配成 AP 中继模式。
- `install_zh.py`：SSH 进 OpenWrt 装中文语言包并设默认语言。

脚本中的密码为本机示例值，请按自己的环境修改后再用。

---

## 八、免责声明

本项目仅供学习交流，刷机有风险，操作前请备份原厂固件。因使用本教程导致的任何设备损坏或数据丢失，作者不承担责任。

import paramiko

HOST, PORT, USER, PW = "192.168.3.250", 22, "root", "password"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PW, timeout=15, look_for_keys=False, allow_agent=False,
          disabled_algorithms={})

def run(cmd, timeout=180):
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return out + err

print("===== [1] opkg update（联网刷新软件源）=====")
print(run("opkg update 2>&1 | tail -25", timeout=120))

print("\n===== [2] 当前已装的语言包 =====")
print(run("opkg list-installed 2>/dev/null | grep -i 'luci-i18n'"))

print("\n===== [3] 安装中文包 luci-i18n-base-zh-cn =====")
print(run("opkg install luci-i18n-base-zh-cn 2>&1 | tail -25", timeout=180))

print("\n===== [4] 设置默认语言为 zh_cn =====")
print(run("uci set luci.main.lang='zh_cn'; uci commit luci; echo 'lang set ->'; uci get luci.main.lang"))

print("\n===== [5] 验证安装结果 =====")
print(run("opkg list-installed 2>/dev/null | grep -i 'luci-i18n-base-zh-cn'; echo '---'; ls /usr/lib/lua/luci/i18n/ 2>/dev/null | grep -i zh"))

c.close()
print("\n[完成] 已尝试安装中文包并设默认语言。")

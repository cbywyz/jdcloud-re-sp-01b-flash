import paramiko, sys

HOST, PORT, USER, PW = "192.168.1.1", 22, "root", "password"
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PW, timeout=10, look_for_keys=False, allow_agent=False)

def run(cmd, silent=False):
    stdin, stdout, stderr = c.exec_command(cmd)
    out = stdout.read().decode("utf-8","replace")
    err = stderr.read().decode("utf-8","replace")
    if not silent:
        print(f"$ {cmd}")
        print(out, end="")
        if err.strip(): print("  [err]", err.strip())
    return out, err

step = sys.argv[1] if len(sys.argv) > 1 else "set"

if step == "set":
    # 验证 br-lan 是否第一个 device section
    name, _ = run("uci get network.@device[0].name", silent=True)
    name = name.strip()
    assert name == "br-lan", f"@device[0] 不是 br-lan，实际={name!r}，中止"
    print(f"[ok] network.@device[0].name = {name}")

    # 1) 把 wan 口并入 br-lan
    run("uci add_list network.@device[0].ports='wan'")

    # 2) 删除独立 wan / wan6 接口（wan 口改作桥接成员）
    run("uci -q del network.wan")
    run("uci -q del network.wan6")

    # 3) LAN 改静态 AP 地址
    run("uci del network.lan.ipaddr")
    run("uci add_list network.lan.ipaddr='192.168.3.250/24'")
    run("uci set network.lan.gateway='192.168.3.1'")
    run("uci set network.lan.dns='192.168.3.1'")
    run("uci -q del network.lan.ip6assign")

    # 4) 关闭 DHCP 服务（AP 不派 IP）
    run("uci set dhcp.lan.ignore='1'")

    # 5) 提交
    run("uci commit network")
    run("uci commit dhcp")

    print("\n===== 提交后预览 network =====")
    run("uci show network")
    print("\n===== 提交后预览 dhcp.lan =====")
    run("uci show dhcp.lan")

elif step == "apply":
    # 重启网络（会使当前 SSH 断开，IP 变为 192.168.3.250）
    print("[*] 重启网络服务 ... (此连接将断开)")
    try:
        stdin, stdout, stderr = c.exec_command("/etc/init.d/network restart", timeout=20)
        print(stdout.read().decode("utf-8","replace"))
    except Exception as e:
        print(f"  (连接已在重启中断开: {type(e).__name__}) -> 正常")
    print("[*] 若已断开即代表 network restart 已触发")

c.close()

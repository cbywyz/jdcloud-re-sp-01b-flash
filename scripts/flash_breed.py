import paramiko, sys

host, port, user = '192.168.68.1', 22, 'root'
pw = sys.argv[1] if len(sys.argv) > 1 else 'password'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port, username=user, password=pw, timeout=20,
                   look_for_keys=False, allow_agent=False, disabled_algorithms={})
except Exception as e:
    print("SSH认证失败:", repr(e))
    sys.exit(2)
print("=== SSH 连接成功 ===")

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    return out, err

out, err = run('id; uname -a; echo "--- breed文件 ---"; ls -la /breed-mt7621-jd-cloud-1.bin 2>&1; echo "--- /proc/mtd ---"; cat /proc/mtd 2>&1')
print(out)
if err.strip():
    print("ERR:", err)

print("=== 写入 Breed 到 Bootloader 分区 ===")
out, err = run('mtd write /breed-mt7621-jd-cloud-1.bin Bootloader 2>&1; echo "MTD_EXIT=$?"')
print(out)
if err.strip():
    print("ERR:", err)

client.close()
print("=== 脚本结束 ===")

#!/usr/bin/env python
"""扒京东云 JDCOS 后台：找本地固件升级 / SSH 开关 / 隐藏 API。
用法: python jdcos_probe.py <设备IP> <后台密码>
"""
import sys, json, re, urllib.request, urllib.parse, http.cookiejar, socket

if len(sys.argv) < 3:
    print('用法: python jdcos_probe.py <IP> <密码>'); sys.exit(1)
HOST = sys.argv[1]
PWD = sys.argv[2]
BASE = f'http://{HOST}'

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.ProxyHandler({}))
op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
                 ('Accept', 'text/html,application/json,*/*')]


def get(path, timeout=8):
    try:
        r = op.open(BASE + path, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)
    except Exception as e:
        return -1, f'{type(e).__name__}: {e}', {}


def post_json(path, data, timeout=10):
    body = json.dumps(data).encode()
    req = urllib.request.Request(BASE + path, data=body,
                                 headers={'Content-Type': 'application/json'})
    try:
        r = op.open(req, timeout=timeout)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return -1, f'{type(e).__name__}: {e}'


print(f'=== 目标 {BASE} ===')

# 1. 首页
print('\n[1] 首页 /')
st, body, hd = get('/')
print(f'    HTTP {st}, {len(body)} bytes')
if body:
    title = re.search(r'<title>(.*?)</title>', body, re.I | re.S)
    print(f'    Title: {title.group(1).strip() if title else "-"}')
    # 提取所有 js / api 路径
    paths = set(re.findall(r'["\'](/[a-zA-Z0-9_\-/\.]+(?:\.js|\.json|/api/[a-zA-Z0-9_\-/]+))["\']', body))
    for p in sorted(paths)[:25]:
        print(f'    引用: {p}')

# 2. 常见管理/升级路径
print('\n[2] 探测常见路径')
cands = ['/api/login', '/cgi-bin/luci', '/login', '/admin', '/index.html',
         '/api/status', '/api/system/info', '/api/device/info', '/api/upgrade',
         '/api/firmware/upgrade', '/upgrade', '/firmware', '/cgi-bin/webproc',
         '/local-upload', '/api/misc/upload', '/api/debug', '/api/ssh',
         '/ubus', '/api/ubus', '/api/config/get', '/hualala']
found = []
for c in cands:
    st, body, hd = get(c, timeout=4)
    mark = ''
    if st == 200:
        mark = '  ← ★200'
        found.append(c)
    elif st not in (-1, 404):
        mark = f'  ← HTTP{st}'
        found.append(c)
    print(f'    {c:<32} {st}{mark}')

# 3. 尝试 ubus（JDCOS 可能基于 OpenWrt）
print('\n[3] 尝试 ubus RPC')
try:
    p = {'jsonrpc': '2.0', 'id': 1, 'method': 'call',
         'params': ['0' * 32, 'session', 'login', {'username': 'root', 'password': PWD}]}
    st, body = post_json('/ubus', p, timeout=6)
    print(f'    /ubus login -> {st}: {body[:200]}')
    if st == 200 and 'ubus_rpc_session' in body:
        print('    ★ ubus 可用！可以直接 UCI 改配置')
        sid = json.loads(body)['result'][1]['ubus_rpc_session']
        for m, a in [('system', 'info'), ('system', 'board')]:
            st2, b2 = post_json('/ubus', {'jsonrpc': '2.0', 'id': 1, 'method': 'call',
                                          'params': [sid, m, a, {}]}, timeout=8)
            print(f'      {m}.{a} -> {b2[:400]}')
except Exception as e:
    print(f'    err: {e}')

print('\n=== 结束 ===')

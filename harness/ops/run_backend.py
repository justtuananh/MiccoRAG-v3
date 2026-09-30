#!/usr/bin/env python3
"""Launch one owned backend from a protected runtime configuration."""
import argparse,json,os,stat,sys,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--port',type=int,required=True);p.add_argument('--check-ready',action='store_true');a=p.parse_args()
if not 1024<=a.port<=65535:p.error('Invalid backend port')
if a.check_ready:
    for _ in range(120):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{a.port}/ready',timeout=2) as response:
                if response.status==200:sys.exit(0)
        except OSError:pass
        time.sleep(1)
    sys.exit('Backend dependencies did not become ready')
if not a.config or a.config.is_symlink():p.error('A protected regular configuration file is required')
info=a.config.stat()
if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid!=os.getuid():p.error('Configuration must be owned by the service user with mode 0600')
config=json.loads(a.config.read_text())
if not isinstance(config,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in config.items()):p.error('Configuration must contain string environment values')
os.environ.update(config)
os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(a.port)])

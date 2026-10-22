from pathlib import Path
import hashlib,json,subprocess,sys,platform
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
from app.core.config import settings
r=Path('/home/micco/MiccoRAG-v3')
files=sorted([p for base in ['micco-backend/backend/app','micco-frontend/src'] for p in (r/base).rglob('*') if p.is_file() and p.suffix in ['.py','.jsx','.js','.css']])
manifest={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
out={'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'source_tree_hash':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'files':manifest,'python':platform.python_version(),'config':{n:getattr(settings,n,None) for n in ['DEBUG','LLM_PROVIDER','LLM_MODEL_FAST','NEXUSRAG_EMBEDDING_MODEL','NEXUSRAG_RERANKER_MODEL','KG_EMBEDDING_PROVIDER','KG_EMBEDDING_MODEL','KG_EMBEDDING_DIMENSION']}}
Path('/tmp/micco-evaluation-20260929/snapshot.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Source manifest created',len(files),'files')

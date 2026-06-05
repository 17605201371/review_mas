
#验证 ModelScope token
from modelscope.hub.api import HubApi
api = HubApi()
api.login('ms-98760c28-bc6f-452f-a3af-8b307f2b2f25')

#模型下载
from modelscope import snapshot_download
model_dir = snapshot_download('zhengshsh/drmas-math-1.5b')
print(f"模型文件实际存放路径是: {model_dir}")

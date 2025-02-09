import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # 可以添加其他模型的API配置
    XUNFEI_API_KEY = os.getenv('XUNFEI_API_KEY')
    BAIDU_API_KEY = os.getenv('BAIDU_API_KEY') 
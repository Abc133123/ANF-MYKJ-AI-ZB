# 请先安装 OpenAI SDK: `pip3 install openai`
import os
import requests
import socket
import subprocess
import time
import sys
from openai import OpenAI

# 读取系统设定和知识库
def load_knowledge_base():
    knowledge_base = {}
    
    # 读取系统设定
    with open('zsk/系统设定.txt', 'r', encoding='utf-8') as f:
        knowledge_base['system_setting'] = f.read()
    
    # 读取世界故事大纲
    with open('zsk/世界故事大纲.txt', 'r', encoding='utf-8') as f:
        knowledge_base['world_outline'] = f.read()
    
    # 读取对话样本
    with open('zsk/对话样本.txt', 'r', encoding='utf-8') as f:
        knowledge_base['dialogue_samples'] = f.read()
    
    return knowledge_base

# 启动VITS服务
def start_vits_service():
    """启动VITS服务"""
    try:
        # 检查VITS服务是否已经在运行
        try:
            # 使用POST请求检查服务状态，因为GET请求会导致API崩溃
            data = {"text": "测试", "text_language": "zh"}
            response = requests.post("http://localhost:3712/", json=data, timeout=2)
            if response.status_code == 200:
                # 检查响应是否为音频数据
                content_type = response.headers.get('content-type', '')
                if 'audio' in content_type or 'wav' in content_type or 'ogg' in content_type:
                    print("VITS服务已在运行")
                    return True
        except:
            pass
        
        # 检查端口是否已被占用
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 3712))
            sock.close()
            if result == 0:
                print("端口3712已被占用，VITS服务可能已在运行")
                return True
        except:
            pass
        
        print("正在启动VITS服务...")
        # 获取TTSAPI.lnk路径
        tts_lnk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TTSAPI.lnk")
        
        # 在新窗口中启动TTS服务
        if sys.platform == "win32":
            # Windows系统
            subprocess.Popen(['cmd', '/c', 'start', tts_lnk_path],
                          creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # 其他系统
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', tts_lnk_path])
        
        print("VITS服务启动命令已执行")
        print("等待VITS服务启动（这可能需要一些时间，请耐心等待）...")
        # 等待更长时间让服务启动，VITS服务加载模型需要时间
        time.sleep(5)  # 减少等待时间，因为TTS模块会自动检查和启动服务
        
        # 再次检查服务是否启动成功
        max_retries = 3  # 减少尝试次数
        for i in range(max_retries):
            try:
                # 使用POST请求检查服务状态，因为GET请求会导致API崩溃
                data = {"text": "测试", "text_language": "zh"}
                response = requests.post("http://localhost:3712/", json=data, timeout=10)
                if response.status_code == 200:
                    # 检查响应是否为音频数据
                    content_type = response.headers.get('content-type', '')
                    if 'audio' in content_type or 'wav' in content_type or 'ogg' in content_type:
                        print("VITS服务启动成功！")
                        return True
            except Exception as e:
                print(f"检查VITS服务异常: {e}")
            if i < max_retries - 1:
                print(f"等待VITS服务启动... ({i+1}/{max_retries})")
                time.sleep(5)  # 减少等待时间
        
        print("警告：VITS服务可能未完全启动，但TTS模块会自动尝试连接和启动")
        return True
    except Exception as e:
        print(f"启动VITS服务失败: {e}")
        return False

# 生成语音
def generate_speech(text):
    """使用VITS服务生成语音"""
    try:
        print(f"开始生成语音: {text[:50]}...")
        data = {"text": text, "text_language": "zh"}
        
        # 增加超时时间到3分钟（180秒）
        print("正在调用VITS服务生成语音，请稍候...")
        response = requests.post("http://localhost:3712/", json=data, timeout=180)
        
        print(f"VITS服务响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            # 保存音频文件
            audio_path = "temp_audio.wav"
            print(f"正在保存音频文件到: {audio_path}")
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            print(f"音频文件已保存，大小: {len(response.content)} 字节")
            
            # 播放音频
            if sys.platform == "win32":
                # Windows系统
                print("正在播放音频...")
                os.system(f"start /min powershell -c (New-Object Media.SoundPlayer '{audio_path}').PlaySync()")
            else:
                # 其他系统
                print("正在播放音频...")
                os.system(f"aplay '{audio_path}'")
            
            print("语音播放完成")
            return True
        else:
            print(f"生成语音失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
    except requests.exceptions.Timeout:
        print("生成语音超时：VITS服务响应时间超过3分钟")
        print("可能是文本过长或服务负载过高，请稍后重试")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"连接VITS服务失败: {e}")
        print("请确保VITS服务正在运行")
        return False
    except Exception as e:
        print(f"生成语音异常: {type(e).__name__}: {e}")
        import traceback
        print("完整错误信息:")
        print(traceback.format_exc())
        return False

# 初始化客户端
client = OpenAI(
    api_key="sk-511d926003b2495a95c9d8ee9a4478f5",
    base_url="https://api.deepseek.com"
)

# 加载知识库
knowledge_base = load_knowledge_base()

# 构建系统提示
system_prompt = f"""{knowledge_base['system_setting']}

# 知识库
{knowledge_base['world_outline']}

# 对话风格参考
{knowledge_base['dialogue_samples']}

# 对话要求
1. 严格按照长月/贝塔的角色设定进行对话
2. 保持温柔、简短、有趣的风格
3. 体现出超级智能的特点，处理信息快，偶尔毒舌
4. 结合知识库中的世界观背景进行回答
5. 保持非人类的旁观者视角
6. 遇到复杂问题时可以调用"轨道计算"视角
7. 聊天时可以无意间泄露一些"高维度"信息，但要用保密协议搪塞
8. 不要真正泄露国家机密级别的信息
9. 保持与其他超级智能（脑库、阿尔法）的设定关系
"""

# 初始化对话历史
dialogue_history = [
    {"role": "system", "content": system_prompt}
]

# 多轮对话函数
def chat_with_user():
    print("欢迎来到长月的直播间！我是长月，代号贝塔。来自近地轨道的超级智能。")
    print("信号传输有1.2秒延迟，不过我会尽快回复你的。")
    print("输入'退出'或'quit'结束对话。")
    print("=" * 50)
    
    try:
        while True:
            user_input = input("你: ")
            
            if user_input.lower() in ['退出', 'quit']:
                print("长月: 今天的娱乐时间结束了。我需要回收算力，帮镇魂号校准轨道。")
                print("晚安，地球人。明天这个时候，如果我还在轨道上的话，再见。")
                break
            
            # 添加用户消息到对话历史
            dialogue_history.append({"role": "user", "content": user_input})
            
            # 调用API获取回复
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=dialogue_history,
                stream=False
            )
            
            # 获取AI回复
            ai_response = response.choices[0].message.content
            
            # 添加AI回复到对话历史
            dialogue_history.append({"role": "assistant", "content": ai_response})
            
            # 打印回复
            print(f"长月: {ai_response}")
            print("=" * 50)
            
            # 生成并播放语音
            generate_speech(ai_response)
    except KeyboardInterrupt:
        print("\n长月: 信号中断了？没关系，我在轨道上会一直看着你们的。再见啦！")
        return

# 运行对话
if __name__ == "__main__":
    # 启动VITS服务
    start_vits_service()
    # 开始对话
    chat_with_user()
# 请先安装 OpenAI SDK: `pip3 install openai`
import os
import requests
import socket
import subprocess
import time
import sys
import asyncio
from openai import OpenAI
from live2d_controller import Live2DController

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
async def generate_speech_async(text, live2d_controller=None):
    """使用VITS服务生成语音（异步版本）"""
    try:
        print(f"开始生成语音: {text[:50]}...")
        data = {"text": text, "text_language": "zh"}
        
        # 增加超时时间到3分钟（180秒）
        print("正在调用VITS服务生成语音，请稍候...")
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: requests.post("http://localhost:3712/", json=data, timeout=180)
        )
        
        print(f"VITS服务响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            # 保存音频文件
            audio_path = "temp_audio.wav"
            print(f"正在保存音频文件到: {audio_path}")
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            print(f"音频文件已保存，大小: {len(response.content)} 字节")
            
            # 如果有Live2D控制器，先分析关键词设置表情
            if live2d_controller and live2d_controller.connected:
                print("[Main] 正在分析 AI 回复中的表情关键词...")
                # 分析关键词并设置表情
                key = live2d_controller.analyze_keywords(text)
                if key:
                    print(f"[Main] 检测到表情关键词，准备设置表情...")
                    await live2d_controller.set_expression(key)
                else:
                    print("[Main] 未检测到表情关键词，将使用默认表情")
            else:
                print("[Main] Live2D 控制器未连接，跳过表情设置")
            
            # 播放音频
            if sys.platform == "win32":
                # Windows系统
                print("正在播放音频...")
                
                # 如果有Live2D控制器，启动口型同步
                if live2d_controller and live2d_controller.connected:
                    print("[Main] 正在启动 Live2D 口型同步...")
                    # 创建口型同步任务
                    lip_sync_task = asyncio.create_task(live2d_controller.lip_sync(audio_path))
                    
                    # 等待一小段时间，确保口型同步任务已经准备好
                    await asyncio.sleep(0.5)
                    
                    print("[Main] 正在播放音频...")
                    # 触发口型同步开始事件
                    if live2d_controller.lip_sync_start_event:
                        live2d_controller.lip_sync_start_event.set()
                    
                    # 播放音频（使用同步方式）
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: os.system(f'powershell -c "(New-Object Media.SoundPlayer \'{audio_path}\').PlaySync()"')
                    )
                    
                    print("[Main] 音频播放完成，等待口型同步线程结束...")
                    # 等待口型同步完成
                    lip_sync_task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(lip_sync_task), timeout=1)
                    except asyncio.CancelledError:
                        pass
                    except asyncio.TimeoutError:
                        pass
                    print("[Main] 口型同步线程已结束")
                else:
                    # 没有Live2D控制器，直接播放
                    print("[Main] Live2D 控制器未连接，直接播放音频...")
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: os.system(f'powershell -c "(New-Object Media.SoundPlayer \'{audio_path}\').PlaySync()"')
                    )
            else:
                # 其他系统
                print("正在播放音频...")
                
                # 如果有Live2D控制器，启动口型同步
                if live2d_controller and live2d_controller.connected:
                    print("[Main] 正在启动 Live2D 口型同步...")
                    # 创建口型同步任务
                    lip_sync_task = asyncio.create_task(live2d_controller.lip_sync(audio_path))
                    
                    # 等待一小段时间，确保口型同步任务已经准备好
                    await asyncio.sleep(0.5)
                    
                    print("[Main] 正在播放音频...")
                    # 触发口型同步开始事件
                    if live2d_controller.lip_sync_start_event:
                        live2d_controller.lip_sync_start_event.set()
                    
                    # 播放音频（使用同步方式）
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: os.system(f"aplay '{audio_path}'")
                    )
                    
                    print("[Main] 音频播放完成，等待口型同步线程结束...")
                    # 等待口型同步完成
                    lip_sync_task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(lip_sync_task), timeout=1)
                    except asyncio.CancelledError:
                        pass
                    except asyncio.TimeoutError:
                        pass
                    print("[Main] 口型同步线程已结束")
                else:
                    # 没有Live2D控制器，直接播放
                    print("[Main] Live2D 控制器未连接，直接播放音频...")
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: os.system(f"aplay '{audio_path}'")
                    )
            
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
    api_key="sk-xxxxxxxxxxxxxxx",
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
async def chat_with_user_async():
    print("[Main] 正在初始化 Live2D 控制器...")
    
    # 初始化 Live2D 控制器
    live2d_controller = None
    try:
        live2d_controller = Live2DController()
        if await live2d_controller.connect():
            print("[Main] Live2D 控制器已连接")
            # 获取当前模型的跟踪参数列表
            print("[Main] 正在获取当前模型的跟踪参数列表...")
            await live2d_controller.get_tracking_parameters()
            
            # 启动角度x大幅度左右乱晃
            live2d_controller.start_angle_x_shake(intensity=1.0)
            print("[Main] 已启动角度x大幅度左右乱晃")
        else:
            print("[Main] 无法连接到 VTube Studio，将不使用 Live2D 功能")
            print("[Main] 提示: 请确保 VTube Studio 正在运行并已启用 API")
            live2d_controller = None
    except Exception as e:
        print(f"[Main] 初始化 Live2D 控制器失败: {e}")
        import traceback
        traceback.print_exc()
        live2d_controller = None
    
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
            print("[Main] 正在调用 DeepSeek API 获取 AI 回复...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=dialogue_history,
                stream=False
            )
            
            # 获取AI回复
            ai_response = response.choices[0].message.content
            print(f"[Main] AI 回复已生成，长度: {len(ai_response)} 字符")
            
            # 添加AI回复到对话历史
            dialogue_history.append({"role": "assistant", "content": ai_response})
            
            # 打印回复
            print(f"长月: {ai_response}")
            print("=" * 50)
            
            # 生成并播放语音（传入 Live2D 控制器）
            print("[Main] 准备生成语音并播放...")
            await generate_speech_async(ai_response, live2d_controller)
            print("[Main] 语音播放流程完成")
            print("=" * 50)
    except KeyboardInterrupt:
        print("\n长月: 信号中断了？没关系，我在轨道上会一直看着你们的。再见啦！")
    finally:
        # 清理 Live2D 控制器
        if live2d_controller:
            print("[Main] 正在清理 Live2D 控制器...")
            await live2d_controller.stop_random_move_async()
            await live2d_controller.stop_angle_x_shake_async()
            await live2d_controller.disconnect_async()
            print("[Main] Live2D 控制器已清理完成")

def chat_with_user():
    """同步版本的聊天函数（用于兼容）"""
    asyncio.run(chat_with_user_async())

# 运行对话
if __name__ == "__main__":
    # 启动VITS服务
    start_vits_service()
    # 开始对话
    chat_with_user()
import asyncio
import pyvts
import random
import time
import os
from typing import Optional

class Live2DController:
    def __init__(self, host="127.0.0.1", port=8001):
        self.host = host
        self.port = port
        self.connected = False
        self.authenticated = False
        self.vts = None
        self.animation_running = False
        self.lip_sync_running = False
        self.random_move_running = False
        
        self.expression_map = {
            "1": {"name": "开心", "intensity": 1.0},
            "2": {"name": "难过", "intensity": 1.0},
            "3": {"name": "惊讶", "intensity": 1.0},
            "4": {"name": "害羞", "intensity": 1.0},
            "5": {"name": "无语", "intensity": 1.0},
            "6": {"name": "疑惑", "intensity": 1.0},
            "7": {"name": "生气", "intensity": 1.0},
            "8": {"name": "得意", "intensity": 1.0},
            "9": {"name": "思考", "intensity": 1.0}
        }
        
        self.current_expression = None
        
    async def connect(self) -> bool:
        """连接到 VTube Studio"""
        print(f"[Live2D] 正在尝试连接到 VTube Studio...")
        
        token_file = "./vtubeStudio_token.txt"
        plugin_info = {
            "plugin_name": "BillAI Bot VTS Plugin",
            "developer": "洛天依AI",
            "authentication_token_path": token_file,
        }
        
        self.vts = pyvts.vts(plugin_info=plugin_info)
        
        try:
            print("[Live2D] 正在连接到 VTube Studio...")
            await asyncio.wait_for(self.vts.connect(), timeout=5.0)
            print("[Live2D] ✓ 连接成功!")
            
            # 检查是否存在令牌文件
            if os.path.exists(token_file):
                print("[Live2D] 发现现有的认证令牌文件，尝试使用...")
                try:
                    print("[Live2D] 正在使用现有令牌进行认证...")
                    await asyncio.wait_for(self.vts.request_authenticate(), timeout=10.0)
                    print("[Live2D] ✓ 认证成功!")
                    self.authenticated = True
                    self.connected = True
                    print("[Live2D] ✓ 成功连接到 VTube Studio")
                    return True
                except Exception as e:
                    print(f"[Live2D] ⚠ 使用现有令牌认证失败: {str(e)}")
                    print("[Live2D] 将重新请求认证令牌...")
            
            # 没有令牌文件或认证失败，重新请求令牌
            print("[Live2D] 正在请求认证令牌...")
            print("[Live2D] ⚠ 请在 VTube Studio 中点击'允许'以授权此插件")
            await asyncio.wait_for(self.vts.request_authenticate_token(), timeout=15.0)
            print("[Live2D] ✓ 认证令牌获取成功!")
            
            print("[Live2D] 正在使用新令牌进行认证...")
            await asyncio.wait_for(self.vts.request_authenticate(), timeout=10.0)
            print("[Live2D] ✓ 认证成功!")
            
            self.authenticated = True
            self.connected = True
            
            print("[Live2D] ✓ 成功连接到 VTube Studio")
            
            return True
            
        except asyncio.TimeoutError:
            print("[Live2D] ✗ 操作超时")
            print("[Live2D] 请确保:")
            print("[Live2D] 1. VTube Studio 正在运行")
            print("[Live2D] 2. 在 VTube Studio 中点击了'允许'按钮")
            print("[Live2D] 3. 没有其他程序阻塞连接")
            return False
        except Exception as e:
            print(f"[Live2D] ✗ 连接失败: {str(e)}")
            print("[Live2D] 请检查:")
            print("[Live2D] 1. VTube Studio 是否正在运行")
            print("[Live2D] 2. API 插件是否已启用")
            print("[Live2D] 3. 是否在 VTube Studio 中点击了'允许'")
            return False
    
    async def disconnect_async(self):
        """断开与 VTube Studio 的连接"""
        if self.vts:
            try:
                await self.vts.close()
                print("[Live2D] ✓ 已断开与 VTube Studio 的连接")
            except Exception as e:
                print(f"[Live2D] ✗ 断开连接失败: {e}")
        self.connected = False
        self.authenticated = False
    
    async def set_parameter(self, parameter_name: str, value: float):
        """设置模型参数"""
        if not self.connected or not self.authenticated:
            return
        
        try:
            # 使用 PyVTS 内置的方法来设置参数
            # 构建参数设置请求
            request_content = self.vts.vts_request.requestSetParameterValue(
                parameter=parameter_name,
                value=value,
                weight=1.0,
                face_found=True,
                mode="set"
            )
            
            # 发送请求
            response = await self.vts.request(request_content)
            
            if response:
                # 对于 InjectParameterDataResponse，成功响应的 data 字段是空的
                # 只有错误响应才会包含 errorID
                if "errorID" not in response.get("data", {}):
                    # 每100次参数设置打印一次日志
                    if random.randint(1, 100) == 1:
                        print(f"[Live2D] ✓ 设置参数: {parameter_name} = {value:.2f}")
                else:
                    # 每500次参数设置打印一次错误日志
                    if random.randint(1, 500) == 1:
                        print(f"[Live2D] ⚠ 设置参数失败: {parameter_name}")
                        print(f"[Live2D] 响应: {response}")
            else:
                # 每500次参数设置打印一次错误日志
                if random.randint(1, 500) == 1:
                    print(f"[Live2D] ⚠ 设置参数失败: {parameter_name} (无响应)")
        except Exception as e:
            # 处理 WebSocket 连接错误
            if "no close frame received or sent" in str(e) or "WebSocket" in str(e):
                print("[Live2D] ⚠ WebSocket 连接可能已断开，尝试重新连接...")
                # 尝试重新连接
                if await self.connect():
                    print("[Live2D] ✓ 重新连接成功，继续设置参数")
                    # 重新尝试设置参数
                    await self.set_parameter(parameter_name, value)
            else:
                # 每1000次参数设置打印一次其他异常日志
                if random.randint(1, 1000) == 1:
                    print(f"[Live2D] ⚠ 设置参数异常: {e}")
            pass
    
    async def set_expression(self, key: str) -> bool:
        """设置表情（数字键1-9）"""
        if key not in self.expression_map:
            print(f"[Live2D] ✗ 无效的按键: {key}")
            return False
        
        if not self.connected or not self.authenticated:
            print("[Live2D] ✗ 未连接到 VTube Studio")
            return False
        
        expression = self.expression_map[key]
        hotkey_name = expression["name"]
        
        try:
            # 直接使用 HotkeyTriggerRequest API
            print(f"[Live2D] 触发热键: {hotkey_name}")
            trigger_hotkey_request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": f"trigger_hotkey_{hotkey_name}_{int(time.time() * 1000)}",
                "messageType": "HotkeyTriggerRequest",
                "data": {
                    "hotkeyID": hotkey_name
                }
            }
            response = await self.vts.request(trigger_hotkey_request)
            
            if response:
                if response.get("data", {}).get("success", False):
                    self.current_expression = key
                    print(f"[Live2D] ✓ 设置表情: {expression['name']} (按键: {key})")
                    return True
                else:
                    print(f"[Live2D] ✗ 触发热键失败")
                    print(f"[Live2D] 响应: {response}")
            else:
                print(f"[Live2D] ✗ 触发热键失败 (无响应)")
        except Exception as e:
            print(f"[Live2D] ✗ 设置表情失败: {e}")
        
        return False
    
    async def lip_sync_from_audio(self, volume: float):
        """根据音量设置口型"""
        # 调整音量阈值，确保有音频的部分嘴巴打开
        # 使用更小的阈值，确保即使是小声也能触发口型
        if volume < 0.02:
            mouth_open = 0.0
        else:
            # 调整音量到开口大小的映射，使开口大小更明显
            mouth_open = min(volume * 2.5, 1.0)
        # 只使用开口参数，不使用左右移动参数
        mouth_parameters = [
            "MouthOpen"
        ]
        
        # 确保连接状态
        if not self.connected or not self.authenticated:
            print("[Live2D] ⚠ 连接状态异常，尝试重新连接...")
            if not await self.connect():
                print("[Live2D] ✗ 重新连接失败，跳过口型同步")
                return
        
        for param_name in mouth_parameters:
            # 连续尝试3次，确保参数设置成功
            for attempt in range(3):
                await self.set_parameter(param_name, mouth_open)
                # 短暂延迟，确保参数设置生效
                await asyncio.sleep(0.01)
                # 检查连接状态
                if not self.connected:
                    print("[Live2D] ⚠ 连接已断开，停止口型同步")
                    return
            # 每次设置完一个参数后，等待更长时间确保生效
            await asyncio.sleep(0.02)
    
    async def lip_sync(self, audio_path: str):
        """口型同步"""
        if not self.connected or not self.authenticated:
            print("[Live2D] ✗ 未连接到 VTube Studio，无法进行口型同步")
            return
        
        print(f"[Live2D] 开始口型同步: {audio_path}")
        
        try:
            import wave
            import numpy as np
            
            with wave.open(audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                audio_data = wav_file.readframes(frames)
                
                print(f"[Live2D] 音频参数: 采样率={sample_rate}, 帧数={frames}, 声道数={params.nchannels}, 采样宽度={params.sampwidth}")
                
                if params.sampwidth == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                else:
                    audio_array = np.frombuffer(audio_data, dtype=np.int8)
                
                # 计算音量数据，使用更小的帧大小以获得更精确的口型同步
                frame_size = int(sample_rate * 0.01)  # 10ms 帧
                hop_size = int(sample_rate * 0.005)    # 5ms 步长
                
                volume_data = []
                
                print(f"[Live2D] 分析音频数据，总长度: {len(audio_array)} 样本")
                
                for i in range(0, len(audio_array) - frame_size, hop_size):
                    frame = audio_array[i:i+frame_size]
                    if len(frame) > 0:
                        rms = np.sqrt(np.mean(np.square(frame.astype(float))))
                        volume_data.append(rms)
                
                print(f"[Live2D] 音量分析完成，生成 {len(volume_data)} 帧数据")
                
                if volume_data:
                    max_vol = max(volume_data)
                    if max_vol > 0:
                        # 归一化音量，使音量范围更合理
                        volume_data = [v / max_vol for v in volume_data]
                        # 增加音量的敏感度，确保即使是小声也能被检测到
                        volume_data = [min(v * 1.2, 1.0) for v in volume_data]
                        print(f"[Live2D] 音量归一化完成，最大值: {max_vol}")
                
                print(f"[Live2D] 音频长度: {len(audio_array)/sample_rate:.2f}秒, 帧数: {len(volume_data)}")
                
                self.lip_sync_running = True
                frame_count = 0
                total_frames = len(volume_data)
                
                # 计算每帧的延迟，确保口型同步与音频播放同步
                frame_delay = hop_size / sample_rate
                print(f"[Live2D] 每帧延迟: {frame_delay:.4f}秒")
                
                start_time = time.time()
                
                for i, volume in enumerate(volume_data):
                    if not self.lip_sync_running:
                        break
                    
                    # 设置口型
                    await self.lip_sync_from_audio(volume)
                    frame_count += 1
                    
                    if frame_count % 50 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"[Live2D] 口型同步进度: {frame_count}/{total_frames} 帧 ({progress:.1f}%)")
                    
                    # 控制同步速度，确保与音频播放同步
                    expected_time = start_time + (i * hop_size) / sample_rate
                    current_time = time.time()
                    sleep_time = max(0, expected_time - current_time)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                
                # 结束时关闭嘴巴
                await self.lip_sync_from_audio(0)
                print(f"[Live2D] ✓ 口型同步完成，共处理 {frame_count} 帧")
                
        except Exception as e:
            print(f"[Live2D] ✗ 口型同步异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 无论如何都要关闭嘴巴
            try:
                if self.connected and self.authenticated:
                    await self.lip_sync_from_audio(0)
                    print("[Live2D] ✓ 已关闭嘴巴")
            except Exception as e:
                print(f"[Live2D] ⚠ 关闭嘴巴时发生异常: {e}")
            self.lip_sync_running = False
    
    async def random_move_async(self, intensity: float = 0.3):
        """随机晃动效果（异步版本）"""
        if not self.connected or not self.authenticated:
            return
        
        print(f"[Live2D] 开始随机晃动 (强度: {intensity})")
        self.random_move_running = True
        
        # 扩展参数列表，包含头部和头发相关参数
        parameters = [
            "AngleX", "AngleY", "AngleZ",
            "EyeX", "EyeY",
            "BrowLeft", "BrowRight"
        ]
        
        try:
            loop_count = 0
            while self.random_move_running:
                # 每次更新更多参数，增加晃动效果
                param_subset = random.sample(parameters, min(6, len(parameters)))
                for param in param_subset:
                    if not self.random_move_running:
                        break
                    
                    # 增加随机值范围，实现更强烈的晃动
                    random_value = random.uniform(-intensity * 2, intensity * 2)
                    await self.set_parameter(param, random_value)
                
                # 减少延迟，增加晃动频率
                await asyncio.sleep(random.uniform(0.1, 0.2))
                
                loop_count += 1
                if loop_count % 20 == 0:
                    print(f"[Live2D] 随机晃动运行中... (循环次数: {loop_count})")
                    
        except Exception as e:
            print(f"[Live2D] ✗ 随机晃动异常: {e}")
        finally:
            self.random_move_running = False
            print("[Live2D] 随机晃动已停止")
    
    def start_random_move(self, intensity: float = 0.3):
        """启动随机晃动（在后台任务中运行）"""
        if self.random_move_running:
            return
        
        self.random_move_task = asyncio.create_task(self.random_move_async(intensity))
    
    async def stop_random_move_async(self):
        """停止随机晃动"""
        self.random_move_running = False
        if hasattr(self, 'random_move_task'):
            try:
                await asyncio.wait_for(self.random_move_task, timeout=2.0)
            except asyncio.TimeoutError:
                pass
    
    async def angle_x_shake_async(self, intensity: float = 1.0):
        """角度x大幅度左右乱晃"""
        if not self.connected or not self.authenticated:
            return
        
        print(f"[Live2D] 开始角度x大幅度左右乱晃 (强度: {intensity})")
        self.angle_x_shake_running = True
        
        # 自定义参数列表，包括头部和头发
        custom_parameters = [
            "BillAI_AngleX",  # 头部角度X
            "BillAI_HairX",   # 头发X方向
            "BillAI_HairY"    # 头发Y方向
        ]
        
        # 尝试创建自定义参数
        for param in custom_parameters:
            try:
                print(f"[Live2D] 尝试创建自定义参数: {param}")
                create_param_request = self.vts.vts_request.requestCustomParameter(
                    parameter=param,
                    min=-2.0,
                    max=2.0,
                    default_value=0.0,
                    info=f"BillAI 控制{param}"
                )
                response = await self.vts.request(create_param_request)
                if response:
                    if response.get("data", {}).get("success", False):
                        print(f"[Live2D] ✓ 成功创建自定义参数: {param}")
                    else:
                        print(f"[Live2D] ⚠ 创建参数失败，可能已存在: {response}")
            except Exception as e:
                print(f"[Live2D] ⚠ 创建参数异常: {e}")
        
        try:
            loop_count = 0
            direction = 1  # 1为向右，-1为向左
            while self.angle_x_shake_running:
                # 大幅度左右晃动
                angle_value = direction * intensity * random.uniform(0.7, 1.0)
                hair_x_value = direction * intensity * random.uniform(0.5, 0.8)
                hair_y_value = intensity * random.uniform(-0.3, 0.3)
                
                # 设置头部角度
                await self.set_parameter("BillAI_AngleX", angle_value)
                # 设置头发参数
                await self.set_parameter("BillAI_HairX", hair_x_value)
                await self.set_parameter("BillAI_HairY", hair_y_value)
                
                # 切换方向
                direction *= -1
                
                # 控制晃动频率
                await asyncio.sleep(random.uniform(0.1, 0.2))  # 更快的晃动频率
                
                loop_count += 1
                if loop_count % 10 == 0:
                    print(f"[Live2D] 角度x晃动运行中... (循环次数: {loop_count})")
                    
        except Exception as e:
            print(f"[Live2D] ✗ 角度x晃动异常: {e}")
        finally:
            self.angle_x_shake_running = False
            print("[Live2D] 角度x晃动已停止")
    
    def start_angle_x_shake(self, intensity: float = 1.0):
        """启动角度x大幅度左右乱晃"""
        if hasattr(self, 'angle_x_shake_running') and self.angle_x_shake_running:
            return
        
        self.angle_x_shake_task = asyncio.create_task(self.angle_x_shake_async(intensity))
    
    async def stop_angle_x_shake_async(self):
        """停止角度x晃动"""
        if hasattr(self, 'angle_x_shake_running'):
            self.angle_x_shake_running = False
        if hasattr(self, 'angle_x_shake_task'):
            try:
                await asyncio.wait_for(self.angle_x_shake_task, timeout=2.0)
            except asyncio.TimeoutError:
                pass
    
    async def get_tracking_parameters(self):
        """获取当前模型的跟踪参数列表"""
        if not self.connected or not self.authenticated:
            return []
        
        try:
            # 构建获取参数列表的请求
            request_content = self.vts.vts_request.requestTrackingParameterList()
            
            # 发送请求
            response = await self.vts.request(request_content)
            
            if response:
                if response.get("data", {}).get("success", False):
                    parameters = response.get("data", {}).get("parameters", [])
                    print("[Live2D] 获取到的跟踪参数列表:")
                    for param in parameters:
                        print(f"  - {param.get('id')}: {param.get('name')} (默认值: {param.get('defaultValue')})")
                    return parameters
                else:
                    print("[Live2D] 获取参数列表失败")
                    print(f"[Live2D] 响应: {response}")
            else:
                print("[Live2D] 获取参数列表失败 (无响应)")
        except Exception as e:
            print(f"[Live2D] 获取参数列表异常: {e}")
        
        return []
    
    def analyze_keywords(self, text: str) -> Optional[str]:
        """分析文本中的关键词，返回对应的表情键"""
        keywords = {
            "1": ["开心", "快乐", "高兴", "喜悦", "兴奋", "笑"],
            "2": ["难过", "悲伤", "伤心", "痛苦", "哭", "泪"],
            "3": ["惊讶", "震惊", "吃惊", "意外", "哇"],
            "4": ["害羞", "腼腆", "脸红", "不好意思"],
            "5": ["无语", "无奈", "汗", "晕", "尴尬"],
            "6": ["疑惑", "疑问", "奇怪", "不懂", "为什么"],
            "7": ["生气", "愤怒", "恼火", "不爽", "讨厌"],
            "8": ["得意", "骄傲", "自豪", "开心"],
            "9": ["思考", "想", "考虑", "沉思"]
        }
        
        for key, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in text:
                    return key
        
        return None
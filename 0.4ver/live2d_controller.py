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
        
        # 口型同步事件，用于与音频播放同步
        self.lip_sync_start_event = None
        
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
            print("[Live2D] ⚠ 连接状态异常，跳过口型同步")
            return
        
        # 简化参数设置，减少重试次数
        for param_name in mouth_parameters:
            try:
                await self.set_parameter(param_name, mouth_open)
            except Exception as e:
                # 只在发生严重错误时打印日志
                if "WebSocket" in str(e) or "connection" in str(e).lower():
                    print(f"[Live2D] ⚠ 连接错误: {e}")
                pass
    
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
                
                # 创建同步事件
                self.lip_sync_start_event = asyncio.Event()
                
                # 等待音频播放开始信号
                print("[Live2D] 等待音频播放开始...")
                await self.lip_sync_start_event.wait()
                print("[Live2D] 收到音频播放开始信号，开始口型同步")
                
                # 记录开始时间（在收到信号后）
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
            self.lip_sync_start_event = None
    
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
        """角度x大幅度左右乱晃 - 柔美弹性版本（增强左右晃动）"""
        if not self.connected or not self.authenticated:
            return
        
        print(f"[Live2D] 开始柔美弹性晃动 (强度: {intensity})")
        self.angle_x_shake_running = True
        
        # 使用模型实际支持的参数
        # 从模型配置文件中获取的实际参数名称
        shake_parameters = {
            "FaceAngleX": {"range": (-25.0, 25.0), "output_range": (-30.0, 30.0)},
            "FaceAngleY": {"range": (-25.0, 25.0), "output_range": (-30.0, 30.0)},
            "FaceAngleZ": {"range": (-25.0, 25.0), "output_range": (-30.0, 30.0)}
        }
        
        # 缓动函数 - 让运动更加自然
        def ease_in_out_sine(t):
            return -(math.cos(math.pi * t) - 1) / 2
        
        def ease_out_elastic(t):
            c4 = (2 * math.pi) / 3
            if t == 0:
                return 0
            elif t == 1:
                return 1
            else:
                return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
        
        try:
            import math
            
            loop_count = 0
            start_time = time.time()
            
            # 平滑插值函数 - 惰性过渡
            def smooth_lerp(current, target, factor):
                return current + (target - current) * factor
            
            # 随机数列表 - 保存3个目标值
            def generate_random_targets(amplitude):
                return [
                    random.uniform(-amplitude, amplitude),
                    random.uniform(-amplitude, amplitude),
                    random.uniform(-amplitude, amplitude)
                ]
            
            # 初始化当前值和目标值
            current_x = 0.0
            current_y = 0.0
            current_z = 0.0
            
            # 目标值列表（3个）- 速度加快2倍，幅度也增大2倍补偿
            x_targets = generate_random_targets(30.0)
            y_targets = generate_random_targets(12.0)
            z_targets = generate_random_targets(32.0)
            
            # 当前目标索引
            x_target_index = 0
            y_target_index = 0
            z_target_index = 0
            
            # 过渡进度（0-1）
            x_progress = 0.0
            y_progress = 0.0
            z_progress = 0.0
            
            # 惯性系数（越小越慢，惰性越大）
            x_inertia = 0.03
            y_inertia = 0.04
            z_inertia = 0.03
            
            # 过渡速度（加快2倍）
            x_transition_speed = 0.04
            y_transition_speed = 0.05
            z_transition_speed = 0.04
            
            # 添加微小抖动的函数
            def add_micro_jitter(value, intensity):
                return value + random.uniform(-0.3, 0.3) * intensity
            
            print(f"[Live2D] 开始连贯晃动 - X目标:{x_targets}, Y目标:{y_targets}, Z目标:{z_targets}")
            
            while self.angle_x_shake_running:
                elapsed = time.time() - start_time
                
                # X轴：平滑过渡到目标值
                target_x = x_targets[x_target_index]
                x_progress += x_transition_speed
                
                if x_progress >= 1.0:
                    # 到达当前目标，切换到下一个（不重置current_x，保持连贯）
                    x_progress = 0.0
                    x_target_index = (x_target_index + 1) % 3
                    # 生成新的随机目标
                    x_targets[x_target_index] = random.uniform(-30.0, 30.0) * intensity
                
                # 使用 ease-in-out 缓动函数让过渡更自然
                ease_t = x_progress * x_progress * (3 - 2 * x_progress)
                target_x_with_ease = current_x + (x_targets[x_target_index] - current_x) * ease_t
                
                # 应用惯性平滑
                current_x = smooth_lerp(current_x, target_x_with_ease, x_inertia)
                
                # Y轴：平滑过渡到目标值
                target_y = y_targets[y_target_index]
                y_progress += y_transition_speed
                
                if y_progress >= 1.0:
                    y_progress = 0.0
                    y_target_index = (y_target_index + 1) % 3
                    y_targets[y_target_index] = random.uniform(-12.0, 12.0) * intensity
                
                ease_t_y = y_progress * y_progress * (3 - 2 * y_progress)
                target_y_with_ease = current_y + (y_targets[y_target_index] - current_y) * ease_t_y
                current_y = smooth_lerp(current_y, target_y_with_ease, y_inertia)
                
                # Z轴：平滑过渡到目标值
                target_z = z_targets[z_target_index]
                z_progress += z_transition_speed
                
                if z_progress >= 1.0:
                    z_progress = 0.0
                    z_target_index = (z_target_index + 1) % 3
                    z_targets[z_target_index] = random.uniform(-32.0, 32.0) * intensity
                
                ease_t_z = z_progress * z_progress * (3 - 2 * z_progress)
                target_z_with_ease = current_z + (z_targets[z_target_index] - current_z) * ease_t_z
                current_z = smooth_lerp(current_z, target_z_with_ease, z_inertia)
                
                # 添加微小自然抖动
                total_x_shake = add_micro_jitter(current_x, intensity)
                total_y_shake = add_micro_jitter(current_y, intensity)
                total_z_shake = add_micro_jitter(current_z, intensity)
                
                # 设置头部角度参数
                await self.set_parameter("FaceAngleX", total_x_shake)
                await self.set_parameter("FaceAngleY", total_y_shake)
                await self.set_parameter("FaceAngleZ", total_z_shake)
                
                # 偶尔调整过渡速度，增加变化
                if random.random() < 0.01:
                    x_transition_speed = random.uniform(0.03, 0.05)
                    y_transition_speed = random.uniform(0.04, 0.06)
                    z_transition_speed = random.uniform(0.03, 0.05)
                
                # 控制更新频率（加快）
                await asyncio.sleep(random.uniform(0.03, 0.05))
                
                loop_count += 1
                if loop_count % 20 == 0:
                    print(f"[Live2D] 连贯晃动运行中... (循环:{loop_count}, X:{total_x_shake:.1f}, Y:{total_y_shake:.1f}, Z:{total_z_shake:.1f})")
                    print(f"[Live2D] 目标值 - X:{x_targets}, Y:{y_targets}, Z:{z_targets}")
                    
        except Exception as e:
            print(f"[Live2D] ✗ 角度x晃动异常: {e}")
        finally:
            self.angle_x_shake_running = False
            print("[Live2D] 柔美晃动已停止")
    
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
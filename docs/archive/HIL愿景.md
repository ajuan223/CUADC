                                                                                                    
● 那就选 HIL，这条路对你更合适，而且可以不刷 SoH 固件。                                      
                                                                                                    
  先给结论                                                                                          
                                                                                                    
  对 CUAV X7+，你现在最合理的目标是：                                                               
                                                                                                    
  - 飞控上跑 正常 ArduPlane 固件                                                                    
  - 飞控保留你真实参数                                                                              
  - 外部主机负责“物理世界 / 传感器”                                                                 
  - Striker 连接的对象改成 真实 X7+ 的 MAVLink 串口/UDP                                             
  - 最终形成：                                                                                      
                                                                                                    
  外部模拟器 ⇄ X7+ (HIL) ⇄ Striker                                                                  
                                                                                                    
  这比纯 SITL 更接近你要验证的东西：                                                                
  - 真飞控硬件    
  - 真参数                                                                                          
  - 真调度/真驱动栈
  - 真 MAVLink 通路                                                                                 
                                                                                                    
  ---
  你现在要接受的一个现实                                                                            
                                                                                                    
  如果你 不刷 SoH，那就做不到：
                                                                                                    
  - “飞控自己同时扮演传感器 + 物理世界 + 自动驾驶”                                                  
                                                                                                    
  也就是：                                                                                          
  裸飞控无法只靠自己 MCU 完成完整类 SITL 世界模拟。
                                                                                                    
  所以 HIL 的本质就是：                                                                             
                                                                                                    
  - 飞控负责 autopilot                                                                              
  - 外部电脑负责 simulation
                                                                                                    
  这正是你现在说的：                                                                                
                                                                                                    
  ▎ 更接近“真实飞控 + 外部物理模拟”                                                                 
                  
  对，这就是正确方向。                                                                              
                  
  ---                                                                                               
  HIL 模式里，ArduPilot 关键点
                                                                                                    
  官方文档确认了两件事：
                                                                                                    
  - HIL_PROTOCOL_MAVLINK
  - HIL_MODE_SENSORS                                                                                
                                                                                                    
  也就是说，推荐路线是 MAVLink HIL，由外部模拟器向飞控注入 HIL 数据。                               
                                                                                                    
  概念上：                                                                                          
                  
  - 飞控输出舵量/油门/控制意图                                                                      
  - 模拟器根据这些输出更新飞机状态
  - 模拟器再把“虚拟 IMU/GPS/气压/姿态”等喂回飞控                                                    
                                                                                                    
  这是一个闭环。                                                                                    
                                                                                                    
  ---             
  你的推荐系统结构
                                                                                                    
  我建议你这样搭：
                                                                                                    
  结构 A：最实用  
                                                                                                    
  一台仿真主机 + 一块 X7+ + Striker                                                                 
  
  - X7+                                                                                             
    - 跑正常 ArduPlane
    - 导入你的真实参数                                                                              
    - 开 HIL 相关参数                                                                               
  - 仿真主机                                                                                        
    - 跑 HIL 模拟器 / HIL bridge                                                                    
    - 给飞控注入传感器/姿态/GPS                                                                     
  - Striker                                                                                         
    - 连 X7+ 的 MAVLink                                                                             
    - 像连真机一样工作                                                                              
                                                                                                    
  ---                                                                                               
  接线建议                                                                                          
                                                                                                    
  最小闭环接线    
                                                                                                    
  你至少需要：                                                                                      
                                                                                                    
  1) X7+ ↔ 仿真主机                                                                                 
                  
  通常走：                                                                                          
  - USB           
  或                                                                                                
  - TELEM1/TELEM2 串口 + USB-TTL
                                                                                                    
  优先建议：                                                                                        
  - 先用 USB 跑通                                                                                   
  因为最省事。                                                                                      
                                                                                                    
  ---                                                                                               
  2) Striker ↔ X7+
                                                                                                    
  可以有两种方式：
                                                                                                    
  方式 1：Striker 和 HIL bridge 共用同一条 MAVLink 链路                                             
                                                                                                    
  比如在主机上做 MAVLink 路由：                                                                     
  - 一个端口给 HIL
  - 一个端口给 Striker                                                                              
  - 一个端口给 GCS    
                                                                                                    
  这通常最灵活。                                                                                    
                                                                                                    
  方式 2：X7+ 开多个 MAVLink 端口                                                                   
                                                                                                    
  比如：                                                                                            
  - USB 给 HIL/GCS
  - TELEM 给 Striker
                    
  但这会更麻烦。                                                                                    
                                                                                                    
  ---                                                                                               
  推荐网络/链路拓扑                                                                                 
                  
  我更建议：

  用 mavlink-router 或 MAVProxy                                                                     
  
  让真实飞控的 MAVLink 一路进来，再分发给多个消费者：                                               
                  
  - HIL bridge                                                                                      
  - Striker       
  - Mission Planner / QGC
                                                                                                    
  例如逻辑上：
  X7+ USB/serial                                                                                    
     ↓                                                                                              
  mavlink-router / MAVProxy                                                                         
     ├─ UDP -> HIL simulator                                                                        
     ├─ UDP -> Striker                                                                              
     └─ UDP -> GCS                                                                                  
                                                                                                    
  这样最方便调试。                                                                                  
                                                                                                    
  ---                                                                                               
  参数层面的思路  
                                                                                                    
  你不想刷固件，所以重点在参数。
                                                                                                    
  官方资料里确认：
  - HIL_PROTOCOL_MAVLINK
  - HIL_MODE_SENSORS    
                    
  也就是你要把飞控切进 MAVLink HIL + sensors 路线。                                                 
                                                                                                    
  但我建议你不要让我现在凭记忆乱报整套参数名和值，因为不同版本 AP 细节会变。                        
  更稳妥做法是：                                                                                    
                                                                                                    
  1. 先把 X7+ 接上 Mission Planner / QGC                                                            
  2. 搜索 HIL 相关参数                                                                              
  3. 设置为：                                                                                       
    - protocol = MAVLink                                                                            
    - mode = sensors                                                                                
                                                                                                    
  如果你愿意，我下一步可以继续帮你按你当前 AP 版本把具体参数名和值核出来。                          
                                                                                                    
  ---                                                                                               
  你现在最应该搭的不是“完整飞行物理”，而是 3 层验证
                                                                                                    
  第 1 层：通信闭环
                                                                                                    
  目标：          
  - X7+ 上电                                                                                        
  - Striker 能连上                                                                                  
  - 能收心跳、位置、模式、mission current
  - 能发 command_long / mission upload                                                              
                                      
  这一步不需要完整 HIL，先把链路打通。                                                              
                                                                                                    
  ---                                                                                               
  第 2 层：HIL 传感器闭环                                                                           
                                                                                                    
  目标：
  - 外部模拟器喂飞控姿态/GPS/IMU                                                                    
  - 飞控进入“像在飞”的状态                                                                          
  - 飞控输出舵量/模式变化                                                                           
  - Striker 看到的 telemetry 是来自真飞控计算结果                                                   
                                                                                                    
  这一步才是核心。                                                                                  
                                                                                                    
  ---                                                                                               
  第 3 层：业务闭环
                                                                                                    
  目标：
  - 用 Striker 跑你的任务链                                                                         
  - preflight                                                                                       
  - mission upload
  - takeoff / scan / enroute / release / landing                                                    
  - 验证真实硬件上的行为差异                    

  ---                                                                                               
  对你项目最关键的意义
                                                                                                    
  你真正想验证的不是“飞机飞得像不像”，而是：
                                                                                                    
  - 状态机是否在真实飞控条件下按预期推进                                                            
  - mission seq / mode / waypoint 事件是否一致
  - 投弹/释放/降落相关命令在真飞控上的行为是否和 SITL 一样                                          
  - 参数差异、调度延迟、串口时序是否引入偏差                                                        
                                                                                                    
  HIL 正好适合这个。                                                                                
                                                                                                    
  ---                                                                                               
  你可以怎么让 Striker 接入 X7+
                                                                                                    
  你项目当前配置支持串口：
                                                                                                    
  config.example.json:3-6                                                                           
  "serial_port": "/dev/serial0",                                                                    
  "serial_baud": 921600,                                                                            
  "transport": "serial",                                                                            
  "mavlink_url": "",                                                                                
                                                                                                    
  也就是说，把 Striker 改成连真实飞控即可，例如：                                                   
                                                                                                    
  {                                                                                                 
    "transport": "serial",                                                                          
    "serial_port": "/dev/ttyACM0",                                                                  
    "serial_baud": 115200,                                                                          
    "mavlink_url": ""                                                                               
  }                                                                                                 
                                                                                                    
  或者如果你用 mavlink-router 转成 UDP：                                                            
                                                                                                    
  {                                                                                                 
    "transport": "udp",
    "mavlink_url": "udp:127.0.0.1:14550"                                                            
  }                                                                                                 
                                                                                                    
  这个模式我更推荐，因为：                                                                          
  - HIL、GCS、Striker 都能同时接                                                                    
  - 调试方便                                                                                        
                  
  ---                                                                                               
  我给你的推荐实施方案
                                                                                                    
  方案 1：最稳    
                                                                                                    
  X7+ + MAVLink Router + HIL host + Striker                                                         
                                                                                                    
  - X7+ USB 接主机                                                                                  
  - 主机跑 mavlink-router
  - 主机再把 MAVLink 分发给：                                                                       
    - HIL bridge                                                                                    
    - Striker                                                                                       
    - Mission Planner/QGC                                                                           
                                                                                                    
  这是你现在最应该做的。                                                                            
                  
  ---
  方案 2：更简单但可观测性差
                                                                                                    
  X7+ 直接串口给 Striker，另一路给 HIL
                                                                                                    
  可行，但布线和端口管理更烦。                                                                      
                                                                                                    
  ---                                                                                               
  一个重要提醒    
              
  HIL 不等于完全不接真实传感器
                                                                                                    
  有的固件/配置下，如果 HIL 没完整接管，真传感器可能仍参与系统状态。                                
  所以你做 bench 时要非常小心：                                                                     
                                                                                                    
  - 拆桨                                                                                            
  - 不接 ESC/电机
  - 不让舵面造成危险动作                                                                            
  - 先只看 telemetry / mode / mission，不先做执行机构动作                                           
                                                                                                    
  ---                                                                                               
  你现在的最佳下一步                                                                                
                  
  如果你要我给你最实用的下一步，我建议是：

  第一步先做“真飞控链路接入”                                                                        
  
  我帮你把 Striker 先改成能连 X7+，验证：                                                           
  - heartbeat     
  - telemetry                                                                                       
  - mission upload
  - mode switch                                                                                     
                  
  第二步再上 HIL                                                                                    
                  
  等真实飞控链路稳定了，再接 HIL 模拟器。
  
  
  
  可以，而且树莓派最适合先做“桥接+路由”这层。                  
                                                               
  对你现在这条路，建议把 Pi 放在中间，拓扑先做成这样：         
                                                               
  CUAV X7+  <--USB/TELEM-->  Raspberry Pi                      
                                ├─ MAVProxy / mavlink-router   
                                ├─ HIL bridge / simulator      
                                ├─ Striker                     
                                └─ GCS(QGC/Mission Planner)    
                                                               
  核心点只有两个：                                             
                                                               
  1. Pi 负责转发 MAVLink                                       
  2. Pi 上的 HIL 程序负责给飞控注入虚拟传感器                  
                                                               
  ---             
  1. 先说结论：Pi 上怎么落地                                   
                                                               
  推荐分两阶段做
                                                               
  阶段 A：先打通真飞控链路                                     
                                                               
  先别急着完整 HIL，先做到：                                   
                  
  - Pi 通过 USB 连上 X7+                                       
  - Pi 能收到 heartbeat
  - Striker 能通过 Pi 连上 X7+                                 
  - GCS 也能通过 Pi 连上 X7+                                   
                                                               
  这一步只需要 MAVProxy / mavlink-router，不需要完整物理模拟。 
                                                               
  阶段 B：再加 HIL 注入                                        
                  
  再在 Pi 上跑一个程序：                                       
                  
  - 读取飞控输出/状态                                          
  - 根据“虚拟世界”计算姿态/GPS/IMU
  - 向飞控发送 HIL MAVLink 消息                                
                                                               
  这才是真正的 HIL 闭环。                                      
                                                               
  ---                                                          
  2. 树莓派上的最小可行方案
                                                               
  假设你登录 Pi： 
                                                               
  ssh ubuntu@ubuntu-desktop.local
                                                               
  2.1 先确认飞控被识别                                         
   
  X7+ 用 USB 接 Pi 后，通常会出现类似：                        
                  
  - /dev/ttyACM0                                               
  - 或 /dev/ttyUSB0
                                                               
  你可以在 Pi 上看：                                           
                                                               
  ls /dev/ttyACM* /dev/ttyUSB*                                 
                                                               
  如果是 Telem 串口走 USB-TTL，则可能是 /dev/ttyUSB0。         
                                                               
  ---                                                          
  3. 在 Pi 上先做 MAVLink 路由
                                                               
  Context7 里的 ArduPilot/MAVProxy 文档给到的最直接做法就是
  --master + 多个 --out。                                      
                  
  3.1 安装 MAVProxy                                            
                  
  在 Pi 上：                                                   
                  
  python3 -m pip install --user MAVProxy                       
                                                               
  如果没装 pymavlink，它会一起带上相关依赖。                   
                                                               
  ---                                                          
  3.2 启动转发    
                                                               
  比如飞控在 /dev/ttyACM0，波特率 115200：
                                                               
  mavproxy.py \   
    --master=/dev/ttyACM0 \                                    
    --baudrate 115200 \                                        
    --out=udp:127.0.0.1:14550 \                                
    --out=udp:127.0.0.1:14551 \                                
    --out=udp:192.168.1.100:14550                              
                                                               
  可以这样分配：                                               
                                                               
  - 127.0.0.1:14550 → Striker                                  
  - 127.0.0.1:14551 → HIL bridge
  - 192.168.1.100:14550 → 你的地面站电脑                       
                                                               
  如果 Striker、HIL、GCS 都在 Pi 本机，就全走 127.0.0.1。      
                                                               
  ---                                                          
  4. 飞控侧要配什么
                                                               
  从 ArduPilot 文档看，HIL 相关思路是：
                                                               
  - HIL_PROTOCOL = MAVLink
  - MAVLink HIL 需要 HIL_MODE_SENSORS

  但我不建议你现在凭记忆硬填整套参数值。更稳的做法是：         
   
  1. 让 X7+ 先连上 QGC / Mission Planner                       
  2. 搜索 HIL 相关参数
  3. 确认当前固件里对应参数名和值                              
  4. 切到 MAVLink HIL / sensors 这一路                         
                                                               
  另外，Pi 连接飞控的串口协议应是 MAVLink。ArduPilot           
  文档里常见串口配置类似：                                     
                                                               
  SERIALx_PROTOCOL = 1                                         
  SERIALx_BAUD = 115                                           
                                                               
  也就是该串口作为 MAVLink 端口使用。                          
                                                               
  ---                                                          
  5. Pi 上的 HIL 程序到底要做什么
                                                               
  这部分最关键。
                                                               
  5.1 HIL 不是“开个参数就完成”                                 
                                                               
  你还需要一个 HIL bridge，它运行在 Pi 上，职责是：            
                  
  输入                                                         
                  
  从飞控拿到：                                                 
                  
  - 姿态/模式/状态                                             
  - 舵机输出、油门输出、控制意图
  - 其他你需要的 MAVLink 信息                                  
                                                               
  计算                                                         
                                                               
  在 Pi 上做一个轻量“物理世界”：                               
   
  - 当前油门、舵量 -> 更新速度/姿态/位置                       
  - 或者先不用真实气动模型，只做一个简化状态机模型
                                                               
  输出                                                         
   
  把计算后的“虚拟传感器”喂回飞控：                             
                  
  - IMU                                                        
  - GPS           
  - 气压/高度                                                  
  - 姿态/角速度                                                
   
  ---                                                          
  6. 对你来说最现实的实现方式
                                                               
  方案 1：Pi 只做路由，模拟器在更强的主机上
                                                               
  这是我更推荐的：
                                                               
  X7+ <-> Pi(MAVProxy)                                         
            ├─ UDP -> Striker
            ├─ UDP -> GCS                                      
            └─ UDP -> 上位机HIL模拟器                          
                                                               
  优点：                                                       
                                                               
  - Pi 压力小                                                  
  - HIL 计算放在 PC 上更方便调试
  - Striker 仍然可以像连真机一样工作                           
                                                               
  方案 2：Pi 同时做路由 + HIL bridge                           
                                                               
  如果你的 HIL 模型比较轻，也可以全放 Pi 上：                  
                  
  X7+ <-> Pi                                                   
            ├─ MAVProxy                                        
            ├─ striker                                         
            └─ hil_bridge.py                                   
                                                               
  这个更紧凑，但调试没那么舒服。                               
                                                               
  ---                                                          
  7. 我建议你的第一版别追求“真实气动”
                                                               
  你现在真正要验证的多半不是气动精度，而是：
                                                               
  - 真飞控是否能稳定进入任务流程                               
  - mission 上传/切模式是否正常                                
  - 状态机推进是否和 SITL 一致                                 
  - 真实飞控时序是否影响 Striker                               
                                                               
  所以第一版 HIL bridge 建议做成：                             
                                                               
  v1：简化模型                                                 
                  
  - 固定风                                                     
  - 简单速度积分  
  - 简单姿态响应                                               
  - GPS/IMU 按固定频率发回去                                   
                                                               
  先让飞控“感觉自己在飞”。                                     
                                                               
  v2：再加复杂模型                                             
                  
  - 更真实的滚转/俯仰动态                                      
  - 高度变化                                                   
  - 更细的噪声模型                                             
                                                               
  ---                                                          
  8. 你现在在 Pi 上可以先做的命令级步骤                        
                                                               
  Step 1
                                                               
  SSH 上 Pi：
                                                               
  ssh ubuntu@ubuntu-desktop.local                              
                                                               
  Step 2                                                       
                                                               
  确认飞控串口：                                               
                  
  ls /dev/ttyACM* /dev/ttyUSB*                                 
                                                               
  Step 3                                                       
                                                               
  启动 MAVProxy：                                              
                  
  mavproxy.py --master=/dev/ttyACM0 --baudrate 115200          
  --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551          
                                                               
  Step 4                                                       
                                                               
  验证：                                                       
  - QGC 能不能连
  - Striker 能不能连                                           
  - 能不能收到 heartbeat / attitude / gps
                                                               
  Step 5                                                       
                                                               
  再写一个 hil_bridge.py：                                     
  - 监听 udp:127.0.0.1:14551                                   
  - 读取飞控消息                                               
  - 按固定周期回发 HIL 传感器消息
                                                               
  ---                                                          
  9. 一个很重要的现实提醒                                      
                                                               
  树莓派不是“自动拥有 HIL”。
  它只是个宿主机。                                             
                                                               
  你还得在 Pi 上跑这两类程序之一：                             
                                                               
  - 现成 HIL 模拟器/桥                                         
  - 或 你自己写的 pymavlink bridge
                                                               
  如果你问“Pi 上怎么实现”，本质上答案是：                      
                                                               
  ▎ Pi 上跑一个 MAVLink 路由器 + 一个 HIL 数据注入程序。       
            
  ---                                                          
  10. 最适合你的下一步
                                                               
  我建议按这个顺序：
                                                               
  1. 先把 Pi → X7+ → GCS/Striker 的 MAVLink 链路打通
  2. 再写最小版 hil_bridge.py                                  
  3. 先做简化 HIL，不追求真实气动                              
  4. 最后再把 Striker 任务链接进来
                                                               
  ---
  如果你愿意，我下一步可以直接给你两样东西里的任意一个：
                                                               
  A. Pi 上可直接运行的 hil_bridge.py 最小骨架
                                                               
  用 pymavlink 写，负责：                                      
  - 连 X7+                                                     
  - 读飞控消息                                                 
  - 周期发送 HIL 传感器/GPS
                                                               
  B. 一套完整部署方案                                          
                                                               
  包括：                                                       
  - Pi 上的 systemd 服务                                       
  - MAVProxy 启动命令                                          
  - Striker/地面站端口规划    
  - 调试顺序                                                   
                                                               
  如果你要，我建议我直接先给你 A：最小可跑的 hil_bridge.py。

                                                                                                    
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

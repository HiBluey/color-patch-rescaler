import pandas as pd
import numpy as np
import os
import sys

def get_range_preset(bit_depth, range_type):
    """根据位深和范围类型返回 (min, max)"""
    if bit_depth == 8:
        if range_type == 'full': return (0, 255)
        if range_type == 'legal': return (16, 235)
    elif bit_depth == 10:
        if range_type == 'full': return (0, 1023)
        if range_type == 'legal': return (64, 940)
    elif bit_depth == 12:
        if range_type == 'full': return (0, 4095)
        if range_type == 'legal': return (256, 3760)
    return None

def get_user_range_setting(io_type="输入"):
    """交互式获取用户的范围设置"""
    print(f"\n--- 设置 {io_type} 格式 ---")
    print("请选择位深:")
    print("1. 8-bit")
    print("2. 10-bit")
    print("3. 12-bit")
    print("4. 自定义 (手动输入 Min/Max)")
    
    choice = input("请输入选项 (1-4): ").strip()
    
    if choice == '4':
        try:
            c_min = int(input(f"请输入 {io_type} 最小值 (例如 0): "))
            c_max = int(input(f"请输入 {io_type} 最大值 (例如 1023): "))
            return c_min, c_max
        except ValueError:
            print("输入错误，请输入整数。")
            sys.exit()

    bit_map = {'1': 8, '2': 10, '3': 12}
    if choice not in bit_map:
        print("无效选项。")
        sys.exit()
    
    bit_depth = bit_map[choice]
    
    print(f"请选择 {bit_depth}-bit 的范围类型:")
    print("1. 全范围 Full Range (例如 0-255, 0-1023)")
    print("2. 视频/有限范围 Legal/Limited Range (例如 16-235, 64-940)")
    print("3. 自定义范围")
    
    range_choice = input("请输入选项 (1-3): ").strip()
    
    if range_choice == '1':
        return get_range_preset(bit_depth, 'full')
    elif range_choice == '2':
        return get_range_preset(bit_depth, 'legal')
    elif range_choice == '3':
        try:
            c_min = int(input(f"请输入 {io_type} 最小值: "))
            c_max = int(input(f"请输入 {io_type} 最大值: "))
            return c_min, c_max
        except ValueError:
            print("输入错误。")
            sys.exit()
    else:
        print("无效选项。")
        sys.exit()

def main():
    print("=================================================")
    print("      3D LUT 色块数据通用转换工具 (互转版)")
    print("=================================================")

    # 1. 获取文件路径
    file_path = input("\n请输入CSV文件路径 (可以直接拖入文件): ").strip().strip('"').strip("'")
    
    if not os.path.exists(file_path):
        print("错误: 找不到文件。")
        return

    try:
        df = pd.read_csv(file_path)
        # 检查必要的列
        required_cols = ['R', 'G', 'B']
        if not all(col in df.columns for col in required_cols):
            print(f"错误: CSV文件缺少必要的列 {required_cols}")
            return
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    # 2. 获取输入（源）格式
    src_min, src_max = get_user_range_setting("输入 (源数据)")
    print(f">> 已确认源范围: {src_min} - {src_max}")

    # 3. 获取输出（目标）格式
    tgt_min, tgt_max = get_user_range_setting("输出 (目标数据)")
    print(f">> 已确认目标范围: {tgt_min} - {tgt_max}")

    # 4. 执行转换
    print(f"\n正在转换: [{src_min}~{src_max}] -> [{tgt_min}~{tgt_max}] ...")
    
    # 计算公式：Out = (In - InMin) / (InMax - InMin) * (OutMax - OutMin) + OutMin
    scale = (tgt_max - tgt_min) / (src_max - src_min) if (src_max - src_min) != 0 else 0
    
    for col in ['R', 'G', 'B']:
        # 核心转换逻辑
        val = (df[col] - src_min) * scale + tgt_min
        
        # 四舍五入取整
        val = val.round().astype(int)
        
        # 裁切 (Clip) 防止溢出 (比如转回Legal range时可能会有超标数据)
        # 注意：如果你希望保留超白/超黑用于分析，可以注释掉下面这行，但做LUT通常需要裁切到容器范围
        # 这里假设输出容器的最大值由用户输入的目标范围决定，
        # 如果是转为10bit legal (64-940)，容器其实是0-1023。
        # 为了安全，这里我们根据用户的设定范围进行裁切。
        # 如果你想限制在容器位深内（比如64-940的数据允许溢出到0-1023），需要更复杂的逻辑。
        # 现在的逻辑是严格限制在你设定的 Min-Max 之间。
        val = np.clip(val, tgt_min, tgt_max)
        
        df[col] = val

    # 5. 保存文件
    input_dir, input_name = os.path.split(file_path)
    file_root, _ = os.path.splitext(input_name)
    output_filename = f"{file_root}_Converted_{tgt_min}-{tgt_max}.csv"
    output_path = os.path.join(input_dir, output_filename)
    
    df.to_csv(output_path, index=False)
    print(f"\n转换成功！")
    print(f"文件已保存为: {output_path}")
    print(f"数据预览:\n{df.head()}")

if __name__ == "__main__":
    main()

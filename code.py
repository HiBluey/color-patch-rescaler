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
    print("      3D LUT 色块数据通用转换工具 (增强版)")
    print("=================================================")

    try:
        # 1. 获取文件路径
        # 支持拖入文件直接运行
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            print(f"检测到输入文件: {file_path}")
        else:
            file_path = input("\n请输入CSV文件路径 (可以直接拖入文件): ").strip().strip('"').strip("'")
        
        if not os.path.exists(file_path):
            print("错误: 找不到文件。")
            input("按回车键退出...")
            return

        # --- 读取文件逻辑 (增强版) ---
        try:
            # 尝试默认读取
            df = pd.read_csv(file_path)
            
            # 检查是否有 R, G, B 列
            required_cols = ['R', 'G', 'B']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f">> 警告: 未在首行检测到列名 {missing_cols}")
                print(">> 尝试识别无标题行的数据结构...")
                
                # 重新读取，不将第一行作为标题
                df_no_header = pd.read_csv(file_path, header=None)
                cols_count = df_no_header.shape[1]
                
                if cols_count == 4:
                    # 假设格式为: Index, R, G, B (你的文件属于这种情况)
                    print(f">> 检测到 {cols_count} 列数据。")
                    print(">> 自动应用格式: [Index, R, G, B]")
                    df = df_no_header
                    df.columns = ['Index', 'R', 'G', 'B']
                elif cols_count == 3:
                    # 假设格式为: R, G, B
                    print(f">> 检测到 {cols_count} 列数据。")
                    print(">> 自动应用格式: [R, G, B]")
                    df = df_no_header
                    df.columns = ['R', 'G', 'B']
                else:
                    print(f"错误: 无法自动识别数据列 (检测到 {cols_count} 列)。")
                    print("请确保CSV包含 R,G,B 标题，或者为 3列(RGB) / 4列(ID+RGB) 格式。")
                    input("按回车键退出...")
                    return
            else:
                print(">> 成功识别 R, G, B 列。")

        except Exception as e:
            print(f"读取文件失败: {e}")
            input("按回车键退出...")
            return
        # ---------------------------

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
            
            # 裁切 (Clip)
            val = np.clip(val, tgt_min, tgt_max)
            
            df[col] = val

        # 5. 保存文件
        input_dir, input_name = os.path.split(file_path)
        file_root, _ = os.path.splitext(input_name)
        output_filename = f"{file_root}_Converted_{tgt_min}-{tgt_max}.csv"
        output_path = os.path.join(input_dir, output_filename)
        
        # 保存时 index=False，但因为df里已经有了 'Index' 列（如果是4列数据），所以序号会被保留
        df.to_csv(output_path, index=False)
        print(f"\n转换成功！")
        print(f"文件已保存为: {output_path}")
        print(f"数据预览:\n{df.head()}")
        
        input("\n处理完成。按回车键退出...")
    
    except Exception as e:
        print(f"\n发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n程序异常。按回车键退出...")

if __name__ == "__main__":
    main()

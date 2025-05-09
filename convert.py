import os
import re
import pandas as pd

# 配置输入输出
INPUT_FILE = 'B题附件/008.xlsx'
OUTPUT_DIR = 'clean'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 单位映射
UNIT_MAP = {
    '万': 1e4,
    '亿': 1e8,
}

# 读取原始表格，无表头，全部作为字符串
raw_df = pd.read_excel(INPUT_FILE, header=None, dtype=str)
first_col = raw_df.iloc[:, 0].fillna('').astype(str)

total_rows = len(first_col)
category = None
in_table = False
col_data = {}
list_name = None

for idx, cell in first_col.items():
    text = cell.strip()
    # 检测分类行，如【1.财务指标】
    if re.match(r'^【\d+\..+】$', text):
        # 清理中括号和数字前缀
        category = re.sub(r'[【】]', '', text)
        category = re.sub(r'^\d+\.', '', category).strip()
        continue

    # 检测表格开始，仅当当前不在解析表格时
    if not in_table and text.startswith('┌'):
        # 列表名称在分隔符上一行
        raw_name = first_col.iloc[idx - 1].strip()
        list_name = re.sub(r'[【】]', '', raw_name)
        list_name = re.sub(r'^\d+\.', '', list_name).strip()
        in_table = True
        col_data = {}
        continue

    if in_table:
        # 遇到结束符，检查下一行是否新表开始
        if text.startswith('└'):
            next_idx = idx + 1
            next_line = first_col.iloc[next_idx].strip() if next_idx < total_rows else ''
            # 若下一行为新表开始，继续合并，不保存
            if next_line.startswith('┌'):
                continue
            # 否则真正结束，填充并保存当前表格
            if col_data:
                # 统一列表长度，填充缺失
                max_len = max(len(v) for v in col_data.values())
                for k, v in col_data.items():
                    if len(v) < max_len:
                        v.extend([None] * (max_len - len(v)))
                df_table = pd.DataFrame(col_data)
                base_name = os.path.splitext(os.path.basename(INPUT_FILE))[0]
                safe_cat = re.sub(r'[\\/:"*?<>|]', '_', category)
                safe_list = re.sub(r'[\\/:"*?<>|]', '_', list_name)
                out_file = f"{base_name}_{safe_cat}_{safe_list}.csv"
                df_table.to_csv(os.path.join(OUTPUT_DIR, out_file), index=False)
            in_table = False
            col_data = {}
            continue

        # 忽略分隔符行
        if text.startswith('├'):
            continue

        # 仅处理以半角或全角竖线开头的数据行
        if re.match(r'^[|｜]', text):
            parts = [p.strip() for p in re.split(r'[|｜]', text) if p.strip()]
            if not parts:
                continue
            col = parts[0]
            values = []
            for val in parts[1:]:
                val = val.replace(',', '')
                # 仅处理以汉字结尾的数据（如“万”“亿”）
                if re.match(r'^-?\d+(?:\.\d+)?[\u4e00-\u9fa5]$', val):
                    m = re.match(r'^(-?\d+(?:\.\d+)?)([万亿])$', val)
                    if m:
                        num = float(m.group(1)) * UNIT_MAP[m.group(2)]
                        values.append(int(num))
                # 其他情况跳过
            # 如果本行有有效值，则追加至 col_data
            if values:
                col_data.setdefault(col, []).extend(values)
# 脚本执行完成
print("所有表格已提取并保存至 'clean' 文件夹。（数据填充缺失值为 None）")

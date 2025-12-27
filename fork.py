import os
import glob

# 配置需要扫描和修复的规则
REPLACEMENTS = [
    # 1. 修复核心类型 API (Fix .type() -> .scalar_type())
    {
        "files": [
            "dpvo/lietorch/src/lietorch_gpu.cu",
            "dpvo/lietorch/src/lietorch_cpu.cpp",
            "dpvo/altcorr/correlation_kernel.cu"
        ],
        "rules": {
            ".type()": ".scalar_type()", 
            "at::DeprecatedTypeProperties": "at::ScalarType"
        }
    },
    # 2. 修复宏定义 (Fix dispatch.h)
    {
        "files": ["dpvo/lietorch/include/dispatch.h"],
        "rules": {
            # 移除旧的类型转换函数调用，直接透传
            "at::ScalarType _st = ::detail::scalar_type(the_type);": "at::ScalarType _st = the_type;"
        }
    },
    # 3. 修复线性代数算子 (Fix LinAlg)
    {
        "files": ["dpvo/fastba/ba_cuda.cu"],
        "rules": {
            "torch::linalg::cholesky": "at::linalg_cholesky",
            "at::linalg::cholesky": "at::linalg_cholesky"
        }
    },
]

def update_setup_py():
    """专门修改 setup.py 以屏蔽警告"""
    setup_path = "setup.py"
    if not os.path.exists(setup_path):
        print(f"[ERROR] {setup_path} not found!")
        return

    with open(setup_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了 -w
    if "'-w'" in content:
        print(f"[OK] {setup_path} already patched.")
        return

    # 找到编译参数列表并注入 -w
    # 通常都在 C++17 标准设置附近
    if "'-std=c++17'" in content:
        new_content = content.replace("'-std=c++17'", "'-std=c++17', '-w'")
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[PATCHED] {setup_path} (Warnings suppressed)")
    else:
        print(f"[WARN] Could not find insertion point in {setup_path}")

def process_file(filepath, rules):
    if not os.path.exists(filepath):
        print(f"[SKIP] File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    for old, new in rules.items():
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[PATCHED] {filepath}")
    else:
        print(f"[OK] {filepath}")

def main():
    print(">>> Starting DPVO Systematic Modernization...")
    
    # 执行文件内容替换
    for group in REPLACEMENTS:
        for filepath in group["files"]:
            process_file(filepath, group["rules"])
    
    # 执行 setup.py 特殊修改
    update_setup_py()
    
    print(">>> All tasks completed.")

if __name__ == "__main__":
    main()
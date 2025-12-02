#!/usr/bin/env python3
"""
项目导出脚本 - 生成完整的项目结构和配置
"""
import os
import json
import yaml
from pathlib import Path
from datetime import datetime

class ProjectExporter:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).absolute()
        self.exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules'}
        self.exclude_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll'}
        self.max_file_size = 100 * 1024  # 100KB
        
    def get_file_tree(self, path=None, level=0):
        """生成项目树状结构"""
        if path is None:
            path = self.project_root
        
        tree_lines = []
        indent = "    " * level
        
        # 首先列出文件
        items = sorted(os.listdir(path))
        dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and i not in self.exclude_dirs]
        files = [i for i in items if os.path.isfile(os.path.join(path, i)) 
                 and not any(i.endswith(ext) for ext in self.exclude_extensions)]
        
        # 添加目录
        for d in dirs:
            tree_lines.append(f"{indent}├── {d}/")
            subdir_path = os.path.join(path, d)
            try:
                sub_tree = self.get_file_tree(subdir_path, level + 1)
                tree_lines.extend(sub_tree)
            except PermissionError:
                tree_lines.append(f"{indent}    └── [权限拒绝]")
        
        # 添加文件
        for i, f in enumerate(files):
            prefix = "└──" if i == len(files) - 1 and not dirs else "├──"
            full_path = os.path.join(path, f)
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
            size_str = f" ({file_size} bytes)" if file_size < 1024 else f" ({file_size/1024:.1f} KB)"
            tree_lines.append(f"{indent}{prefix} {f}{size_str}")
        
        return tree_lines
    
    def read_file_content(self, filepath, max_lines=200):
        """读取文件内容（限制行数）"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... [文件过长，已截断，共{i+1}行]\n")
                        break
                    lines.append(line)
                return ''.join(lines)
        except Exception as e:
            return f"[读取文件时出错: {str(e)}]"
    
    def export_project_info(self, output_format='txt'):
        """导出完整的项目信息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 项目结构
        print("生成项目结构...")
        file_tree = self.get_file_tree()
        
        # 2. 关键文件内容
        print("读取关键文件...")
        key_files = self.find_key_files()
        
        # 3. 配置文件内容
        print("读取配置文件...")
        config_files = self.find_config_files()
        
        # 4. Python依赖
        print("检查依赖...")
        dependencies = self.get_dependencies()
        
        # 5. 环境变量
        print("读取环境配置...")
        env_config = self.get_env_config()
        
        # 6. API端点汇总
        print("分析API端点...")
        api_endpoints = self.get_api_endpoints()
        
        # 根据格式导出
        if output_format == 'txt':
            return self.export_to_txt(file_tree, key_files, config_files, 
                                     dependencies, env_config, api_endpoints, timestamp)
        elif output_format == 'json':
            return self.export_to_json(file_tree, key_files, config_files,
                                      dependencies, env_config, api_endpoints, timestamp)
        else:
            return self.export_to_markdown(file_tree, key_files, config_files,
                                          dependencies, env_config, api_endpoints, timestamp)
    
    def find_key_files(self):
        """找到关键文件"""
        key_patterns = [
            '*.py',
            'requirements.txt',
            '*.env*',
            'Dockerfile',
            'docker-compose*.yml',
            '*.md',
            '*.txt'
        ]
        
        key_files = {}
        for pattern in key_patterns:
            for file_path in self.project_root.rglob(pattern):
                if not any(excluded in str(file_path) for excluded in self.exclude_dirs):
                    rel_path = str(file_path.relative_to(self.project_root))
                    key_files[rel_path] = self.read_file_content(file_path)
        
        return key_files
    
    def find_config_files(self):
        """查找配置文件"""
        config_files = {}
        config_patterns = ['*.py', '*.yml', '*.yaml', '*.json', '*.toml']
        
        for pattern in config_patterns:
            for file_path in self.project_root.rglob(pattern):
                if 'config' in file_path.name.lower() or 'setting' in file_path.name.lower():
                    if not any(excluded in str(file_path) for excluded in self.exclude_dirs):
                        rel_path = str(file_path.relative_to(self.project_root))
                        config_files[rel_path] = self.read_file_content(file_path)
        
        return config_files
    
    def get_dependencies(self):
        """获取依赖信息"""
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            return self.read_file_content(requirements_file)
        return "无requirements.txt文件"
    
    def get_env_config(self):
        """获取环境配置"""
        env_files = list(self.project_root.glob('.env*'))
        env_configs = {}
        
        for env_file in env_files:
            env_configs[env_file.name] = self.read_file_content(env_file)
        
        return env_configs
    
    def get_api_endpoints(self):
        """获取API端点信息"""
        endpoints = []
        
        for file_path in self.project_root.rglob('*.py'):
            if 'endpoint' in str(file_path) or 'api' in str(file_path) or 'route' in str(file_path):
                content = self.read_file_content(file_path, 50)
                # 简单提取路由信息
                if '@router.' in content or 'app.include_router' in content:
                    endpoints.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'preview': content[:500]
                    })
        
        return endpoints
    
    def export_to_txt(self, file_tree, key_files, config_files, 
                     dependencies, env_config, api_endpoints, timestamp):
        """导出为TXT格式"""
        output = []
        output.append("=" * 80)
        output.append("FASTAPI 电商平台 - 完整项目导出")
        output.append(f"导出时间: {timestamp}")
        output.append(f"项目根目录: {self.project_root}")
        output.append("=" * 80)
        
        # 1. 项目结构
        output.append("\n📁 项目文件结构:")
        output.append("-" * 40)
        output.extend(file_tree)
        
        # 2. 配置文件
        output.append("\n\n⚙️ 配置文件内容:")
        output.append("-" * 40)
        for file_path, content in config_files.items():
            output.append(f"\n[{file_path}]\n{'-' * 30}")
            output.append(content)
        
        # 3. 关键代码文件
        output.append("\n\n💻 关键代码文件:")
        output.append("-" * 40)
        for file_path, content in key_files.items():
            if file_path not in config_files:  # 避免重复
                output.append(f"\n[{file_path}]\n{'-' * 30}")
                output.append(content[:1000])  # 只显示前1000字符
        
        # 4. 依赖
        output.append("\n\n📦 项目依赖:")
        output.append("-" * 40)
        output.append(dependencies)
        
        # 5. 环境配置
        output.append("\n\n🔧 环境变量配置:")
        output.append("-" * 40)
        for env_file, content in env_config.items():
            output.append(f"\n[{env_file}]\n{'-' * 30}")
            output.append(content)
        
        # 6. API端点
        output.append("\n\n🔌 API端点汇总:")
        output.append("-" * 40)
        for endpoint in api_endpoints:
            output.append(f"\n📄 {endpoint['file']}")
            output.append(endpoint['preview'])
            output.append("-" * 30)
        
        output.append("\n" + "=" * 80)
        output.append("导出结束")
        
        return "\n".join(output)
    
    def export_to_markdown(self, file_tree, key_files, config_files,
                          dependencies, env_config, api_endpoints, timestamp):
        """导出为Markdown格式"""
        output = []
        output.append(f"# FastAPI电商平台 - 完整项目导出\n")
        output.append(f"**导出时间**: {timestamp}  \n")
        output.append(f"**项目根目录**: `{self.project_root}`\n")
        output.append("---\n")
        
        # 1. 项目结构
        output.append("## 📁 项目文件结构\n```")
        output.extend(file_tree)
        output.append("```\n")
        
        # 2. 配置文件
        output.append("## ⚙️ 配置文件内容\n")
        for file_path, content in config_files.items():
            output.append(f"### `{file_path}`\n")
            output.append("```python\n" + content + "\n```\n")
        
        # 3. 关键代码文件
        output.append("## 💻 关键代码文件\n")
        for file_path, content in key_files.items():
            if file_path not in config_files:
                output.append(f"### `{file_path}`\n")
                output.append("```python\n" + content[:2000] + "\n```\n")
        
        # 4. 依赖
        output.append("## 📦 项目依赖\n```txt\n" + dependencies + "\n```\n")
        
        # 5. 环境配置
        output.append("## 🔧 环境变量配置\n")
        for env_file, content in env_config.items():
            output.append(f"### `{env_file}`\n")
            output.append("```env\n" + content + "\n```\n")
        
        # 6. API端点
        output.append("## 🔌 API端点汇总\n")
        for endpoint in api_endpoints:
            output.append(f"### `{endpoint['file']}`\n")
            output.append("```python\n" + endpoint['preview'] + "\n```\n")
        
        return "\n".join(output)
    
    def export_to_json(self, file_tree, key_files, config_files,
                      dependencies, env_config, api_endpoints, timestamp):
        """导出为JSON格式"""
        data = {
            "metadata": {
                "project_name": "FastAPI电商平台",
                "export_time": timestamp,
                "project_root": str(self.project_root)
            },
            "file_structure": file_tree,
            "config_files": config_files,
            "key_files": {k: v[:5000] for k, v in key_files.items()},  # 限制大小
            "dependencies": dependencies,
            "environment": env_config,
            "api_endpoints": api_endpoints
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导出FastAPI项目配置')
    parser.add_argument('--format', choices=['txt', 'md', 'json'], default='md',
                       help='导出格式 (txt, md, json)')
    parser.add_argument('--output', default='project_export',
                       help='输出文件名前缀（不含扩展名）')
    parser.add_argument('--project-dir', default='.',
                       help='项目根目录路径')
    
    args = parser.parse_args()
    
    # 创建导出器
    exporter = ProjectExporter(args.project_dir)
    
    # 导出项目
    print(f"正在导出项目: {args.project_dir}")
    result = exporter.export_project_info(args.format)
    
    # 保存到文件
    output_file = f"{args.output}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if args.format == 'json':
        output_file += '.json'
    elif args.format == 'md':
        output_file += '.md'
    else:
        output_file += '.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"✅ 项目已导出到: {output_file}")
    
    # 同时显示关键信息
    print("\n📋 关键项目信息:")
    print(f"   项目路径: {os.path.abspath(args.project_dir)}")
    print(f"   导出文件: {output_file}")
    print(f"   文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

if __name__ == "__main__":
    main()
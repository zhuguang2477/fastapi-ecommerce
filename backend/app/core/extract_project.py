# extract_project.py
import os
import json
import pathlib
from typing import Dict, List, Set

class ProjectExtractor:
    def __init__(self, root_dir: str = "."):
        self.root_dir = pathlib.Path(root_dir)
        self.output_file = "project_summary.txt"
        
        # 需要提取的文件扩展名
        self.extensions = {
            '.py', '.md', '.txt', '.env', '.ini', 
            '.json', '.yaml', '.yml', '.toml', 
            '.sql', '.html', '.js', '.ts', '.jsx', 
            '.tsx', '.vue', '.css', '.scss'
        }
        
        # 忽略的目录和文件
        self.ignore_dirs = {
            '__pycache__', '.git', '.pytest_cache', 
            'venv', 'node_modules', 'uploads', 
            '.idea', '.vscode', 'dist', 'build'
        }
        
        self.ignore_files = {
            '.DS_Store', '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.dll', '*.exe', 'dump.rdb'
        }
        
        # 最大文件大小（避免读取大文件）
        self.max_size = 50000  # 50KB
    
    def should_include(self, path: pathlib.Path) -> bool:
        """判断文件是否需要包含"""
        # 检查是否在忽略目录中
        for part in path.parts:
            if part in self.ignore_dirs:
                return False
        
        # 检查是否是被忽略的文件
        if path.name in self.ignore_files:
            return False
        
        # 检查文件扩展名
        if path.suffix not in self.extensions:
            return False
        
        # 检查文件大小
        if path.is_file() and path.stat().st_size > self.max_size:
            print(f"跳过大文件: {path} ({path.stat().st_size} bytes)")
            return False
        
        return True
    
    def read_file_content(self, file_path: pathlib.Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"[读取文件时出错: {str(e)}]"
    
    def extract_project_structure(self) -> Dict:
        """提取项目结构"""
        project_data = {
            "structure": [],
            "files": {},
            "backend_models": {},
            "backend_api": {},
            "config_files": {},
            "total_files": 0
        }
        
        # 遍历目录
        for root, dirs, files in os.walk(self.root_dir):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            relative_root = pathlib.Path(root).relative_to(self.root_dir)
            
            for file in files:
                file_path = pathlib.Path(root) / file
                rel_path = file_path.relative_to(self.root_dir)
                
                if not self.should_include(file_path):
                    continue
                
                # 记录文件结构
                project_data["structure"].append(str(rel_path))
                
                # 读取重要文件的内容
                if self.is_important_file(rel_path):
                    content = self.read_file_content(file_path)
                    
                    # 分类存储文件内容
                    category = self.categorize_file(rel_path)
                    if category == "backend_model":
                        project_data["backend_models"][str(rel_path)] = content
                    elif category == "backend_api":
                        project_data["backend_api"][str(rel_path)] = content
                    elif category == "config":
                        project_data["config_files"][str(rel_path)] = content
                    else:
                        project_data["files"][str(rel_path)] = content
                    
                    project_data["total_files"] += 1
        
        return project_data
    
    def is_important_file(self, rel_path: pathlib.Path) -> bool:
        """判断是否是需要读取内容的重要文件"""
        important_patterns = {
            "backend/app/models/",
            "backend/app/api/",
            "backend/app/",
            "alembic/",
            "requirements.txt",
            ".env",
            "Dockerfile",
            "README.md",
            "__init__.py"
        }
        
        path_str = str(rel_path)
        
        # 检查是否是Python文件或其他重要文件
        if rel_path.suffix in ['.py', '.env', '.txt', '.md', '.ini']:
            # 排除测试文件（可选）
            if 'test_' in path_str or '_test.py' in path_str:
                return False
            return True
        
        return False
    
    def categorize_file(self, rel_path: pathlib.Path) -> str:
        """对文件进行分类"""
        path_str = str(rel_path)
        
        if "backend/app/models/" in path_str:
            return "backend_model"
        elif "backend/app/api/" in path_str:
            return "backend_api"
        elif any(pattern in path_str for pattern in ['.env', 'requirements', 'Dockerfile', 'alembic.ini']):
            return "config"
        else:
            return "other"
    
    def generate_summary(self, project_data: Dict) -> str:
        """生成项目摘要文本"""
        summary = []
        summary.append("=" * 80)
        summary.append("项目结构摘要")
        summary.append("=" * 80)
        summary.append(f"总文件数: {project_data['total_files']}")
        summary.append("")
        
        # 文件结构
        summary.append("项目结构:")
        summary.append("-" * 40)
        for file_path in sorted(project_data["structure"]):
            summary.append(f"  {file_path}")
        summary.append("")
        
        # 模型文件
        summary.append("后端模型文件:")
        summary.append("-" * 40)
        for model_file in sorted(project_data["backend_models"].keys()):
            summary.append(f"  {model_file}")
            # 显示前几行内容
            content = project_data["backend_models"][model_file]
            lines = content.split('\n')[:10]  # 只显示前10行
            for line in lines[:3]:  # 模型文件显示前3行
                if line.strip():
                    summary.append(f"    {line}")
            summary.append("")
        summary.append("")
        
        # API文件
        summary.append("后端API文件:")
        summary.append("-" * 40)
        for api_file in sorted(project_data["backend_api"].keys()):
            summary.append(f"  {api_file}")
            content = project_data["backend_api"][api_file]
            # 提取端点信息
            endpoints = self.extract_endpoints(content)
            for endpoint in endpoints:
                summary.append(f"    {endpoint}")
        summary.append("")
        
        # 配置文件
        summary.append("配置文件:")
        summary.append("-" * 40)
        for config_file in sorted(project_data["config_files"].keys()):
            summary.append(f"  {config_file}")
            content = project_data["config_files"][config_file]
            lines = content.split('\n')[:5]  # 显示前5行
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    summary.append(f"    {line}")
            summary.append("")
        
        return '\n'.join(summary)
    
    def extract_endpoints(self, content: str) -> List[str]:
        """从API文件中提取端点信息"""
        endpoints = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('@router.') or line.startswith('@app.'):
                # 获取下一行的函数定义
                if i + 1 < len(lines):
                    func_line = lines[i + 1].strip()
                    if func_line.startswith('def '):
                        endpoints.append(f"{line} -> {func_line}")
        return endpoints
    
    def run(self):
        """运行提取器"""
        print("正在提取项目结构...")
        project_data = self.extract_project_structure()
        
        print("生成项目摘要...")
        summary = self.generate_summary(project_data)
        
        # 保存到文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # 同时保存完整数据为JSON（可选）
        with open("project_data.json", 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        print(f"完成！项目摘要已保存到: {self.output_file}")
        print(f"完整数据已保存到: project_data.json")
        
        # 打印文件数量统计
        print(f"\n文件统计:")
        print(f"  模型文件: {len(project_data['backend_models'])}")
        print(f"  API文件: {len(project_data['backend_api'])}")
        print(f"  配置文件: {len(project_data['config_files'])}")
        print(f"  总文件数: {project_data['total_files']}")

if __name__ == "__main__":
    extractor = ProjectExtractor()
    extractor.run()
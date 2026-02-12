#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份脚本
从指定的API端点下载备份数据并保存到本地
"""

import os
import json
import requests
from datetime import datetime
import logging
import hashlib
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        """初始化备份管理器"""
        self.base_url = os.getenv('BACKUP_URL')
        self.username = os.getenv('BACKUP_USERNAME') 
        self.password = os.getenv('BACKUP_PASSWORD')
        
        # GitHub相关配置
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repository = os.getenv('GITHUB_REPOSITORY')  # 格式: owner/repo
        
        # 获取保留备份文件数量，默认100个
        max_backups_str = os.getenv('MAX_BACKUPS', '100')
        try:
            self.max_backups = int(max_backups_str) if max_backups_str.strip() else 100
        except ValueError:
            logger.warning(f"MAX_BACKUPS 配置无效 '{max_backups_str}'，使用默认值 100")
            self.max_backups = 100
        
        # 获取是否启用变更检测，默认启用
        change_detection_str = os.getenv('ENABLE_CHANGE_DETECTION', 'true')
        self.enable_change_detection = change_detection_str.strip().lower() in ('true', '1', 'yes', 'on') if change_detection_str.strip() else True
        
        # 强制执行私有仓库检查，不可禁用
        self.force_private_repo = True
        
        # 验证环境变量
        if not all([self.base_url, self.username, self.password]):
            raise ValueError("缺少必要的环境变量: BACKUP_URL, BACKUP_USERNAME, BACKUP_PASSWORD")
        
        # 构建完整的备份URL
        # 如果base_url不包含协议，默认使用https
        if not self.base_url.startswith(('http://', 'https://')):
            # 检查是否包含端口号
            if ':' in self.base_url:
                self.backup_url = f"https://{self.base_url}/api/manage/batch/list?includeValue=true&limit=1000"
                self.legacy_backup_url = f"https://{self.base_url}/api/manage/sysConfig/backup?action=backup"
            else:
                self.backup_url = f"https://{self.base_url}/api/manage/batch/list?includeValue=true&limit=1000"
                self.legacy_backup_url = f"https://{self.base_url}/api/manage/sysConfig/backup?action=backup"
        else:
            # 移除末尾的斜杠（如果存在）
            base_url_clean = self.base_url.rstrip('/')
            self.backup_url = f"{base_url_clean}/api/manage/batch/list?includeValue=true&limit=1000"
            self.legacy_backup_url = f"{base_url_clean}/api/manage/sysConfig/backup?action=backup"
        
        # 创建备份目录
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info(f"备份管理器初始化完成，备份URL: {self.backup_url}")
        logger.info(f"备用备份URL: {self.legacy_backup_url}")
        logger.info(f"最大保留备份文件数: {self.max_backups}")
        logger.info(f"变更检测: {'启用' if self.enable_change_detection else '禁用'}")
        logger.info("🔒 私有仓库检查: 强制启用（不可禁用）")
    
    def check_repository_privacy(self):
        """检查GitHub仓库是否为私有（强制执行，不可禁用）"""
        if not self.github_token or not self.github_repository:
            logger.error("❌ 安全检查失败：缺少GitHub Token或Repository信息")
            logger.error("无法验证仓库隐私状态，为了安全起见，备份任务将被终止")
            logger.error("环境变量要求：GITHUB_TOKEN 和 GITHUB_REPOSITORY")
            logger.error("注意：本程序强制要求使用私有仓库，此检查无法禁用")
            return False
        
        try:
            logger.info("🔒 正在检查仓库隐私状态...")
            
            # 检查标记文件是否存在
            privacy_check_file = os.path.join(self.backup_dir, '.privacy_verified')
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Backup-Security-Check/1.0'
            }
            
            # 调用GitHub API检查仓库信息
            api_url = f"https://api.github.com/repos/{self.github_repository}"
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                logger.error("❌ 仓库不存在或无权限访问")
                return False
            elif response.status_code != 200:
                logger.error(f"❌ GitHub API请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return False
            
            repo_info = response.json()
            is_private = repo_info.get('private', False)
            
            if not is_private:
                logger.error("❌ 🚨 严重安全警告：仓库当前为公开状态！ 🚨")
                logger.error("")
                logger.error("📢 此项目会备份包含敏感信息的数据文件！")
                logger.error("📢 公开仓库会导致您的敏感数据被任何人访问！")
                logger.error("")
                logger.error("🛡️  请立即执行以下步骤保护您的数据：")
                logger.error("   1. 前往 GitHub 仓库设置页面")
                logger.error(f"   2. 访问: https://github.com/{self.github_repository}/settings")
                logger.error("   3. 滚动到页面底部的 'Danger Zone' 区域")
                logger.error("   4. 点击 'Change repository visibility'")
                logger.error("   5. 选择 'Make private' 将仓库设为私有")
                logger.error("")
                logger.error("🔧 设置完成后，您可以通过以下方式之一重新运行：")
                logger.error("   • 手动触发 GitHub Actions workflow")
                logger.error("   • 等待下次定时任务执行")
                logger.error("   • 或者设置环境变量 FORCE_PRIVATE_REPO=false 来跳过此检查（不推荐）")
                logger.error("")
                logger.error("⚠️  为了您的数据安全，备份任务现在将被终止")
                
                return False
            
            logger.info("✅ 仓库隐私检查通过：仓库为私有状态")
            
            # 如果是首次通过检查，创建标记文件并给出提示
            if not os.path.exists(privacy_check_file):
                try:
                    with open(privacy_check_file, 'w', encoding='utf-8') as f:
                        f.write(f"Privacy check passed at: {datetime.now().isoformat()}\n")
                        f.write(f"Repository: {self.github_repository}\n")
                        f.write(f"Status: Private\n")
                    
                    logger.info("🎉 首次隐私检查通过！已创建验证标记文件")
                    logger.info("✨ 您的仓库配置正确，数据将得到安全保护")
                    
                except Exception as e:
                    logger.warning(f"无法创建隐私验证标记文件: {e}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {e}")
            logger.error("无法验证仓库隐私状态，为了安全起见，备份任务将被终止")
            return False
        except Exception as e:
            logger.error(f"❌ 隐私检查过程中发生错误: {e}")
            logger.error("为了安全起见，备份任务将被终止")
            return False
    
    def create_session(self):
        """创建带有认证的会话"""
        session = requests.Session()
        
        # 设置请求头
        session.headers.update({
            'User-Agent': 'Backup-Bot/1.0',
            'Accept': 'application/json',
        })
        
        # 设置超时时间
        session.timeout = 30
        
        return session
    
    def authenticate(self, session, url):
        """处理网站认证"""
        try:
            logger.info(f"正在连接到: {url}")
            # 首先访问备份URL，这可能会触发认证
            response = session.get(url, auth=(self.username, self.password), timeout=30)
            
            if response.status_code == 401:
                logger.error("认证失败，请检查用户名和密码")
                return False
            elif response.status_code != 200:
                logger.error(f"访问失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return False
            
            logger.info("认证成功")
            return True
            
        except requests.exceptions.ConnectTimeout:
            logger.error("连接超时，请检查网络连接和服务器状态")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {e}")
            logger.error("可能的原因：")
            logger.error("1. 服务器未运行或端口未开放")
            logger.error("2. 防火墙阻止了连接")
            logger.error("3. URL 配置不正确")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"认证过程中发生错误: {e}")
            return False
    
    def download_backup(self):
        """下载备份文件"""
        session = self.create_session()

        def fetch_backup(url, label):
            # 进行认证
            if not self.authenticate(session, url):
                return None

            try:
                logger.info(f"正在从 {url} 下载备份 ({label})...")
                response = session.get(url, auth=(self.username, self.password))

                if response.status_code == 200:
                    # 检查响应内容类型
                    content_type = response.headers.get('content-type', '')

                    if 'application/json' in content_type:
                        # 直接是JSON响应
                        return response.json()

                    # 尝试解析为JSON
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        logger.error("响应不是有效的JSON格式")
                        return None

                logger.error(f"下载失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"下载过程中发生错误: {e}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return None

        # 优先使用新API，失败后回退到旧API
        backup_data = fetch_backup(self.backup_url, 'new')
        if backup_data is None:
            logger.warning("新API失败，尝试回退到旧API")
            backup_data = fetch_backup(self.legacy_backup_url, 'legacy')

        if backup_data is None:
            raise RuntimeError("新旧API均失败，无法获取备份数据")

        return self.save_backup(backup_data)
    
    def calculate_data_hash(self, data):
        """计算数据的MD5哈希值（排除动态时间戳字段）"""
        try:
            # 创建数据副本，排除可能的动态字段
            data_copy = self.normalize_data_for_hash(data)
            
            # 将数据转换为标准化的JSON字符串
            json_str = json.dumps(data_copy, sort_keys=True, separators=(',', ':'))
            # 计算MD5哈希
            return hashlib.md5(json_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"计算数据哈希时发生错误: {e}")
            return None
    
    def normalize_data_for_hash(self, data):
        """标准化数据用于哈希计算，排除动态字段"""
        try:
            if isinstance(data, dict):
                # 创建数据副本
                normalized = {}
                for key, value in data.items():
                    # 排除动态时间戳字段
                    if key.lower() in ['timestamp', 'created_at', 'updated_at', 'last_modified', 'date', 'time']:
                        continue
                    # 递归处理嵌套对象
                    normalized[key] = self.normalize_data_for_hash(value)
                return normalized
            elif isinstance(data, list):
                # 递归处理列表中的每个元素
                return [self.normalize_data_for_hash(item) for item in data]
            else:
                # 基本类型直接返回
                return data
        except Exception as e:
            logger.error(f"标准化数据时发生错误: {e}")
            return data  # 发生错误时返回原始数据
    
    def get_latest_backup_hash(self):
        """获取最新备份文件的哈希值"""
        latest_filepath = os.path.join(self.backup_dir, 'latest_backup.json')
        
        if not os.path.exists(latest_filepath):
            logger.info("没有找到最新备份文件，这是首次备份")
            return None
        
        try:
            with open(latest_filepath, 'r', encoding='utf-8') as f:
                latest_data = json.load(f)
            return self.calculate_data_hash(latest_data)
        except Exception as e:
            logger.error(f"读取最新备份文件时发生错误: {e}")
            return None
    
    def is_data_changed(self, new_data):
        """检测数据是否发生变化"""
        # 计算新数据的哈希值
        new_hash = self.calculate_data_hash(new_data)
        if new_hash is None:
            logger.warning("无法计算新数据哈希，将强制保存备份")
            return True
        
        # 获取最新备份的哈希值
        latest_hash = self.get_latest_backup_hash()
        if latest_hash is None:
            logger.info("没有历史备份数据，将保存首次备份")
            return True
        
        # 比较哈希值
        logger.info(f"数据哈希对比：")
        logger.info(f"  新数据哈希: {new_hash[:16]}...")
        logger.info(f"  历史数据哈希: {latest_hash[:16]}...")
        
        if new_hash == latest_hash:
            logger.info("✅ 数据未发生变化（排除时间戳），跳过本次备份")
            return False
        else:
            logger.info("🔄 检测到实际数据变化，将保存新的备份")
            return True
    
    def save_backup(self, data):
        """保存备份数据到文件"""
        try:
            # 检测数据是否发生变化（如果启用了变更检测）
            if self.enable_change_detection and not self.is_data_changed(data):
                logger.info("数据未发生变化，跳过保存备份文件")
                return True  # 返回True表示操作成功（虽然没有保存新文件）
            
            # 生成文件名（包含时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(self.backup_dir, filename)
            
            # 保存JSON数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"备份文件已保存: {filepath}")
            
            # 同时保存一个最新的备份文件
            latest_filepath = os.path.join(self.backup_dir, 'latest_backup.json')
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"最新备份文件已更新: {latest_filepath}")
            
            # 清理旧备份文件（保留最近指定数量个）
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"保存备份文件时发生错误: {e}")
            return False
    
    def cleanup_old_backups(self):
        """清理旧的备份文件，保留最近的指定数量个文件"""
        try:
            # 获取所有备份文件（排除latest_backup.json）
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除多余的文件（保留最近指定数量个）
            if len(backup_files) > self.max_backups:
                deleted_count = 0
                for filepath, _ in backup_files[self.max_backups:]:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"已删除旧备份文件: {os.path.basename(filepath)}")
                
                logger.info(f"共删除了 {deleted_count} 个旧备份文件，保留最近 {self.max_backups} 个")
            else:
                logger.info(f"当前有 {len(backup_files)} 个备份文件，无需清理")
                    
        except Exception as e:
            logger.error(f"清理旧备份文件时发生错误: {e}")

def main():
    """主函数"""
    try:
        logger.info("🚀 开始执行备份任务...")
        logger.info("=" * 60)
        
        # 创建备份管理器
        backup_manager = BackupManager()
        
        # 首先进行仓库隐私检查
        logger.info("🔐 执行安全检查...")
        if not backup_manager.check_repository_privacy():
            logger.error("❌ 安全检查失败，备份任务已终止")
            logger.error("请确保仓库为私有状态后重新运行")
            exit(1)
        
        logger.info("✅ 安全检查通过，继续执行备份...")
        logger.info("=" * 60)
        
        # 执行备份
        success = backup_manager.download_backup()
        
        if success:
            logger.info("🎉 备份任务执行成功！")
        else:
            logger.error("❌ 备份任务执行失败！")
            exit(1)
            
    except Exception as e:
        logger.error(f"❌ 备份任务执行过程中发生未预期的错误: {e}")
        exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
安全的 OTP 系统数据库迁移脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect as sa_inspect
from backend.app.database import engine, SessionLocal, Base
from backend.app.models.user import User
from backend.app.models.otp import OTP
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name):
    """检查表是否存在"""
    inspector = sa_inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(table_name, column_name):
    """检查表中是否存在指定列"""
    inspector = sa_inspect(engine)
    columns = inspector.get_columns(table_name)
    column_names = [col['name'] for col in columns]
    return column_name in column_names

def migrate_to_otp_safe():
    """安全地迁移到 OTP 系统"""
    print("🔄 开始安全的 OTP 系统迁移...")
    
    db = SessionLocal()
    
    try:
        # 检查当前状态
        print("📊 检查当前数据库状态...")
        
        # 检查 users 表是否存在
        if not check_table_exists('users'):
            print("   ℹ️  用户表不存在，直接创建新表...")
            Base.metadata.create_all(bind=engine)
            print("   ✅ 所有表创建完成")
            return
        
        print("   ✅ 用户表已存在")
        
        # 检查是否已经迁移过
        if check_column_exists('users', 'hashed_password'):
            print("   ℹ️  检测到旧版用户表结构，开始迁移...")
            
            # 创建备份表
            print("1. 创建用户表备份...")
            try:
                db.execute(text("CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users"))
                db.commit()
                print("   ✅ 用户表备份完成")
            except Exception as e:
                print(f"   ⚠️  备份用户表时出错: {e}")
                db.rollback()
            
            # 检查并修改表结构
            print("2. 修改用户表结构...")
            
            # 检查并移除 hashed_password 列
            if check_column_exists('users', 'hashed_password'):
                try:
                    # 在 PostgreSQL 中，我们需要先创建新表，复制数据，然后重命名
                    print("   移除 hashed_password 列...")
                    
                    # 创建临时表（新结构）
                    db.execute(text("""
                        CREATE TABLE users_new (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            full_name VARCHAR(100),
                            phone VARCHAR(20),
                            avatar_url VARCHAR(500),
                            is_verified BOOLEAN DEFAULT FALSE,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE,
                            updated_at TIMESTAMP WITH TIME ZONE,
                            last_login TIMESTAMP WITH TIME ZONE
                        )
                    """))
                    
                    # 复制数据（排除 hashed_password）
                    db.execute(text("""
                        INSERT INTO users_new (id, email, full_name, phone, avatar_url, 
                                               is_verified, is_active, created_at, updated_at, last_login)
                        SELECT id, email, 
                               CASE WHEN name IS NOT NULL THEN name ELSE full_name END as full_name,
                               phone, avatar_url, 
                               COALESCE(is_verified, FALSE) as is_verified,
                               COALESCE(is_active, TRUE) as is_active,
                               created_at, updated_at, last_login
                        FROM users
                    """))
                    
                    # 删除原表
                    db.execute(text("DROP TABLE users"))
                    
                    # 重命名新表
                    db.execute(text("ALTER TABLE users_new RENAME TO users"))
                    
                    # 创建索引
                    db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
                    
                    db.commit()
                    print("   ✅ 用户表结构更新完成")
                    
                except Exception as e:
                    print(f"   ❌ 更新用户表结构时出错: {e}")
                    db.rollback()
                    raise
            else:
                print("   ℹ️  hashed_password 列已不存在，跳过此步骤")
            
            # 添加缺失的列（如果不存在）
            missing_columns = []
            if not check_column_exists('users', 'full_name'):
                missing_columns.append('full_name')
            if not check_column_exists('users', 'is_verified'):
                missing_columns.append('is_verified')
            
            if missing_columns:
                print(f"3. 添加缺失的列: {missing_columns}")
                try:
                    for column in missing_columns:
                        if column == 'full_name':
                            db.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
                        elif column == 'is_verified':
                            db.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
                    
                    db.commit()
                    print("   ✅ 缺失列添加完成")
                except Exception as e:
                    print(f"   ❌ 添加缺失列时出错: {e}")
                    db.rollback()
            else:
                print("3. 所有必需的列已存在，跳过此步骤")
        
        else:
            print("   ℹ️  用户表已经是最新结构，跳过迁移")
        
        # 创建 OTP 表（如果不存在）
        print("4. 创建 OTP 表...")
        if not check_table_exists('otps'):
            try:
                OTP.__table__.create(bind=engine, checkfirst=True)
                print("   ✅ OTP 表创建完成")
            except Exception as e:
                print(f"   ❌ 创建 OTP 表时出错: {e}")
        else:
            print("   ℹ️  OTP 表已存在，跳过创建")
        
        # 验证迁移结果
        print("5. 验证迁移结果...")
        inspector = sa_inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"   当前表: {tables}")
        
        if 'users' in tables:
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            print(f"   users 表列: {column_names}")
            
            # 检查关键列是否存在
            required_columns = ['email', 'full_name', 'is_verified']
            missing = [col for col in required_columns if col not in column_names]
            
            if not missing:
                print("   ✅ 用户表结构正确")
            else:
                print(f"   ⚠️  用户表缺少列: {missing}")
        
        if 'otps' in tables:
            print("   ✅ OTP 表创建成功")
        
        # 验证数据完整性
        print("6. 验证数据完整性...")
        try:
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"   用户数量: {user_count}")
            
            if check_table_exists('users_backup'):
                backup_count = db.execute(text("SELECT COUNT(*) FROM users_backup")).scalar()
                print(f"   备份表中的用户数量: {backup_count}")
                
                if user_count == backup_count:
                    print("   ✅ 数据迁移完整")
                else:
                    print(f"   ⚠️  数据迁移不完整: 原表 {backup_count} 条，新表 {user_count} 条")
        
        except Exception as e:
            print(f"   ⚠️  验证数据完整性时出错: {e}")
        
        print("\n🎉 OTP 系统迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移过程中出错: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_otp_safe()
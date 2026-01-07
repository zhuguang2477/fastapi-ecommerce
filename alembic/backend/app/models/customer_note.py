# backend/app/models/customer_note.py
"""
客户笔记模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class CustomerNote(Base):
    """客户笔记模型"""
    __tablename__ = "customer_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # 笔记内容
    content = Column(Text, nullable=False)
    note_type = Column(String(50))
    is_important = Column(Boolean, default=False)
    
    # 创建者信息
    created_by = Column(Integer, ForeignKey("users.id"))
    created_by_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系 - 使用字符串引用避免循环导入
    customer = relationship("Customer", back_populates="notes")
    shop = relationship("Shop")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<CustomerNote(id={self.id}, customer_id={self.customer_id}, type='{self.note_type}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'shop_id': self.shop_id,
            'content': self.content,
            'note_type': self.note_type,
            'is_important': self.is_important,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'creator_email': self.creator.email if self.creator else None,
            'customer_email': self.customer.email if self.customer else None
        }
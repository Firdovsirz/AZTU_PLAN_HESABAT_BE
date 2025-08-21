from sqlalchemy import (
    Column,
    UniqueConstraint,
    Integer,
    String,
    Boolean,
    DateTime
)
from app.db.database import Base

class Auth(Base):
    __tablename__ = "auth"
    __table_args__ = (UniqueConstraint("fin_kod"),)

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, unique=True, nullable=False)
    role = Column(Integer, nullable=False)
    # 0. developer
    # 1. admin
    # 2. dekan, tyutor, (zamdekan ?)
    # 3. kafedra mudiri
    # 4. normal teachers (professor, dosent, bas muellim, muellim, diger)
    password = Column(String, nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    otp = Column(Integer)
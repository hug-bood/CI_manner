from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import secrets
import time

from app.core.database import get_db
from app.models.auth import User

router = APIRouter(prefix="/auth", tags=["auth"])

# 简易token存储：{token: (user_id, expire_time)}
_token_store: dict[str, tuple[int, float]] = {}
TOKEN_EXPIRE_SECONDS = 86400  # 24小时


def _generate_token() -> str:
    """生成随机token"""
    return secrets.token_hex(32)


def _create_token(user_id: int) -> str:
    """创建token并存储"""
    token = _generate_token()
    _token_store[token] = (user_id, time.time() + TOKEN_EXPIRE_SECONDS)
    return token


def _validate_token(token: str) -> Optional[int]:
    """验证token，返回user_id或None"""
    if token not in _token_store:
        return None
    user_id, expire_time = _token_store[token]
    if time.time() > expire_time:
        del _token_store[token]
        return None
    return user_id


class UserItem(BaseModel):
    id: int
    username: str
    is_admin: bool
    can_cleanup: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str


class UserUpdate(BaseModel):
    can_cleanup: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    token: str
    user: UserItem


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """从Header中获取当前用户（通过token）"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user_id = _validate_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)):
    """要求管理员权限"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def require_cleanup(user: User = Depends(get_current_user)):
    """要求清理权限"""
    if not user.can_cleanup and not user.is_admin:
        raise HTTPException(status_code=403, detail="需要清理权限")
    return user


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录 - 仅需用户名"""
    user = db.query(User).filter_by(username=data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名不存在")
    
    token = _create_token(user.id)
    return LoginResponse(
        token=token,
        user=UserItem(id=user.id, username=user.username, is_admin=user.is_admin, can_cleanup=user.can_cleanup)
    )


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    """用户登出"""
    if authorization:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        if token in _token_store:
            del _token_store[token]
    return {"message": "已登出"}


@router.get("/users", response_model=List[UserItem])
def list_users(db: Session = Depends(get_db)):
    """获取用户列表"""
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserItem, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """创建用户 - 第一个用户自动成为管理员"""
    existing = db.query(User).filter_by(username=data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if len(data.username) < 2:
        raise HTTPException(status_code=400, detail="用户名长度不能少于2位")
    
    # 第一个用户自动成为管理员
    is_first_user = db.query(User).count() == 0
    
    user = User(
        username=data.username,
        password_hash="",
        is_admin=is_first_user,
        can_cleanup=is_first_user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserItem)
def update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户权限 - 仅管理员可操作"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.can_cleanup is not None:
        user.can_cleanup = data.can_cleanup
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户 - 仅管理员可操作"""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能删除管理员")
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


@router.delete("/users")
def delete_all_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除所有用户（仅管理员可操作）- 清空token并删除所有用户记录"""
    _token_store.clear()
    count = db.query(User).delete()
    db.commit()
    return {"message": f"已删除 {count} 个用户"}


@router.get("/me", response_model=UserItem)
def get_current_user_info(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return user


@router.post("/register", response_model=LoginResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """用户自助注册 - 仅需用户名，注册后自动登录"""
    existing = db.query(User).filter_by(username=data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if len(data.username) < 2:
        raise HTTPException(status_code=400, detail="用户名长度不能少于2位")
    
    # 第一个注册的用户自动成为管理员，后续为普通用户
    is_first_user = db.query(User).count() == 0
    
    user = User(
        username=data.username,
        password_hash="",
        is_admin=is_first_user,
        can_cleanup=is_first_user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 自动登录
    token = _create_token(user.id)
    return LoginResponse(
        token=token,
        user=UserItem(id=user.id, username=user.username, is_admin=user.is_admin, can_cleanup=user.can_cleanup)
    )


@router.get("/check")
def check_auth():
    """检查是否需要初始化（是否有用户）"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        return {"has_users": user_count > 0}
    finally:
        db.close()

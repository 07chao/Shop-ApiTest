"""
购物车服务 (数据访问层/业务逻辑层)
================================

提供购物车相关的业务逻辑处理，包括商品添加、数量修改、删除等。
支持高并发场景、购物车持久化、价格计算等操作。

设计思路:
1. 使用Redis存储购物车数据以提高性能
2. 支持购物车数据同步到数据库
3. 集成库存服务检查商品库存
4. 提供购物车合并功能（用户登录时）
5. 支持购物车过期和清理机制
6. 集成价格计算和优惠处理

本文件是数据访问层，负责处理业务逻辑并与数据库/缓存交互。
它被API路由层调用，使用模型层定义的数据结构。
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import aioredis

# 引入模型层定义的数据结构
from ..models.cart import Cart, CartItem
from ..models.product import Product
from ..models.user import User
from ..core.config import settings
from ..services.product_service import get_cached_stock

# 配置日志
logger = structlog.get_logger(__name__)

# Redis 连接
redis_client = aioredis.from_url(settings.redis_url)


class CartService:
    """购物车服务类"""
    
    @staticmethod
    async def get_cart_key(
            user_id: Optional[int] = None,
            session_id: Optional[str] = None) -> str:
        """
        获取购物车Redis键
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            str: Redis键
        """
        if user_id:
            return f"cart:user:{user_id}"
        elif session_id:
            return f"cart:session:{session_id}"
        else:
            raise ValueError("Either user_id or session_id must be provided")
    
    @staticmethod
    async def get_cart_from_redis(
        user_id: Optional[int] = None, 
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从Redis获取购物车数据
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 购物车数据，如果不存在返回None
        """
        # 使用try-except捕获可能的异常，确保程序稳定性
        try:
            # 获取购物车在Redis中的键名
            cart_key = await CartService.get_cart_key(user_id, session_id)
            # 从Redis中获取购物车数据
            cart_data = await redis_client.get(cart_key)
            
            # 如果购物车数据存在
            if cart_data:
                # 将JSON字符串解析为Python字典并返回
                return json.loads(cart_data)
            # 如果购物车数据不存在，返回None
            return None
            
        # 捕获所有异常
        except Exception as e:
            # 记录错误日志，包括错误信息、用户ID和会话ID
            logger.error("Get cart from Redis error", 
                        error=str(e), 
                        user_id=user_id,
                        session_id=session_id)
            # 发生异常时返回None
            return None
    
    @staticmethod
    async def save_cart_to_redis(
        cart_data: Dict[str, Any],
        user_id: Optional[int] = None, 
        session_id: Optional[str] = None,
        expire_minutes: int = 43200  # 30天
    ) -> bool:
        """
        保存购物车数据到Redis
        
        Args:
            cart_data: 购物车数据
            user_id: 用户ID
            session_id: 会话ID
            expire_minutes: 过期时间（分钟）
            
        Returns:
            bool: 是否保存成功
        """
        # 使用try-except捕获可能的异常，确保程序稳定性
        try:
            # 获取购物车在Redis中的键名
            cart_key = await CartService.get_cart_key(user_id, session_id)
            # 将购物车数据保存到Redis，设置过期时间
            await redis_client.setex(
                cart_key, 
                expire_minutes * 60,  # 将分钟转换为秒
                json.dumps(cart_data, default=str)  # 将字典序列化为JSON字符串
            )
            # 保存成功返回True
            return True
            
        # 捕获所有异常
        except Exception as e:
            # 记录错误日志，包括错误信息、用户ID和会话ID
            logger.error("Save cart to Redis error", 
                        error=str(e), 
                        user_id=user_id,
                        session_id=session_id)
            # 保存失败返回False
            return False
    
    @staticmethod
    async def add_to_cart(
        db: AsyncSession,
        product_id: int,
        quantity: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        添加商品到购物车
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            quantity: 数量
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的购物车数据，如果失败返回None
        """
        try:
            # 检查商品是否存在且可购买 (使用模型层Product)
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .where(Product.is_deleted == False)
            )
            product = result.scalar_one_or_none()
            
            if not product or not product.is_available:
                logger.warning("Product not available", product_id=product_id)
                return None
            
            # 检查库存
            stock = await get_cached_stock(product_id)
            if stock is None or stock < quantity:
                logger.warning("Insufficient stock", 
                             product_id=product_id, 
                             requested=quantity, 
                             available=stock)
                return None
            
            # 获取当前购物车数据
            cart_data = await CartService.get_cart_from_redis(user_id, session_id)
            if not cart_data:
                cart_data = {
                    "items": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            # 更新购物车项
            item_key = str(product_id)
            if item_key in cart_data["items"]:
                # 增加现有项的数量
                current_quantity = cart_data["items"][item_key]["quantity"]
                new_quantity = current_quantity + quantity
                
                # 检查增加后的数量是否超过库存
                if new_quantity > stock:
                    logger.warning("Quantity exceeds stock after addition", 
                                 product_id=product_id, 
                                 current_quantity=current_quantity,
                                 added_quantity=quantity,
                                 stock=stock)
                    return None
                
                cart_data["items"][item_key]["quantity"] = new_quantity
                cart_data["items"][item_key]["total_price"] = float(product.price) * new_quantity
            else:
                # 添加新项
                if quantity > stock:
                    logger.warning("Quantity exceeds stock", 
                                 product_id=product_id, 
                                 requested=quantity, 
                                 available=stock)
                    return None
                
                cart_data["items"][item_key] = {
                    "product_id": product_id,
                    "product_name": product.title,
                    "product_image": product.main_image.url if product.main_image else None,
                    "unit_price": float(product.price),
                    "quantity": quantity,
                    "total_price": float(product.price) * quantity,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # 保存到Redis
            await CartService.save_cart_to_redis(cart_data, user_id, session_id)
            
            logger.info("Item added to cart", 
                       product_id=product_id, 
                       quantity=quantity,
                       user_id=user_id,
                       session_id=session_id)
            
            return cart_data
            
        except Exception as e:
            logger.error("Add to cart error", 
                        error=str(e), 
                        product_id=product_id,
                        quantity=quantity,
                        user_id=user_id,
                        session_id=session_id)
            return None
    
    @staticmethod
    async def update_cart_item(
        db: AsyncSession,
        product_id: int,
        quantity: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新购物车商品数量
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            quantity: 新数量
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的购物车数据，如果失败返回None
        """
        try:
            # 检查商品是否存在且可购买 (使用模型层Product)
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .where(Product.is_deleted == False)
            )
            product = result.scalar_one_or_none()
            
            if not product or not product.is_available:
                logger.warning("Product not available", product_id=product_id)
                return None
            
            # 检查库存
            stock = await get_cached_stock(product_id)
            if stock is None or stock < quantity:
                logger.warning("Insufficient stock", 
                             product_id=product_id, 
                             requested=quantity, 
                             available=stock)
                return None
            
            # 获取当前购物车数据
            cart_data = await CartService.get_cart_from_redis(user_id, session_id)
            if not cart_data or str(product_id) not in cart_data["items"]:
                logger.warning("Item not in cart", product_id=product_id)
                return None
            
            # 更新数量
            item_key = str(product_id)
            cart_data["items"][item_key]["quantity"] = quantity
            cart_data["items"][item_key]["total_price"] = float(product.price) * quantity
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # 保存到Redis
            await CartService.save_cart_to_redis(cart_data, user_id, session_id)
            
            logger.info("Cart item updated", 
                       product_id=product_id, 
                       quantity=quantity,
                       user_id=user_id,
                       session_id=session_id)
            
            return cart_data
            
        except Exception as e:
            logger.error("Update cart item error", 
                        error=str(e), 
                        product_id=product_id,
                        quantity=quantity,
                        user_id=user_id,
                        session_id=session_id)
            return None
    
    @staticmethod
    async def remove_from_cart(
        product_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从购物车移除商品
        
        Args:
            product_id: 商品ID
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的购物车数据，如果失败返回None
        """
        try:
            # 获取当前购物车数据
            cart_data = await CartService.get_cart_from_redis(user_id, session_id)
            if not cart_data or str(product_id) not in cart_data["items"]:
                logger.warning("Item not in cart",
                               product_id=product_id)
                return None
            
            # 移除项
            item_key = str(product_id)
            del cart_data["items"][item_key]
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # 保存到Redis
            await CartService.save_cart_to_redis(cart_data, user_id, session_id)
            
            logger.info("Item removed from cart", 
                       product_id=product_id,
                       user_id=user_id,
                       session_id=session_id)
            
            return cart_data
            
        except Exception as e:
            logger.error("Remove from cart error", 
                        error=str(e), 
                        product_id=product_id,
                        user_id=user_id,
                        session_id=session_id)
            return None
    
    @staticmethod
    async def get_cart(
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取购物车数据
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 购物车数据，如果失败返回None
        """
        try:
            return await CartService.get_cart_from_redis(user_id, session_id)
            
        except Exception as e:
            logger.error("Get cart error", 
                        error=str(e), 
                        user_id=user_id,
                        session_id=session_id)
            return None
    
    @staticmethod
    async def clear_cart(
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        清空购物车
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            bool: 是否清空成功
        """
        try:
            cart_key = await CartService.get_cart_key(user_id, session_id)
            await redis_client.delete(cart_key)
            
            logger.info("Cart cleared", 
                       user_id=user_id,
                       session_id=session_id)
            
            return True
            
        except Exception as e:
            logger.error("Clear cart error", 
                        error=str(e), 
                        user_id=user_id,
                        session_id=session_id)
            return False
    
    @staticmethod
    async def merge_carts(
        db: AsyncSession,
        user_id: int,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        合并游客购物车和用户购物车
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 合并后的购物车数据，如果失败返回None
        """
        try:
            # 获取游客购物车
            guest_cart = await CartService.get_cart_from_redis(session_id=session_id)
            if not guest_cart or not guest_cart["items"]:
                return await CartService.get_cart_from_redis(user_id=user_id)
            
            # 获取用户购物车
            user_cart = await CartService.get_cart_from_redis(user_id=user_id)
            if not user_cart:
                user_cart = {
                    "items": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            # 合并购物车项
            for item_key, guest_item in guest_cart["items"].items():
                product_id = guest_item["product_id"]
                guest_quantity = guest_item["quantity"]
                
                # 检查用户购物车中是否已有该商品
                if item_key in user_cart["items"]:
                    # 合并数量（需要检查库存）
                    user_quantity = user_cart["items"][item_key]["quantity"]
                    total_quantity = user_quantity + guest_quantity
                    
                    # 检查库存
                    stock = await get_cached_stock(product_id)
                    if stock is not None and total_quantity <= stock:
                        # 库存充足，合并数量
                        user_cart["items"][item_key]["quantity"] = total_quantity
                        user_cart["items"][item_key]["total_price"] = \
                            guest_item["unit_price"] * total_quantity
                    else:
                        # 库存不足，使用较小的数量
                        max_quantity = min(total_quantity, stock or 0)
                        user_cart["items"][item_key]["quantity"] = max_quantity
                        user_cart["items"][item_key]["total_price"] = \
                            guest_item["unit_price"] * max_quantity
                else:
                    # 直接添加新项
                    user_cart["items"][item_key] = guest_item
            
            user_cart["updated_at"] = datetime.utcnow().isoformat()
            
            # 保存合并后的购物车
            await CartService.save_cart_to_redis(user_cart, user_id=user_id)
            
            # 清除游客购物车
            await CartService.clear_cart(session_id=session_id)
            
            logger.info("Carts merged", 
                       user_id=user_id,
                       session_id=session_id)
            
            return user_cart
            
        except Exception as e:
            logger.error("Merge carts error", 
                        error=str(e), 
                        user_id=user_id,
                        session_id=session_id)
            return None
    
    @staticmethod
    async def sync_cart_to_db(
        db: AsyncSession,
        user_id: int
    ) -> Optional[Cart]:
        """
        同步 Redis购物车 到数据库
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Optional[Cart]: 同步后的数据库购物车对象，如果失败返回None
        """
        try:
            # 获取Redis购物车数据
            cart_data = await CartService.get_cart_from_redis(user_id=user_id)
            if not cart_data:
                return None
            
            async with db.begin():
                # 获取或创建数据库购物车 (使用模型层Cart)
                result = await db.execute(
                    select(Cart).where(Cart.user_id == user_id)
                )
                db_cart = result.scalar_one_or_none()
                
                if not db_cart:
                    db_cart = Cart(user_id=user_id)
                    db.add(db_cart)
                    await db.flush()
                
                # 删除现有的购物车项
                await db.execute(
                    delete(CartItem).where(CartItem.cart_id == db_cart.id)
                )
                
                # 创建新的购物车项 (使用模型层CartItem)
                subtotal = 0.0
                total_quantity = 0
                item_count = 0
                
                for item_data in cart_data["items"].values():
                    cart_item = CartItem(
                        cart_id=db_cart.id,
                        product_id=item_data["product_id"],
                        product_name=item_data["product_name"],
                        product_image=item_data["product_image"],
                        unit_price=item_data["unit_price"],
                        quantity=item_data["quantity"],
                        total_price=item_data["total_price"]
                    )
                    
                    db.add(cart_item)
                    subtotal += item_data["total_price"]
                    total_quantity += item_data["quantity"]
                    item_count += 1
                
                # 更新购物车统计信息
                db_cart.subtotal = subtotal
                db_cart.total_amount = subtotal  # 简化处理，实际应考虑税费、运费等
                db_cart.item_count = item_count
                db_cart.total_quantity = total_quantity
                db_cart.updated_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(db_cart)
                
                logger.info("Cart synced to database", 
                           cart_id=db_cart.id, 
                           user_id=user_id,
                           item_count=item_count)
                
                return db_cart
                
        except Exception as e:
            logger.error("Sync cart to database error", 
                        error=str(e), 
                        user_id=user_id)
            return None
"""
加密工具模块
用于加密存储敏感信息（如数据库密码）
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional


class CryptoManager:
    """加密管理器"""
    
    def __init__(self, key_file: str = None):
        """
        初始化加密管理器
        
        Args:
            key_file: 密钥文件路径，如果为None则使用默认路径
        """
        if key_file is None:
            key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.crypto_key')
        
        self.key_file = key_file
        self._key = None
        self._cipher = None
    
    def _generate_key(self, password: str = None) -> bytes:
        """
        生成加密密钥
        
        Args:
            password: 密码，如果为None则使用机器标识生成
            
        Returns:
            加密密钥
        """
        if password is None:
            # 使用机器标识作为密码（基于机器名和用户名）
            password = f"{os.environ.get('COMPUTERNAME', 'unknown')}_{os.environ.get('USERNAME', 'user')}"
        
        # 使用PBKDF2生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'cims_salt_2024',  # 固定盐值，实际生产环境应随机生成并存储
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _load_or_create_key(self) -> bytes:
        """加载或创建密钥"""
        if self._key is not None:
            return self._key
        
        if os.path.exists(self.key_file):
            # 从文件加载密钥
            with open(self.key_file, 'rb') as f:
                self._key = f.read()
        else:
            # 生成新密钥并保存
            self._key = self._generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self._key)
            # 设置文件权限（仅当前用户可读写）
            os.chmod(self.key_file, 0o600)
        
        return self._key
    
    def _get_cipher(self) -> Fernet:
        """获取加密器"""
        if self._cipher is None:
            key = self._load_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文
            
        Returns:
            密文（base64编码）
        """
        if not plaintext:
            return ""
        
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: 密文（base64编码）
            
        Returns:
            明文
        """
        if not ciphertext:
            return ""
        
        try:
            cipher = self._get_cipher()
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            print(f"解密失败: {e}")
            return ""
    
    def encrypt_dict(self, data: dict, encrypt_keys: list = None) -> dict:
        """
        加密字典中的指定字段
        
        Args:
            data: 原始字典
            encrypt_keys: 需要加密的字段列表，如果为None则加密所有字符串值
            
        Returns:
            加密后的字典
        """
        result = {}
        for key, value in data.items():
            if encrypt_keys is None or key in encrypt_keys:
                if isinstance(value, str) and value:
                    result[key] = self.encrypt(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result
    
    def decrypt_dict(self, data: dict, decrypt_keys: list = None) -> dict:
        """
        解密字典中的指定字段
        
        Args:
            data: 加密后的字典
            decrypt_keys: 需要解密的字段列表，如果为None则解密所有字符串值
            
        Returns:
            解密后的字典
        """
        result = {}
        for key, value in data.items():
            if decrypt_keys is None or key in decrypt_keys:
                if isinstance(value, str) and value:
                    result[key] = self.decrypt(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result


# 全局加密管理器实例
_crypto_manager = None


def get_crypto_manager() -> CryptoManager:
    """获取全局加密管理器实例"""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager


def encrypt_password(password: str) -> str:
    """加密密码"""
    return get_crypto_manager().encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    return get_crypto_manager().decrypt(encrypted_password)


def encrypt_config(config: dict, sensitive_keys: list = None) -> dict:
    """
    加密配置中的敏感字段
    
    Args:
        config: 配置字典
        sensitive_keys: 敏感字段列表，默认为['password', 'api_key', 'secret']
        
    Returns:
        加密后的配置字典
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'api_key', 'secret', 'api_secret']
    
    return get_crypto_manager().encrypt_dict(config, sensitive_keys)


def decrypt_config(config: dict, sensitive_keys: list = None) -> dict:
    """
    解密配置中的敏感字段
    
    Args:
        config: 配置字典
        sensitive_keys: 敏感字段列表，默认为['password', 'api_key', 'secret']
        
    Returns:
        解密后的配置字典
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'api_key', 'secret', 'api_secret']
    
    return get_crypto_manager().decrypt_dict(config, sensitive_keys)


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("加密工具测试")
    print("=" * 60)
    
    crypto = CryptoManager()
    
    # 测试加密解密
    test_password = "my_secret_password_123"
    print(f"\n原始密码: {test_password}")
    
    encrypted = crypto.encrypt(test_password)
    print(f"加密后: {encrypted}")
    
    decrypted = crypto.decrypt(encrypted)
    print(f"解密后: {decrypted}")
    
    # 测试字典加密
    print("\n字典加密测试:")
    config = {
        'host': 'localhost',
        'port': 3306,
        'username': 'root',
        'password': 'secret123',
        'database': 'test'
    }
    print(f"原始配置: {config}")
    
    encrypted_config = encrypt_config(config)
    print(f"加密后: {encrypted_config}")
    
    decrypted_config = decrypt_config(encrypted_config)
    print(f"解密后: {decrypted_config}")
    
    # 验证
    if decrypted == test_password and decrypted_config['password'] == config['password']:
        print("\n✅ 加密解密测试通过！")
    else:
        print("\n❌ 加密解密测试失败！")

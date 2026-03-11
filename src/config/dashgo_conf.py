from configparser import ConfigParser
from pathlib import Path
from typing import List
import platform
import sys


class PathProj:
    ROOT_PATH = Path(__file__).parent.parent
    CONF_FILE_PATH = ROOT_PATH / 'config' / 'dashgo.ini'
    AVATAR_DIR_PATH = (ROOT_PATH / '..' / 'user_data' / 'avatars').resolve()
    AVATAR_DIR_PATH.mkdir(parents=True, exist_ok=True)


conf = ConfigParser()
conf.read(PathProj.CONF_FILE_PATH, encoding='utf-8')


def _get_annotations(dct):
    """兼容 Python 3.14+ 延迟注解求值 (PEP 749)"""
    annotations = dct.get('__annotations__', {})
    if annotations:
        return annotations
    annotate_fn = dct.get('__annotate__') or dct.get('__annotate_func__')
    if annotate_fn:
        try:
            import annotationlib
            return annotationlib.call_annotate_function(annotate_fn, annotationlib.Format.VALUE)
        except ImportError:
            return annotate_fn(1)
    return {}


class BaseMetaConf(type):
    def __new__(cls, name, bases, dct):
        from config.conf_crypto import is_encrypted, decrypt_value, get_master_key

        sub_conf = conf[name]
        for stat_var_name, type_ in _get_annotations(dct).items():
            raw_value = sub_conf.get(stat_var_name)
            if raw_value is None:
                continue
            if is_encrypted(raw_value):
                master_key = get_master_key()
                if not master_key:
                    raise RuntimeError(
                        f'Config value {name}.{stat_var_name} is encrypted but '
                        f'environment variable DASHGO_MASTER_KEY is not set'
                    )
                raw_value = decrypt_value(raw_value, master_key)
            if type_ is List:
                dct[stat_var_name] = raw_value.split()
            elif type_ is bool:
                dct[stat_var_name] = raw_value.strip().lower() in ('true', '1', 'yes')
            else:
                dct[stat_var_name] = type_(raw_value)
        return super().__new__(cls, name, bases, dct)


class LogConf(metaclass=BaseMetaConf):
    LOG_LEVEL: str = 'WARNING'
    HANDLER_CONSOLE: bool = True
    HANDLER_LOG_FILE: bool = False
    LOG_FILE_PATH: str
    MAX_MB_PER_LOG_FILE: int = 50
    MAX_COUNT_LOG_FILE: int = 3


class CommonConf(metaclass=BaseMetaConf):
    ENCRYPT_KEY: str
    DASH_SERVE_LOCALLY: bool
    SYSTEM_IS_UNIX: str = platform.system() != 'Windows'


class LoginConf(metaclass=BaseMetaConf):
    VERIFY_CODE_SHOW_LOGIN_FAIL_COUNT: int = 5
    VERIFY_CODE_CHAR_NUM: int = 4
    JWT_EXPIRED_FORCE_LOGOUT: bool = False


class FlaskConf(metaclass=BaseMetaConf):
    COMPRESS_ALGORITHM: str = 'br'
    COMPRESS_BR_LEVEL: int = 9
    COOKIE_SESSION_SECRET_KEY: str


class ShowConf(metaclass=BaseMetaConf):
    WEB_TITLE: str
    APP_NAME: str


class JwtConf(metaclass=BaseMetaConf):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRE_MINUTES: int = 1440


class ProxyConf(metaclass=BaseMetaConf):
    NGINX_PROXY: bool = False


class OAuth2Conf(metaclass=BaseMetaConf):
    OAuth2AuthorizationCodeExpiresInMinutes: int
    OAuth2AuthorizationCodeLength: int
    OAuth2TokenExpiresInMinutes: int


class ApSchedulerConf(metaclass=BaseMetaConf):
    DATA_EXPIRE_DAY: int
    HOST: str
    PORT: int


class SqlDbConf(metaclass=BaseMetaConf):
    RDB_TYPE: str
    SQLITE_DB_PATH: str
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    DATABASE: str
    POOL_SIZE: int


class ListenTaskConf(metaclass=BaseMetaConf):
    PERIOD_MINTUES: int

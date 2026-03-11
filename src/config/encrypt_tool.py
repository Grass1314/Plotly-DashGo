#!/usr/bin/env python3
"""
DashGo 配置敏感值加密工具。

用法:
  1) 交互式加密单个值:
     python encrypt_tool.py

  2) 一键加密 dashgo.ini 中的预定义敏感字段:
     python encrypt_tool.py --encrypt-ini

  3) 解密验证一个 ENC(...) 值:
     python encrypt_tool.py --decrypt
"""

import argparse
import getpass
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.conf_crypto import decrypt_value, encrypt_value, is_encrypted

SENSITIVE_FIELDS = {
    'CommonConf': ['ENCRYPT_KEY'],
    'FlaskConf': ['COOKIE_SESSION_SECRET_KEY'],
    'JwtConf': ['JWT_SECRET_KEY'],
    'SqlDbConf': ['HOST', 'USER', 'PASSWORD'],
}

INI_PATH = Path(__file__).parent / 'dashgo.ini'


def prompt_master_key() -> str:
    key = getpass.getpass('请输入主密钥 (DASHGO_MASTER_KEY): ')
    if not key:
        print('错误: 主密钥不能为空', file=sys.stderr)
        sys.exit(1)
    return key


def cmd_encrypt_single():
    master_key = prompt_master_key()
    plaintext = input('请输入要加密的明文值: ')
    result = encrypt_value(plaintext, master_key)
    print(f'\n加密结果:\n{result}')
    decrypted = decrypt_value(result, master_key)
    assert decrypted == plaintext, '解密验证失败!'
    print('(解密验证通过)')


def cmd_decrypt_single():
    master_key = prompt_master_key()
    enc_string = input('请输入 ENC(...) 密文: ')
    if not is_encrypted(enc_string):
        print('错误: 输入不是有效的 ENC(...) 格式', file=sys.stderr)
        sys.exit(1)
    plaintext = decrypt_value(enc_string, master_key)
    print(f'\n解密结果:\n{plaintext}')


def cmd_encrypt_ini():
    if not INI_PATH.exists():
        print(f'错误: 找不到配置文件 {INI_PATH}', file=sys.stderr)
        sys.exit(1)

    master_key = prompt_master_key()
    confirm_key = getpass.getpass('请再次输入主密钥确认: ')
    if master_key != confirm_key:
        print('错误: 两次输入不一致', file=sys.stderr)
        sys.exit(1)

    content = INI_PATH.read_text(encoding='utf-8')
    encrypted_count = 0
    skipped_count = 0

    for section, fields in SENSITIVE_FIELDS.items():
        for field in fields:
            pattern = re.compile(
                rf'^(\s*{re.escape(field)}\s*=\s*)(.+)$',
                re.MULTILINE,
            )
            match = pattern.search(content)
            if not match:
                print(f'  [跳过] {section}.{field} — 在配置文件中未找到')
                skipped_count += 1
                continue

            current_value = match.group(2).strip()
            if is_encrypted(current_value):
                print(f'  [跳过] {section}.{field} — 已是加密状态')
                skipped_count += 1
                continue

            enc_value = encrypt_value(current_value, master_key)
            content = pattern.sub(rf'\g<1>{enc_value}', content, count=1)
            print(f'  [加密] {section}.{field}')
            encrypted_count += 1

    if encrypted_count > 0:
        INI_PATH.write_text(content, encoding='utf-8')
        print(f'\n完成: 加密了 {encrypted_count} 个字段, 跳过 {skipped_count} 个')
        print(f'配置文件已更新: {INI_PATH}')
        print(f'\n请确保启动时设置环境变量:')
        print(f'  export DASHGO_MASTER_KEY="你的主密钥"')
    else:
        print(f'\n无需操作: 所有敏感字段已加密或未找到')


def main():
    parser = argparse.ArgumentParser(description='DashGo 配置敏感值加密工具')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--encrypt-ini', action='store_true', help='一键加密 dashgo.ini 中的敏感字段')
    group.add_argument('--decrypt', action='store_true', help='解密验证一个 ENC(...) 值')
    args = parser.parse_args()

    if args.encrypt_ini:
        cmd_encrypt_ini()
    elif args.decrypt:
        cmd_decrypt_single()
    else:
        cmd_encrypt_single()


if __name__ == '__main__':
    main()

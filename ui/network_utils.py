import socket
import requests
import json
from datetime import datetime
import subprocess
import platform
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import os
import struct
import select
import re


class NetworkUtils:
    def __init__(self):
        self.geoip_cache = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.lock = threading.Lock()
        self.cache_file = "geoip_cache.json"
        self.load_cache()

    def load_cache(self):
        """加载地理位置缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.geoip_cache = json.load(f)
                print(f"已加载 {len(self.geoip_cache)} 条地理位置缓存")
        except Exception as e:
            print(f"加载缓存失败: {e}")

    def save_cache(self):
        """保存地理位置缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.geoip_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def get_ip_location(self, ip_address):
        """获取IP地址的地理位置信息 - 增强版本"""
        # 英文到中文的地址映射字典 - 增强版本
        en_to_cn_mapping = {
            # 常见国家和地区组合
            'China Shanghai Shanghai': '中国 上海 上海',
            'China Jiangsu Nanjing': '中国 江苏 南京',
            'China Beijing Beijing': '中国 北京 北京',
            'China Guangdong Guangzhou': '中国 广东 广州',
            'China Guangdong Shenzhen': '中国 广东 深圳',
            'China Zhejiang Hangzhou': '中国 浙江 杭州',
            
            # 常见国家
            'China': '中国',
            'United States': '美国',
            'USA': '美国',
            'Japan': '日本',
            'Korea': '韩国',
            'Singapore': '新加坡',
            'Germany': '德国',
            'France': '法国',
            'United Kingdom': '英国',
            'UK': '英国',
            'Hong Kong': '中国香港',
            'Taiwan': '中国台湾',
            'Macau': '中国澳门',
            
            # 常见地区
            'Shanghai': '上海',
            'Beijing': '北京',
            'Guangdong': '广东',
            'Zhejiang': '浙江',
            'Jiangsu': '江苏',
            'Fujian': '福建',
            'Shandong': '山东',
            'Henan': '河南',
            'Sichuan': '四川',
            'Hubei': '湖北',
            
            # 常见城市
            'Shanghai': '上海',
            'Beijing': '北京',
            'Guangzhou': '广州',
            'Shenzhen': '深圳',
            'Hangzhou': '杭州',
            'Nanjing': '南京',
            'Chengdu': '成都',
            'Wuhan': '武汉',
            'Xiamen': '厦门',
            'Qingdao': '青岛',
            
            # 运营商信息
            'China Unicom': '中国联通',
            'China Unicom CnNet': '中国联通',
            'China Telecom': '中国电信',
            'China Mobile': '中国移动',
            
            # 其他常见英文词汇
            'unknown': '未知',
            'Unknown': '未知',
            'timeout': '超时',
            'Timeout': '超时',
            'private': '私有',
            'Private': '私有',
            'reserved': '保留',
            'Reserved': '保留',
            'loopback': '环回',
            'Loopback': '环回'
        }
        
        # 检查缓存
        if ip_address in self.geoip_cache:
            return self.geoip_cache[ip_address]

        # 处理特殊IP地址
        special_ips = {
            '*': {
                'country': '未知路由',
                'region': '网络设备',
                'city': '未知路由',
                'isp': '防火墙或路由器',
                'country_code': '***',
                'timezone': '未知',
                'lat': '',
                'lon': ''
            },
            '请求超时': {
                'country': '网络超时',
                'region': '无法到达',
                'city': '超时节点',
                'isp': '网络设备',
                'country_code': 'TIMEOUT',
                'timezone': '未知',
                'lat': '',
                'lon': ''
            },
            '超时': {
                'country': '网络超时',
                'region': '无法到达',
                'city': '超时节点',
                'isp': '网络设备',
                'country_code': 'TIMEOUT',
                'timezone': '未知',
                'lat': '',
                'lon': ''
            },
            '未知': {
                'country': '未知位置',
                'region': '无法解析',
                'city': '未知节点',
                'isp': '未知运营商',
                'country_code': 'UNKNOWN',
                'timezone': '未知',
                'lat': '',
                'lon': ''
            },
            '解析失败': {
                'country': '解析失败',
                'region': 'DNS错误',
                'city': '无法解析',
                'isp': 'DNS服务器',
                'country_code': 'DNSERR',
                'timezone': '未知',
                'lat': '',
                'lon': ''
            }
        }

        if ip_address in special_ips:
            location_info = special_ips[ip_address]
            
            # 将英文地址转换为中文
            for key in ['country', 'region', 'city', 'isp']:
                if key in location_info and location_info[key]:
                    # 检查整个字符串是否在映射中
                    if location_info[key] in en_to_cn_mapping:
                        location_info[key] = en_to_cn_mapping[location_info[key]]
                    else:
                        # 检查部分匹配（处理如"China Shanghai"这样的组合）
                        parts = location_info[key].split()
                        for i, part in enumerate(parts):
                            if part in en_to_cn_mapping:
                                parts[i] = en_to_cn_mapping[part]
                        location_info[key] = ' '.join(parts)
            
            self.geoip_cache[ip_address] = location_info
            return location_info

        # 处理私有IP地址
        if self.is_private_ip(ip_address):
            location_info = self._get_private_ip_info(ip_address)
            
            # 将英文地址转换为中文
            for key in ['country', 'region', 'city', 'isp']:
                if key in location_info and location_info[key]:
                    # 检查整个字符串是否在映射中
                    if location_info[key] in en_to_cn_mapping:
                        location_info[key] = en_to_cn_mapping[location_info[key]]
                    else:
                        # 检查部分匹配（处理如"China Shanghai"这样的组合）
                        parts = location_info[key].split()
                        for i, part in enumerate(parts):
                            if part in en_to_cn_mapping:
                                parts[i] = en_to_cn_mapping[part]
                        location_info[key] = ' '.join(parts)
            
            self.geoip_cache[ip_address] = location_info
            return location_info

        # 处理公网IP
        location_info = self._get_public_ip_location(ip_address)
        
        # 将英文地址转换为中文 - 增强版本
        for key in ['country', 'region', 'city', 'isp']:
            if key in location_info and location_info[key]:
                # 检查整个字符串是否在映射中（优先处理组合形式）
                if location_info[key] in en_to_cn_mapping:
                    location_info[key] = en_to_cn_mapping[location_info[key]]
                else:
                    # 检查部分匹配（处理如"China Shanghai"这样的组合）
                    parts = location_info[key].split()
                    for i, part in enumerate(parts):
                        if part in en_to_cn_mapping:
                            parts[i] = en_to_cn_mapping[part]
                    # 重建字符串
                    location_info[key] = ' '.join(parts)
                    
                    # 额外处理：移除重复的中国前缀
                    if location_info[key].startswith('中国 中国'):
                        location_info[key] = location_info[key].replace('中国 中国', '中国', 1)
                    # 处理常见的地址组合格式
                    location_info[key] = location_info[key].replace('China Shanghai', '中国 上海')
                    location_info[key] = location_info[key].replace('China Beijing', '中国 北京')
                    location_info[key] = location_info[key].replace('China Jiangsu', '中国 江苏')
                    location_info[key] = location_info[key].replace('China Guangdong', '中国 广东')
                    location_info[key] = location_info[key].replace('China Zhejiang', '中国 浙江')
                    location_info[key] = location_info[key].replace('China Fujian', '中国 福建')
                    
                    # 处理运营商信息
                    location_info[key] = location_info[key].replace('China Unicom', '中国联通')
                    location_info[key] = location_info[key].replace('China Telecom', '中国电信')
                    location_info[key] = location_info[key].replace('China Mobile', '中国移动')
        
        self.geoip_cache[ip_address] = location_info
        return location_info

    def _get_public_ip_location(self, ip_address):
        """获取公网IP地址的地理位置"""
        location_info = None

        # 尝试多个地理位置API
        apis = [
            self._get_ipapi_co,
            self._get_ip_api_com,
            self._get_ipinfo_io
        ]

        for api_func in apis:
            try:
                location_info = api_func(ip_address)
                if location_info and location_info['country'] != '未知':
                    # 验证数据的完整性
                    if self._validate_location_info(location_info):
                        break
            except:
                continue

        # 如果所有API都失败或数据不完整，使用改进的默认信息
        if not location_info or not self._validate_location_info(location_info):
            location_info = self._get_fallback_location(ip_address)

        return location_info

    def _get_fallback_location(self, ip_address):
        """获取备用的地理位置信息"""
        # 根据IP段提供更详细的信息
        first_octet = int(ip_address.split('.')[0])

        # 常见IP段信息
        ip_ranges = {
            1: {'region': '北美', 'isp': 'ARIN'},
            2: {'region': '欧洲', 'isp': 'RIPE NCC'},
            3: {'region': '北美', 'isp': 'ARIN'},
            4: {'region': '北美', 'isp': 'ARIN'},
            5: {'region': '欧洲', 'isp': 'RIPE NCC'},
            8: {'region': '北美', 'isp': 'ARIN'},
            9: {'region': '北美', 'isp': 'ARIN'},
            11: {'region': '北美', 'isp': 'ARIN'},
            12: {'region': '北美', 'isp': 'ARIN'},
            13: {'region': '北美', 'isp': 'ARIN'},
            14: {'region': '亚太', 'isp': 'APNIC'},
            16: {'region': '北美', 'isp': 'ARIN'},
            17: {'region': '北美', 'isp': 'ARIN'},
            18: {'region': '北美', 'isp': 'ARIN'},
            19: {'region': '北美', 'isp': 'ARIN'},
            20: {'region': '北美', 'isp': 'ARIN'},
            21: {'region': '北美', 'isp': 'ARIN'},
            22: {'region': '北美', 'isp': 'ARIN'},
            23: {'region': '北美', 'isp': 'ARIN'},
            24: {'region': '北美', 'isp': 'ARIN'},
            25: {'region': '欧洲', 'isp': 'RIPE NCC'},
            26: {'region': '北美', 'isp': 'ARIN'},
            28: {'region': '北美', 'isp': 'ARIN'},
            29: {'region': '北美', 'isp': 'ARIN'},
            30: {'region': '北美', 'isp': 'ARIN'},
            31: {'region': '欧洲', 'isp': 'RIPE NCC'},
            32: {'region': '北美', 'isp': 'ARIN'},
            33: {'region': '北美', 'isp': 'ARIN'},
            34: {'region': '北美', 'isp': 'ARIN'},
            35: {'region': '北美', 'isp': 'ARIN'},
            36: {'region': '亚太', 'isp': 'APNIC'},
            37: {'region': '欧洲', 'isp': 'RIPE NCC'},
            38: {'region': '北美', 'isp': 'ARIN'},
            39: {'region': '亚太', 'isp': 'APNIC'},
            40: {'region': '北美', 'isp': 'ARIN'},
            42: {'region': '亚太', 'isp': 'APNIC'},
            43: {'region': '亚太', 'isp': 'APNIC'},
            45: {'region': '北美', 'isp': 'ARIN'},
            46: {'region': '欧洲', 'isp': 'RIPE NCC'},
            47: {'region': '北美', 'isp': 'ARIN'},
            48: {'region': '北美', 'isp': 'ARIN'},
            49: {'region': '亚太', 'isp': 'APNIC'},
            50: {'region': '北美', 'isp': 'ARIN'},
            51: {'region': '欧洲', 'isp': 'RIPE NCC'},
            52: {'region': '北美', 'isp': 'ARIN'},
            53: {'region': '欧洲', 'isp': 'RIPE NCC'},
            54: {'region': '北美', 'isp': 'ARIN'},
            55: {'region': '北美', 'isp': 'ARIN'},
            56: {'region': '北美', 'isp': 'ARIN'},
            57: {'region': '欧洲', 'isp': 'RIPE NCC'},
            58: {'region': '亚太', 'isp': 'APNIC'},
            59: {'region': '亚太', 'isp': 'APNIC'},
            60: {'region': '亚太', 'isp': 'APNIC'},
            61: {'region': '亚太', 'isp': 'APNIC'},
            62: {'region': '欧洲', 'isp': 'RIPE NCC'},
            63: {'region': '北美', 'isp': 'ARIN'},
            64: {'region': '北美', 'isp': 'ARIN'},
            65: {'region': '北美', 'isp': 'ARIN'},
            66: {'region': '北美', 'isp': 'ARIN'},
            67: {'region': '北美', 'isp': 'ARIN'},
            68: {'region': '北美', 'isp': 'ARIN'},
            69: {'region': '北美', 'isp': 'ARIN'},
            70: {'region': '北美', 'isp': 'ARIN'},
            71: {'region': '北美', 'isp': 'ARIN'},
            72: {'region': '北美', 'isp': 'ARIN'},
            73: {'region': '北美', 'isp': 'ARIN'},
            74: {'region': '北美', 'isp': 'ARIN'},
            75: {'region': '北美', 'isp': 'ARIN'},
            76: {'region': '北美', 'isp': 'ARIN'},
            77: {'region': '欧洲', 'isp': 'RIPE NCC'},
            78: {'region': '欧洲', 'isp': 'RIPE NCC'},
            79: {'region': '欧洲', 'isp': 'RIPE NCC'},
            80: {'region': '欧洲', 'isp': 'RIPE NCC'},
            81: {'region': '欧洲', 'isp': 'RIPE NCC'},
            82: {'region': '欧洲', 'isp': 'RIPE NCC'},
            83: {'region': '欧洲', 'isp': 'RIPE NCC'},
            84: {'region': '欧洲', 'isp': 'RIPE NCC'},
            85: {'region': '欧洲', 'isp': 'RIPE NCC'},
            86: {'region': '欧洲', 'isp': 'RIPE NCC'},
            87: {'region': '欧洲', 'isp': 'RIPE NCC'},
            88: {'region': '欧洲', 'isp': 'RIPE NCC'},
            89: {'region': '欧洲', 'isp': 'RIPE NCC'},
            90: {'region': '欧洲', 'isp': 'RIPE NCC'},
            91: {'region': '欧洲', 'isp': 'RIPE NCC'},
            92: {'region': '欧洲', 'isp': 'RIPE NCC'},
            93: {'region': '欧洲', 'isp': 'RIPE NCC'},
            94: {'region': '欧洲', 'isp': 'RIPE NCC'},
            95: {'region': '欧洲', 'isp': 'RIPE NCC'},
            96: {'region': '北美', 'isp': 'ARIN'},
            97: {'region': '北美', 'isp': 'ARIN'},
            98: {'region': '北美', 'isp': 'ARIN'},
            99: {'region': '北美', 'isp': 'ARIN'},
            100: {'region': '北美', 'isp': 'ARIN'}
        }

        range_info = ip_ranges.get(first_octet, {'region': '未知地区', 'isp': '未知运营商'})

        return {
            'country': f'IP段 {first_octet}.x.x.x',
            'region': range_info['region'],
            'city': '网络节点',
            'isp': range_info['isp'],
            'country_code': f'NET{first_octet}',
            'timezone': '未知',
            'lat': '',
            'lon': ''
        }

    def _validate_location_info(self, location_info):
        """验证地理位置信息的完整性"""
        if not location_info:
            return False

        required_fields = ['country', 'region', 'city', 'isp']
        for field in required_fields:
            if not location_info.get(field) or location_info[field] == '未知':
                return False

        # 检查是否都是默认值
        if (location_info['country'] == '未知' and
                location_info['region'] == '未知' and
                location_info['city'] == '未知'):
            return False

        return True



    def _get_private_ip_info(self, ip_address):
        """获取私有IP地址的详细信息"""
        ip_num = self.ip_to_int(ip_address)

        # 10.x.x.x 网段
        if self.ip_to_int('10.0.0.0') <= ip_num <= self.ip_to_int('10.255.255.255'):
            return {
                'country': '私有网络',
                'region': 'A类私网',
                'city': f'10.x.x.x网段',
                'isp': '内部网络',
                'country_code': 'PRIVATE-A',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

        # 172.16.x.x - 172.31.x.x 网段
        elif self.ip_to_int('172.16.0.0') <= ip_num <= self.ip_to_int('172.31.255.255'):
            second_octet = ip_address.split('.')[1]
            return {
                'country': '私有网络',
                'region': 'B类私网',
                'city': f'172.{second_octet}.x.x网段',
                'isp': '内部网络',
                'country_code': 'PRIVATE-B',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

        # 192.168.x.x 网段
        elif self.ip_to_int('192.168.0.0') <= ip_num <= self.ip_to_int('192.168.255.255'):
            second_octet = ip_address.split('.')[1]
            third_octet = ip_address.split('.')[2]
            return {
                'country': '私有网络',
                'region': 'C类私网',
                'city': f'192.168.{third_octet}.x网段',
                'isp': '内部网络',
                'country_code': 'PRIVATE-C',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

        # 127.x.x.x 环回地址
        elif self.ip_to_int('127.0.0.0') <= ip_num <= self.ip_to_int('127.255.255.255'):
            return {
                'country': '本地主机',
                'region': '环回地址',
                'city': '本机',
                'isp': '操作系统',
                'country_code': 'LOOPBACK',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

        # 169.254.x.x 链路本地
        elif self.ip_to_int('169.254.0.0') <= ip_num <= self.ip_to_int('169.254.255.255'):
            return {
                'country': '链路本地',
                'region': '自动配置',
                'city': 'APIPA地址',
                'isp': 'DHCP失败',
                'country_code': 'LINKLOCAL',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

        # 其他私有地址
        else:
            return {
                'country': '私有网络',
                'region': '内部地址',
                'city': '私有IP',
                'isp': '内部网络',
                'country_code': 'PRIVATE',
                'timezone': '本地时间',
                'lat': '',
                'lon': ''
            }

    def is_private_ip(self, ip_address):
        """检查是否为私有IP地址"""
        try:
            ip = ip_address.split('.')
            if len(ip) != 4:
                return False

            first = int(ip[0])
            second = int(ip[1])

            # 10.0.0.0/8
            if first == 10:
                return True

            # 172.16.0.0/12
            if first == 172 and 16 <= second <= 31:
                return True

            # 192.168.0.0/16
            if first == 192 and second == 168:
                return True

            # 127.0.0.0/8 (环回地址)
            if first == 127:
                return True

            # 169.254.0.0/16 (链路本地)
            if first == 169 and second == 254:
                return True

            return False
        except:
            return False

    def ip_to_int(self, ip):
        """将IP地址转换为整数"""
        try:
            return struct.unpack("!I", socket.inet_aton(ip))[0]
        except:
            return 0

    def _get_ipapi_co(self, ip_address):
        """使用ipapi.co API获取地理位置信息"""
        try:
            url = f"http://ipapi.co/{ip_address}/json/"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', '未知'),
                    'region': data.get('region', '未知'),
                    'city': data.get('city', '未知'),
                    'isp': data.get('org', '未知'),
                    'country_code': data.get('country_code', 'XX'),
                    'timezone': data.get('timezone', '未知'),
                    'lat': data.get('latitude', ''),
                    'lon': data.get('longitude', '')
                }
        except:
            pass
        return None

    def _get_ip_api_com(self, ip_address):
        """使用ip-api.com API获取地理位置信息"""
        try:
            url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', '未知'),
                        'region': data.get('regionName', '未知'),
                        'city': data.get('city', '未知'),
                        'isp': data.get('isp', '未知'),
                        'country_code': data.get('countryCode', 'XX'),
                        'timezone': data.get('timezone', '未知'),
                        'lat': data.get('lat', ''),
                        'lon': data.get('lon', '')
                    }
        except:
            pass
        return None

    def _get_ipinfo_io(self, ip_address):
        """使用ipinfo.io API获取地理位置信息"""
        try:
            url = f"http://ipinfo.io/{ip_address}/json"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country', '未知'),
                    'region': data.get('region', '未知'),
                    'city': data.get('city', '未知'),
                    'isp': data.get('org', '未知'),
                    'country_code': data.get('country', 'XX'),
                    'timezone': data.get('timezone', '未知'),
                    'lat': data.get('lat', ''),
                    'lon': data.get('lon', '')
                }
        except:
            pass
        return None

    def format_location_string(self, location_info):
        """格式化地理位置字符串"""
        if not location_info:
            return "未知"

        country = location_info.get('country', '未知')
        region = location_info.get('region', '未知')
        city = location_info.get('city', '未知')

        # 移除重复信息
        parts = []
        if country and country != '未知':
            parts.append(country)
        if region and region != country and region != '未知':
            parts.append(region)
        if city and city != region and city != '未知':
            parts.append(city)

        return ' - '.join(parts) if parts else '未知'

    def parse_windows_traceroute_line(self, line):
        """解析Windows tracert输出行"""
        try:
            if not line or not line[0].isdigit():
                return None

            parts = line.split()
            if len(parts) < 2:
                return None

            hop = int(parts[0])
            
            # 查找延迟值（改进的解析逻辑）
            delay = -1
            
            # 1. 检查位置3的延迟值（最常见的位置）
            if len(parts) > 3:
                third_part = parts[3]
                if third_part != '*':
                    # 提取数字部分，去除ms后缀和特殊字符
                    clean_part = third_part.replace('ms', '').replace('毫秒', '').replace('<', '').replace('>', '').strip()
                    if clean_part and clean_part.replace('.', '', 1).isdigit():
                        delay = float(clean_part)
                        print(f"Found delay at position 3: {delay}")
            
            # 2. 检查位置4的延迟值（备用位置）
            if delay == -1 and len(parts) > 4:
                fourth_part = parts[4]
                if fourth_part != '*':
                    clean_part = fourth_part.replace('ms', '').replace('毫秒', '').replace('<', '').replace('>', '').strip()
                    if clean_part and clean_part.replace('.', '', 1).isdigit():
                        delay = float(clean_part)
                        print(f"Found delay at position 4: {delay}")
            
            # 3. 检查位置5的延迟值（另一个备用位置）
            if delay == -1 and len(parts) > 5:
                fifth_part = parts[5]
                if fifth_part != '*':
                    clean_part = fifth_part.replace('ms', '').replace('毫秒', '').replace('<', '').replace('>', '').strip()
                    if clean_part and clean_part.replace('.', '', 1).isdigit():
                        delay = float(clean_part)
                        print(f"Found delay at position 5: {delay}")
            
            # 4. 检查位置2的延迟值（备用）
            if delay == -1 and len(parts) > 2:
                second_part = parts[2]
                clean_part = second_part.replace('ms', '').replace('毫秒', '').replace('<', '').replace('*', '').strip()
                if clean_part and clean_part.replace('.', '', 1).isdigit():
                    delay = float(clean_part)
                    print(f"Found delay at position 2: {delay}")
            
            # 提取IP地址（通常在倒数第二或第三位置）
            ip = "*"
            for i in range(len(parts) - 1, 1, -1):
                if self.is_valid_ip(parts[i]) or parts[i] == '*':
                    ip = parts[i]
                    break
            
            # 提取跳数
            try:
                hop = int(parts[0])
                # 获取地理位置信息
                location_info = self.get_ip_location(ip)
                # 格式化位置字符串
                if isinstance(location_info, dict):
                    location = f"{location_info.get('country', '')} - {location_info.get('region', '')} - {location_info.get('city', '')}"
                    # 移除空字段和多余的连字符
                    location = location.replace(' -  - ', ' ').replace(' - ', ' ').strip()
                    if location.startswith('- '):
                        location = location[2:]
                    isp = location_info.get('isp', '未知')
                else:
                    location = "未知"
                    isp = "未知"
                
                return (hop, ip, delay, location, isp)
            except ValueError:
                return None
        except Exception:
            return None

    def traceroute(self, hostname, max_hops=64, timeout=1, callback=None, process_callback=None):
        """系统traceroute命令，支持实时回调
        
        :param hostname: 目标主机名或IP
        :param max_hops: 最大跳数
        :param timeout: 超时时间（秒）
        :param callback: 实时结果回调函数
        :param process_callback: 进程回调函数，用于传递进程引用以便取消操作
        :return: 路由跟踪结果列表
        """
        system = platform.system().lower()
        results = []

        try:
            if system == 'windows':
                # 按照要求的格式执行: tracert -d -w [超时时间] -h [最大跳数] [hostname]
                # Windows tracert的-w参数单位为毫秒，但需要确保值为整数
                timeout_ms = int(timeout * 1000)
                # 确保超时时间在合理范围内
                timeout_ms = max(1, min(timeout_ms, 65535))
                cmd = ['tracert', '-d', '-w', str(timeout_ms), '-h', str(max_hops), hostname]
            else:
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), '-q', '1', hostname]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 通过回调函数传递进程引用，以便GUI层可以取消进程
            if process_callback:
                process_callback(process)

            lines = []
            for line in iter(process.stdout.readline, ''):
                stripped_line = line.strip()
                lines.append(stripped_line)
                # 添加实时输出调试信息
                print(f"Traceroute output: {stripped_line}")
                
                # 实时处理Windows tracert输出行
                if system == 'windows' and callback and stripped_line and stripped_line[0].isdigit():
                    # 立即解析并通过回调函数返回结果
                    hop_result = self.parse_windows_traceroute_line(stripped_line)
                    if hop_result:
                        callback(hop_result)

            process.wait()

            # 改进错误处理机制
            if process.returncode != 0 and not lines:
                stderr_lines = []
                for line in iter(process.stderr.readline, ''):
                    stderr_lines.append(line.strip())
                error_output = '\n'.join(stderr_lines)
                return [(-1, "执行失败", 0, f"命令执行错误: {error_output}")]

            # 处理Windows的tracert输出，确保捕获所有跳数
            if system == 'windows':
                # 收集所有已解析的跳数，避免重复
                parsed_hops = {}
                for line in lines:
                    if line and line[0].isdigit():
                        hop_result = self.parse_windows_traceroute_line(line)
                        if hop_result:
                            parsed_hops[hop_result[0]] = hop_result  # 直接使用跳数作为键
                
                # 按跳数顺序添加所有结果（包括超时的）
                for hop in sorted(parsed_hops.keys()):
                    results.append(parsed_hops[hop])
            else:
                # 解析Unix/Linux输出格式
                for line in lines:
                    if not line:
                        continue

                    # 解析不同系统的输出格式
                    hop_info = self.parse_traceroute_output(line, system)
                    if hop_info:
                        hop, ip, delay = hop_info

                        # 获取地理位置
                        location_info = self.get_ip_location(ip)
                        location_str = self.format_location_string(location_info)

                        results.append((hop, ip, delay, location_str))

                # 如果没有解析到任何结果，尝试另一种解析方式
                if not results:
                    for line in lines:
                        # 尝试更通用的解析方式
                        generic_result = self.parse_generic_traceroute_line(line)
                        if generic_result:
                            results.append(generic_result)

            return results

        except Exception as e:
            return [(-1, f"错误: {str(e)}", 0, "执行异常")]

    def parse_traceroute_output(self, line, system):
        """解析系统traceroute输出"""
        try:
            if system == 'windows':
                # Windows tracert 输出解析
                if line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    parts = line.split()
                    if len(parts) >= 5:
                        hop = int(parts[0])
                        
                        # 查找有效的延迟值（通常在位置2、4、6）
                        delays = []
                        for i in range(2, min(len(parts), 8), 2):  # 检查位置2、4、6
                            if parts[i] != '*':
                                # 提取数字部分，去除ms后缀
                                delay_num = ''.join(filter(str.isdigit, parts[i]))
                                if delay_num:
                                    delays.append(int(delay_num))
                        
                        # 取第一个有效延迟值或平均值
                        if delays:
                            delay = delays[0]  # 使用第一个有效延迟值
                        else:
                            delay = -1  # 表示超时
                        
                        # 查找IP地址（通常在最后）
                        ip = parts[-1]
                        # 检查IP是否有效
                        if self.is_valid_ip(ip) or ip == "*":
                            return hop, ip, delay

            else:
                # Unix/Linux traceroute 输出解析
                if line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    parts = line.split()
                    if len(parts) >= 2:
                        hop = int(parts[0])
                        ip = parts[1]
                        if ip.startswith('(') and ip.endswith(')'):
                            ip = ip[1:-1]

                        if not self.is_valid_ip(ip):
                            # 查找行中是否有有效的IP地址
                            for part in parts:
                                if self.is_valid_ip(part):
                                    ip = part
                                    break
                            else:
                                return None

                        delay = 0
                        for part in parts:
                            if part.endswith('ms'):
                                try:
                                    delay_str = part.replace('ms', '')
                                    delay = float(delay_str)
                                    break
                                except:
                                    pass

                        return hop, ip, delay

            return None
        except:
            return None

    def parse_generic_traceroute_line(self, line):
        """通用的traceroute行解析方法"""
        try:
            # 查找行中的IP地址
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, line)
            
            # 查找跳数
            hop_match = re.match(r'^\s*(\d+)', line)
            if hop_match:
                hop = int(hop_match.group(1))
            else:
                return None
                
            # 查找延迟
            delay_match = re.search(r'(\d+(?:\.\d+)?)\s*ms', line)
            delay = float(delay_match.group(1)) if delay_match else 0
            
            # 获取第一个有效的IP地址
            ip = None
            for potential_ip in ips:
                if self.is_valid_ip(potential_ip):
                    ip = potential_ip
                    break
                    
            if not ip and '*' in line:
                ip = '*'
                
            if ip:
                location_info = self.get_ip_location(ip)
                location_str = self.format_location_string(location_info)
                return (hop, ip, delay, location_str)
                
        except Exception as e:
            pass
            
        return None

    def is_valid_ip(self, ip):
        """检查是否为有效的IP地址"""
        try:
            if ip in ['*', '请求超时', '超时', '未知']:
                return False
            socket.inet_aton(ip)
            return True
        except:
            return False

    def ping_test(self, hostname, count=4):
        """执行ping测试"""
        system = platform.system().lower()

        try:
            if system == 'windows':
                cmd = ['ping', '-n', str(count), hostname]
            else:
                cmd = ['ping', '-c', str(count), hostname]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            return stdout

        except Exception as e:
            return f"Ping测试失败: {str(e)}"

    def debug_traceroute(self, hostname, max_hops=64, timeout=2):
        """调试traceroute输出"""
        system = platform.system().lower()
        print(f"系统类型: {system}")
        print(f"目标主机: {hostname}")

        try:
            if system == 'windows':
                cmd = ['tracert', '-h', str(max_hops), '-w', str(timeout * 1000), hostname]
            else:
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), '-q', '1', hostname]

            print(f"执行命令: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            print("=== 标准输出 ===")
            print(stdout)
            print("=== 错误输出 ===")
            print(stderr)
            print("=== 返回码 ===")
            print(process.returncode)

            return stdout, stderr

        except Exception as e:
            print(f"执行异常: {e}")
            return None, str(e)

    def __del__(self):
        """析构函数，保存缓存"""
        try:
            self.executor.shutdown(wait=False)
            self.save_cache()
        except:
            pass


# 创建全局实例
network_utils = NetworkUtils()
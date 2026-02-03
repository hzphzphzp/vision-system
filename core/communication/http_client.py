#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP REST API客户端模块

实现HTTP客户端功能，支持GET/POST/PUT/DELETE等REST API调用。

功能特性:
- 常用HTTP方法支持
- JSON请求/响应
- 请求头/认证
- 超时和重试

Usage:
    from core.communication import HTTPClient

    http = HTTPClient()

    # GET请求
    response = http.get("https://api.example.com/data")

    # POST请求
    response = http.post("https://api.example.com/data", json={"key": "value"})

    # 带认证
    http.set_auth("username", "password")
"""

import logging
import os
import sys
from typing import Any, Callable, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import ConnectionState, ProtocolBase

logger = logging.getLogger("HTTPClient")


class HTTPClient(ProtocolBase):
    """HTTP REST API客户端类

    提供HTTP客户端功能，支持常用的REST API调用。
    """

    protocol_name = "HTTPClient"

    def __init__(self):
        super().__init__()
        self._session: Optional[requests.Session] = None
        self._base_url = ""
        self._timeout = 30
        self._verify_ssl = True
        self._retry_count = 0

    def connect(self, config: Dict[str, Any]) -> bool:
        """初始化HTTP会话

        Args:
            config: 配置
                - base_url: 基础URL
                - timeout: 请求超时（秒）
                - verify_ssl: 是否验证SSL
                - retry_count: 重试次数
                - proxies: 代理配置
                - headers: 默认请求头

        Returns:
            bool: 是否成功
        """
        self._base_url = config.get("base_url", "").rstrip("/")
        self._timeout = config.get("timeout", 30)
        self._verify_ssl = config.get("verify_ssl", True)
        self._retry_count = config.get("retry_count", 0)
        proxies = config.get("proxies", None)
        headers = config.get("headers", {})

        self._config = config
        self.set_state(ConnectionState.CONNECTED)

        try:
            self._session = requests.Session()

            if proxies:
                self._session.proxies = proxies

            if headers:
                self._session.headers.update(headers)

            retry_strategy = Retry(
                total=self._retry_count,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

            logger.info(
                f"[HTTPClient] 会话已初始化: {self._base_url or '无基础URL'}"
            )
            return True

        except Exception as e:
            self.set_state(ConnectionState.ERROR)
            logger.error(f"[HTTPClient] 初始化失败: {e}")
            self._emit("on_error", str(e))
            return False

    def disconnect(self):
        """关闭会话"""
        if self._session:
            try:
                self._session.close()
            except Exception as e:
                logger.debug(f"[HTTPClient] 关闭会话时发生异常: {e}")
            self._session = None

        self.set_state(ConnectionState.DISCONNECTED)
        self._emit = lambda *args, **kwargs: None  # 断开回调引用
        self.clear_callbacks()
        logger.info("[HTTPClient] 会话已关闭")

    def set_auth(self, username: str, password: str, auth_type: str = "basic"):
        """设置认证

        Args:
            username: 用户名
            password: 密码
            auth_type: 认证类型（basic, digest, bearer）
        """
        if not self._session:
            logger.warning("[HTTPClient] 请先调用connect")
            return

        if auth_type == "basic":
            from requests.auth import HTTPBasicAuth

            self._session.auth = HTTPBasicAuth(username, password)
        elif auth_type == "digest":
            from requests.auth import HTTPDigestAuth

            self._session.auth = HTTPDigestAuth(username, password)
        elif auth_type == "bearer":
            self._session.headers["Authorization"] = f"Bearer {password}"

    def set_token(self, token: str, token_type: str = "Bearer"):
        """设置Bearer Token"""
        if self._session:
            self._session.headers["Authorization"] = f"{token_type} {token}"

    def get(self, url: str = "", params: Dict = None, **kwargs) -> Dict:
        """GET请求"""
        return self._request("GET", url, params=params, **kwargs)

    def post(
        self, url: str = "", data: Any = None, json: Dict = None, **kwargs
    ) -> Dict:
        """POST请求"""
        return self._request("POST", url, data=data, json=json, **kwargs)

    def put(self, url: str = "", data: Any = None, **kwargs) -> Dict:
        """PUT请求"""
        return self._request("PUT", url, data=data, **kwargs)

    def patch(self, url: str = "", data: Any = None, **kwargs) -> Dict:
        """PATCH请求"""
        return self._request("PATCH", url, data=data, **kwargs)

    def delete(self, url: str = "", **kwargs) -> Dict:
        """DELETE请求"""
        return self._request("DELETE", url, **kwargs)

    def _request(self, method: str, url: str = "", **kwargs) -> Dict:
        """发送HTTP请求

        Returns:
            Dict: {
                "success": bool,
                "status_code": int,
                "data": Any,
                "text": str,
                "headers": Dict,
                "elapsed": float,
                "error": str
            }
        """
        if not self._session:
            return {"success": False, "error": "会话未初始化"}

        full_url = (
            f"{self._base_url}/{url.lstrip('/')}"
            if self._base_url and not url.startswith(("http://", "https://"))
            else url
        )

        timeout = kwargs.pop("timeout", self._timeout)
        params = kwargs.get("params", {})

        try:
            response = self._session.request(
                method=method,
                url=full_url,
                timeout=timeout,
                verify=self._verify_ssl,
                **kwargs,
            )

            result = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "text": response.text,
                "headers": dict(response.headers),
                "elapsed": response.elapsed.total_seconds(),
            }

            try:
                result["data"] = response.json()
            except:
                result["data"] = response.text

            if not result["success"]:
                result["error"] = f"HTTP {response.status_code}"

            self._emit("on_response", result)
            return result

        except requests.Timeout:
            error_msg = f"请求超时 ({timeout}s)"
            logger.error(f"[HTTPClient] {error_msg}")
            return {"success": False, "error": error_msg}

        except requests.ConnectionError as e:
            error_msg = f"连接失败: {e}"
            logger.error(f"[HTTPClient] {error_msg}")
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"请求异常: {e}"
            logger.error(f"[HTTPClient] {error_msg}")
            return {"success": False, "error": error_msg}

    def download(self, url: str, save_path: str) -> bool:
        """下载文件

        Args:
            url: 文件URL
            save_path: 保存路径

        Returns:
            bool: 是否下载成功
        """
        try:
            response = self._session.get(
                url, timeout=self._timeout, stream=True
            )
            response.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"[HTTPClient] 文件已下载: {save_path}")
            return True

        except Exception as e:
            logger.error(f"[HTTPClient] 下载失败: {e}")
            return False

    def upload(
        self,
        url: str,
        file_path: str,
        field_name: str = "file",
        data: Dict = None,
    ) -> Dict:
        """上传文件

        Args:
            url: 上传URL
            file_path: 文件路径
            field_name: 表单字段名
            data: 附加表单数据

        Returns:
            Dict: 上传结果
        """
        try:
            files = {field_name: open(file_path, "rb")}
            response = self._session.post(
                url, files=files, data=data, timeout=self._timeout
            )

            result = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
            }

            files[field_name].close()
            return result

        except Exception as e:
            logger.error(f"[HTTPClient] 上传失败: {e}")
            return {"success": False, "error": str(e)}

    def receive(self, timeout: float = None) -> Any:
        """HTTP客户端不支持此方法"""
        logger.warning(
            "[HTTPClient] 不支持receive方法，请使用get/post等HTTP方法"
        )
        return None

    def is_connected(self) -> bool:
        """HTTP是请求-响应模式，始终返回True"""
        return self._session is not None


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    http = HTTPClient()
    http.connect({"base_url": "https://httpbin.org", "timeout": 10})

    # GET请求
    print("\n=== GET请求 ===")
    response = http.get("/get", params={"key": "value"})
    print(f"状态码: {response.get('status_code')}")
    print(f"数据: {json.dumps(response.get('data', {}), indent=2)}")

    # POST请求
    print("\n=== POST请求 ===")
    response = http.post("/post", json={"name": "test", "value": 123})
    print(f"状态码: {response.get('status_code')}")

    # 带认证
    print("\n=== 带认证的请求 ===")
    http2 = HTTPClient()
    http2.connect({"base_url": "https://httpbin.org"})
    http2.set_auth("username", "password")

    response = http2.get("/basic-auth/username/password")
    print(f"状态码: {response.get('status_code')}")

    http.disconnect()
    http2.disconnect()

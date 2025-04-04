import json
import os
from typing import Any

import requests

from app.tool import BaseTool
from app.tool.base import ToolResult


class Onebound(BaseTool):
    name:str = "onebound"
    description:str = """
可以搜索淘宝

- 'taobao.item_search_img': 淘宝/天猫按图搜索淘宝商品（拍立淘）
- '1688.item_search_img': 阿里巴巴中国站按图搜索1688商品（拍立淘）


    """
    parameters:dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "taobao.item_search_img",
                    "1688.item_search_img",
                ],
                "description": "能够执行的操作",
            },
            "img_path": {
                "type": "string",
                "description": "用户输入的图片的本地链接",
            },
        },
        "required": ["action"],
        "dependencies": {
            "taobao.item_search_img": ["img_path"],
            "1688.item_search_img": ["img_path"],
        },
    }

    key:str=os.getenv('ONEBOUND_KEY')
    secret:str=os.getenv('ONEBOUND_SECRET')
    picui_token:str = os.getenv('PICUI_TOKEN')

    async def upload_image(self, img_path: str) -> str:
        """上传图片到PicUI图床并返回远程URL"""
        upload_url = "https://picui.cn/api/v1/upload"
        headers = {
            "Accept": "application/json",
        }

        if self.picui_token:
            headers["Authorization"] = f"Bearer {self.picui_token}"

        try:
            with open(img_path, 'rb') as img_file:
                files = {'file': img_file}
                response = requests.post(upload_url, headers=headers, files=files)
                if response.status_code == 200:
                    data = response.json()
                    if data['status']:
                        return data['data']['links']['url']
                raise Exception(f"上传失败: {response.text}")
        except Exception as e:
            raise Exception(f"图片上传出错: {str(e)}")

    async def execute(self, **kwargs) -> Any:
        action = kwargs.get("action")
        if action == "taobao.item_search_img":
            if "img_path" not in kwargs:
                return "img_path is required for 'taobao.item_search_img' action"
            img_path = kwargs.get("img_path")
            # 上传图片获取远程URL
            img_remote_path = await self.upload_image(img_path)

            url = ("https://api-gw.onebound.cn/taobao/item_search_img/?"
                   f"key={self.key}"
                   f"&secret={self.secret}"
                   f"&imgid={img_remote_path}"
                   "&img_type=")
            headers = {
                "Accept-Encoding": "gzip",
                "Connection": "close"
            }
            r = requests.get(url, headers=headers)
            json_obj = r.json()
            obj=[{
                "商品标题":item["title"],
                "价格":item["price"],
                "优惠价":item["promotion_price"],
                "商品链接":item["detail_url"],
                "图片链接":item["pic_url"],
                "是否天猫":item["is_tmall"],
                "地区":item["area"],
            } for item in json_obj["items"]["item"]]

            return ToolResult(output=json.dumps(obj, ensure_ascii=False))

        elif action == "1688.item_search_img":
            if "img_path" not in kwargs:
                return "img_path is required for '1688.item_search_img' action"
            img_path = kwargs.get("img_path")
            # 上传图片获取远程URL
            img_remote_path = await self.upload_image(img_path)
            url = ("https://api-gw.onebound.cn/1688/item_search_img/?"
                   f"key={self.key}"
                   f"&secret={self.secret}"
                   f"&imgid={img_remote_path}"
                   "&img_type=")
            headers = {
                "Accept-Encoding": "gzip",
                "Connection": "close"
            }
            r = requests.get(url, headers=headers)
            json_obj = r.json()
            print(json_obj)
            obj=[{
                "商品标题":item["title"],
                "价格":item["price"],
                "优惠价":item["promotion_price"],
                "商品链接":item["detail_url"],
                "图片链接":item["pic_url"],
                "销量":item["sales"],
                "回头率":item["turn_head"],
                "是否为一件代发":item["one_psale"],
                "是否为精选货源":item["is_jxhy"],
            } for item in json_obj["items"]["item"]]

            return ToolResult(output=json.dumps(obj, ensure_ascii=False))


"""处理HTML内容的工具，可以直接渲染到Web界面的结果框。"""

from typing import Any, Literal, Optional, get_args

from app.config import config
from app.exceptions import ToolError
from app.tool import BaseTool
from app.tool.base import ToolResult

Command = Literal[
    "render_html",
    "update_html",
    "append_html",
]

# 工具描述
_HTML_RENDERER_DESCRIPTION = """用于生成和渲染HTML内容的工具
* 可以生成HTML内容并直接渲染到Web界面的结果框中
* 命令:
  - render_html: 替换结果框中的全部内容
  - update_html: 更新结果框中的特定部分内容
  - append_html: 在结果框中追加内容
* HTML内容可以包含任何有效的HTML标签、CSS样式和JavaScript代码
* 生成的HTML将直接显示在用户界面的"结果"框中
"""

# 渲染容器
_HTML_RESULT = ""

class HtmlRenderer(BaseTool):
    """用于渲染HTML内容到Web界面结果框的工具。"""

    name: str = "html_renderer"
    description: str = _HTML_RENDERER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "要执行的命令。可选项: `render_html`, `update_html`, `append_html`.",
                "enum": ["render_html", "update_html", "append_html"],
                "type": "string",
            },
            "html_content": {
                "description": "要渲染的HTML内容",
                "type": "string",
            },
            "selector": {
                "description": "在使用`update_html`命令时，指定要更新的元素选择器",
                "type": "string",
            },
            "position": {
                "description": "在使用`append_html`命令时，指定添加的位置 (start 或 end)",
                "enum": ["start", "end"],
                "type": "string",
            },
        },
        "required": ["command", "html_content"],
    }

    # 存储HTML结果
    _html_result: str = ""

    @property
    def html_result(self) -> str:
        """获取当前HTML结果"""
        return self._html_result

    @html_result.setter
    def html_result(self, value: str) -> None:
        """设置HTML结果"""
        self._html_result = value

    async def execute(
        self,
        *,
        command: Command,
        html_content: str,
        selector: Optional[str] = None,
        position: Optional[str] = "end",
        **kwargs: Any,
    ) -> str:
        """执行HTML渲染命令"""

        # 执行相应的命令
        if command == "render_html":
            result = await self.render_html(html_content)
        elif command == "update_html":
            if selector is None:
                raise ToolError("使用update_html命令时，必须提供selector参数")
            result = await self.update_html(html_content, selector)
        elif command == "append_html":
            result = await self.append_html(html_content, position)
        else:
            # 通过类型检查应该捕获此错误，但为了安全我们包含它
            raise ToolError(
                f'无法识别的命令 {command}。{self.name}工具允许的命令有: {", ".join(get_args(Command))}'
            )

        return str(result)

    async def render_html(self, html_content: str) -> ToolResult:
        """将HTML内容渲染到结果框"""
        # 设置HTML结果
        self.html_result = html_content

        return ToolResult(
            output=f"HTML内容已成功渲染。结果将显示在Web界面的结果框中。\n预览HTML:\n{html_content[:200]}{'...' if len(html_content) > 200 else ''}"
        )

    async def update_html(self, html_content: str, selector: str) -> ToolResult:
        """更新结果框中指定元素的内容"""
        # 为了简单起见，在此实现中我们不实际操作DOM
        # 实际应用中，你可能需要在前端JavaScript中实现这个功能
        update_info = f"更新选择器'{selector}'的内容为新的HTML"

        # 在实际应用中，这里会更新特定元素
        # 简化起见，我们只更新整个内容
        self.html_result = html_content

        return ToolResult(
            output=f"HTML内容已更新。{update_info}。\n预览HTML:\n{html_content[:200]}{'...' if len(html_content) > 200 else ''}"
        )

    async def append_html(self, html_content: str, position: str = "end") -> ToolResult:
        """在结果框中追加HTML内容"""
        current_html = self.html_result

        if position == "start":
            self.html_result = html_content + current_html
            append_info = "内容已添加到HTML的开头"
        else:  # position == "end"
            self.html_result = current_html + html_content
            append_info = "内容已添加到HTML的末尾"

        return ToolResult(
            output=f"HTML内容已追加。{append_info}。\n预览HTML:\n{self.html_result[:200]}{'...' if len(self.html_result) > 200 else ''}"
        )

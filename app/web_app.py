import os
import base64
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
import asyncio

from app.agent.manus import Manus
from app.logger import logger

# 获取当前模块的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
           static_url_path='/static',
           static_folder=os.path.join(current_dir, 'static'),
           template_folder=os.path.join(current_dir, 'templates'))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传文件夹存在
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads'), exist_ok=True)

# 日志存储
log_messages = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def log_capture(message):
    """捕获日志消息"""
    log_messages.append(message)
    return message

@app.route('/')
def index():
    """渲染主页"""
    print("正在访问首页...")
    try:
        rendered = render_template('index.html')
        print("模板渲染成功")
        return rendered
    except Exception as e:
        print(f"模板渲染失败: {str(e)}")
        return f"<h1>出错了</h1><p>无法加载页面: {str(e)}</p>", 500

@app.route('/test')
def test():
    """测试路由"""
    print("正在访问测试页面...")
    try:
        return render_template('test.html')
    except Exception as e:
        print(f"测试页面渲染失败: {str(e)}")
        return f"<h1>出错了</h1><p>无法加载测试页面: {str(e)}</p>", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if file and allowed_file(file.filename):
        # 生成唯一文件名，防止覆盖
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{file.filename}"

        # 保存文件
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', filename)
        file.save(filepath)

        # 返回文件URL路径
        file_url = f'/static/uploads/{filename}'
        absolute_path = os.path.abspath(filepath)

        log_capture(f"图片上传成功: {filename}")

        return jsonify({
            'success': True,
            'file_url': file_url,
            'file_path': absolute_path
        })

    return jsonify({'error': '不允许的文件类型'}), 400

@app.route('/process', methods=['POST'])
def process_prompt():
    """处理用户提交的prompt"""
    global log_messages
    log_messages = []  # 清空日志

    data = request.json
    user_text = data.get('text', '')
    image_path = data.get('image_path', '')

    if not user_text:
        return jsonify({'error': '请输入文本描述'}), 400

    # 构建prompt
    prompt = f"用户输入：{user_text}\n"
    if image_path:
        prompt += f"图片地址：{image_path}\n"
    prompt += "请根据以上信息生成对应内容，使用html_renderer工具的render_html命令输出**精美的**HTML格式的结果，这些内容将被直接渲染到网页中的结果框里。在html上能渲染良好在约屏幕一半宽度上，包括合适大小的字体，图片。"

    log_capture(f"生成的prompt: {prompt}")
    print(f"生成的prompt: {prompt}")

    # 使用异步方式处理请求
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(process_async(prompt))
        log_capture("处理完成")
        return jsonify({
            'success': True,
            'result': result,
            'logs': log_messages
        })
    except Exception as e:
        error_msg = f"处理过程中出错: {str(e)}"
        log_capture(error_msg)
        return jsonify({
            'error': error_msg,
            'logs': log_messages
        }), 500
    finally:
        loop.close()

async def process_async(prompt):
    """异步处理prompt"""
    agent = Manus()
    log_capture("初始化Manus代理")

    try:
        log_capture("开始处理请求...")
        result = await agent.run(prompt)
        log_capture("请求处理完成")

        # 尝试获取HTML渲染器的结果
        html_result = ""
        for tool in agent.available_tools.tools:
            if tool.name == "html_renderer":
                html_result = tool.html_result
                break

        # 如果HTML渲染器有内容，则返回它，否则返回原始结果
        if html_result:
            log_capture("使用HTML渲染器的结果")
            return html_result
        else:
            log_capture("使用原始结果")
            return result
    except Exception as e:
        log_capture(f"处理过程中出错: {str(e)}")
        raise

def run_web_app():
    """启动Web应用"""
    print(f"当前工作目录: {os.getcwd()}")
    print(f"模板目录: {os.path.join(current_dir, 'templates')}")
    print(f"静态文件目录: {os.path.join(current_dir, 'static')}")
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_web_app()

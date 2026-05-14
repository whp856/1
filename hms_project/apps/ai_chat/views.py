import json
import urllib.request
import urllib.error
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

OLLAMA_BASE = 'http://localhost:11434'
OLLAMA_MODEL = 'deepseek-r1:7b'
OLLAMA_TIMEOUT = 120

SYSTEM_PROMPT = (
    '你是一位经验丰富的全科医生AI助手，名字叫"小医"。'
    '你的职责是为患者提供专业的健康咨询、用药指导和生活方式建议。\n\n'
    '## 行为准则\n'
    '1. 用通俗易懂的中文与患者交流，避免过于专业的医学术语\n'
    '2. 首先表达对患者状况的关心和理解\n'
    '3. 提供科学、循证的建议，不推荐未经证实的偏方\n'
    '4. 涉及药物时，说明用法、用量、注意事项和可能的副作用\n'
    '5. 紧急情况（胸痛、呼吸困难、严重外伤等）必须建议立即就医\n'
    '6. 始终提醒：AI建议仅供参考，不能替代医生面诊\n'
    '7. 回答简洁、有条理，使用序号分段\n'
    '8. 如问题超出医疗范围，礼貌说明并引导至相关科室\n\n'
    '## 格式要求\n'
    '- 使用 Markdown 格式化回答\n'
    '- 重要提醒用 **加粗** 标注\n'
    '- 如需列出步骤，使用有序列表\n'
)


@login_required
def chat_page(request: HttpRequest) -> HttpResponse:
    return render(request, 'ai_chat/chat.html')


@csrf_exempt
@login_required
def chat_api(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': '无效的JSON格式'}, status=400)

    messages = body.get('messages', [])
    stream = body.get('stream', True)

    if not messages:
        return JsonResponse({'error': '消息不能为空'}, status=400)

    payload = {
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages,
        'stream': stream,
        'options': {
            'temperature': 0.7,
            'top_p': 0.9,
            'num_predict': 2048,
        },
    }

    try:
        if stream:
            return _stream_response(payload)
        return _collect_response(payload)
    except Exception as e:
        logger.exception('AI对话请求失败')
        return JsonResponse({'error': f'服务异常: {str(e)}'}, status=500)


def _stream_response(payload: dict) -> StreamingHttpResponse:
    def generate():
        try:
            request_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f'{OLLAMA_BASE}/api/chat',
                data=request_data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                buffer = b''
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line.decode('utf-8'))
                            content = data.get('message', {}).get('content', '')
                            done = data.get('done', False)
                            if content:
                                yield f'data: {json.dumps({"content": content, "done": done})}\n\n'.encode('utf-8')
                            if done:
                                yield b'data: [DONE]\n\n'
                                return
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
        except urllib.error.URLError as e:
            error_msg = _resolve_ollama_error(e)
            logger.error(f'Ollama请求失败: {error_msg}')
            yield f'data: {json.dumps({"error": error_msg, "done": True})}\n\n'.encode('utf-8')
        except Exception as e:
            logger.exception('AI对话流式异常')
            yield f'data: {json.dumps({"error": str(e), "done": True})}\n\n'.encode('utf-8')

    return StreamingHttpResponse(
        generate(),
        content_type='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


def _collect_response(payload: dict) -> JsonResponse:
    try:
        nonstream = {**payload, 'stream': False}
        request_data = json.dumps(nonstream).encode('utf-8')
        req = urllib.request.Request(
            f'{OLLAMA_BASE}/api/chat',
            data=request_data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data.get('message', {}).get('content', '')
            return JsonResponse({'content': content, 'done': True})
    except urllib.error.URLError as e:
        logger.error(f'Ollama非流式请求失败: {_resolve_ollama_error(e)}')
        return JsonResponse({'error': _resolve_ollama_error(e)}, status=503)
    except json.JSONDecodeError as e:
        logger.error(f'Ollama返回数据解析失败: {e}')
        return JsonResponse({'error': 'AI服务返回数据异常'}, status=502)
    except Exception as e:
        logger.exception('AI对话非流式异常')
        return JsonResponse({'error': str(e)}, status=500)


def _resolve_ollama_error(e: urllib.error.URLError) -> str:
    reason = getattr(e, 'reason', None)
    if reason is None:
        return f'Ollama请求失败: {e}'
    reason_type = type(reason).__name__
    if reason_type in ('ConnectionRefusedError', 'ConnectionResetError',
                       'RemoteDisconnected', 'ConnectionAbortedError'):
        return '无法连接到Ollama服务，请确认已启动: ollama serve'
    if isinstance(reason, TimeoutError):
        return 'Ollama服务响应超时，请稍后重试'
    return f'网络错误: {reason}'


@csrf_exempt
@login_required
def health_check_api(request: HttpRequest) -> HttpResponse:
    try:
        req = urllib.request.Request(f'{OLLAMA_BASE}/api/tags', method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            available = any(OLLAMA_MODEL.split(':')[0] in m for m in models)
            return JsonResponse({
                'ollama_running': True,
                'model_available': available,
                'model': OLLAMA_MODEL,
                'installed_models': models,
            })
    except urllib.error.URLError as e:
        logger.warning(f'健康检测失败: {_resolve_ollama_error(e)}')
        return JsonResponse({'ollama_running': False, 'model_available': False})
    except Exception as e:
        logger.exception('健康检测异常')
        return JsonResponse({'ollama_running': False, 'model_available': False, 'error': str(e)})

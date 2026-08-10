import os
import random
from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

SYSTEM_PROMPT = """你是一个严格按照规则执行的材料组装器。根据用户输入的映射分数（0-100的整数），从预置的20个标准化信息点中，按比例组装视觉引导和语言引导两种形式的提示。"""

# ========== 学习材料展示页面 ==========
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>你的专属学习材料</title>
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; padding: 30px; max-width: 750px; margin: 0 auto; background: #f0f2f5; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 12px; text-align: center; }
        .material { background: white; padding: 15px 20px; margin: 10px 0; border-radius: 8px; border-left: 5px solid #667eea; }
        .material.visual { border-left-color: #4CAF50; }
        .material.verbal { border-left-color: #2196F3; }
        .code-box { background: #fff8e1; border: 2px dashed #f39c12; border-radius: 12px; padding: 18px; text-align: center; margin: 20px 0; }
        .code-box .code { font-size: 34px; font-weight: 900; color: #e74c3c; letter-spacing: 8px; background: white; padding: 6px 28px; border-radius: 8px; display: inline-block; }
        .btn-close { display: block; background: #27AE60; color: white; border: none; padding: 14px 44px; border-radius: 50px; font-size: 18px; font-weight: 600; cursor: pointer; margin: 10px auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 你的专属学习材料</h1>
        <p>映射分数：{{ score }} 分 | 视觉引导：{{ visual_count }} 条 | 语言引导：{{ verbal_count }} 条</p>
    </div>

    {% for item in materials %}
    <div class="material {{ item.type }}">
        <strong>{{ item.prefix }}</strong> {{ item.content }}
    </div>
    {% endfor %}

    <div class="code-box">
        <p>🔑 学习完成后，请返回问卷页面输入以下验证码：</p>
        <div class="code">{{ code }}</div>
    </div>

    <button class="btn-close" onclick="window.close();">✅ 已完成学习，关闭此页面</button>
</body>
</html>
"""

# ========== 量表页面 ==========
SURVEY_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>记忆偏好评估</title>
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 20px; }
        .container { background: white; max-width: 750px; margin: 0 auto; padding: 30px; border-radius: 16px; }
        h1 { text-align: center; }
        .instruction { background: #f7f9fc; padding: 14px 18px; border-radius: 10px; margin-bottom: 25px; border-left: 4px solid #667eea; }
        .question-item { padding: 16px 0; border-bottom: 1px solid #eee; }
        .question-item:last-child { border-bottom: none; }
        .options { display: flex; gap: 6px; flex-wrap: wrap; }
        .options label { padding: 6px 14px; background: #f5f6fa; border-radius: 8px; cursor: pointer; }
        .options input[type="radio"] { margin-right: 4px; }
        .btn-submit { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 12px; font-size: 18px; cursor: pointer; margin-top: 25px; }
        .error-msg { color: #e74c3c; background: #fde8e8; padding: 12px; border-radius: 8px; margin-top: 15px; display: none; }
        .error-msg.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 记忆偏好评估</h1>
        <div class="instruction">
            <p>1=完全不符合 2=比较不符合 3=有点不符合 4=一般/不确定 5=有点符合 6=比较符合 7=完全符合</p>
        </div>
        {% for q in questions %}
        <div class="question-item">
            <p><strong>{{ loop.index }}.</strong> {{ q }}</p>
            <div class="options">
                {% for i in range(1, 8) %}
                <label>
                    <input type="radio" name="q{{ loop.parent.index }}" value="{{ i }}" required>
                    {{ i }}
                </label>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
        <div class="error-msg" id="errorMsg">请完成所有题目的作答。</div>
        <button class="btn-submit" id="submitBtn">提交并生成学习材料</button>
    </div>
    <script>
        document.getElementById('submitBtn').addEventListener('click', function() {
            var answers = [];
            for (var i = 1; i <= 10; i++) {
                var radios = document.querySelectorAll('input[name="q' + i + '"]');
                var selected = false;
                for (var j = 0; j < radios.length; j++) {
                    if (radios[j].checked) {
                        answers.push(radios[j].value);
                        selected = true;
                        break;
                    }
                }
                if (!selected) {
                    document.getElementById('errorMsg').classList.add('show');
                    return;
                }
            }
            document.getElementById('errorMsg').classList.remove('show');
            this.disabled = true;
            this.textContent = '⏳ 生成中...';
            var url = '/generate_from_survey?q1=' + answers[0] + '&q2=' + answers[1] + '&q3=' + answers[2] + '&q4=' + answers[3] + '&q5=' + answers[4] + '&q6=' + answers[5] + '&q7=' + answers[6] + '&q8=' + answers[7] + '&q9=' + answers[8] + '&q10=' + answers[9];
            window.location.href = url;
        });
    </script>
</body>
</html>
"""

# ==================== 路由 ====================

@app.route('/survey')
def survey():
    questions = [
        "阅读小说时，我通常会在脑海中形成清晰详细的场景或房间的画面",
        "当我在脑海里回忆或想象某个东西时，它的大小、颜色和轮廓都跟我现实里见过的一样",
        "我可以轻松记住别人可能注意不到的大量视觉细节",
        "我闭上眼睛就能轻松地回想我经历过的场景画面",
        "我回忆人们的外貌和姿态会比回忆他们说过的话要详细得多",
        "如果想要了解一个物体或人物，我更愿意查看文字描述，而不是看图片",
        "当我回忆某个场景时，会更容易回想起对它的语言描述，而较难在脑海中浮现画面",
        "我有时会难以精确表达自己想要说的意思",
        "我觉得自己在遣词造句方面有较好的能力",
        "我常常能很好地复述和转述复杂的信息"
    ]
    return render_template_string(SURVEY_PAGE, questions=questions)

@app.route('/generate_from_survey')
def generate_from_survey():
    try:
        q1 = int(request.args.get('q1', 0))
        q2 = int(request.args.get('q2', 0))
        q3 = int(request.args.get('q3', 0))
        q4 = int(request.args.get('q4', 0))
        q5 = int(request.args.get('q5', 0))
        q6 = int(request.args.get('q6', 0))
        q7 = int(request.args.get('q7', 0))
        q8 = int(request.args.get('q8', 0))
        q9 = int(request.args.get('q9', 0))
        q10 = int(request.args.get('q10', 0))
    except ValueError:
        return "参数格式错误，请重新作答", 400

    o_mean = (q1 + q2 + q3 + q4 + q5) / 5
    v_mean = (q6 + q7 + (8 - q8) + q9 + q10) / 5
    mapScore = round(((v_mean - o_mean + 6) / 12) * 100, 2)

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': str(mapScore)}
                ],
                'temperature': 0.1,
                'max_tokens': 4000
            },
            timeout=30
        )
        result = response.json()
        ai_output = result['choices'][0]['message']['content']
    except Exception as e:
        return f"材料生成失败：{str(e)}", 500

    lines = ai_output.strip().split('\n')
    materials = []
    code = ''

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('验证码：'):
            code = line.replace('验证码：', '').strip()
            continue
        if line.startswith('【画面想象】'):
            content = line.replace('【画面想象】', '').strip()
            materials.append({'type': 'visual', 'prefix': '【画面想象】', 'content': content})
        elif line.startswith('【要点记忆】'):
            content = line.replace('【要点记忆】', '').strip()
            materials.append({'type': 'verbal', 'prefix': '【要点记忆】', 'content': content})

    if not code:
        code = str(random.randint(1000, 9999))

    visual_count = sum(1 for m in materials if m['type'] == 'visual')
    verbal_count = sum(1 for m in materials if m['type'] == 'verbal')

    return render_template_string(HTML_TEMPLATE, score=mapScore, materials=materials, code=code, visual_count=visual_count, verbal_count=verbal_count)

@app.route('/generate')
def generate():
    score = request.args.get('score', '50')
    try:
        score = int(score)
        if score < 0 or score > 100:
            return "请输入0-100之间的数字", 400
    except ValueError:
        return "请输入0-100之间的数字", 400

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': str(score)}
                ],
                'temperature': 0.1,
                'max_tokens': 4000
            },
            timeout=30
        )
        result = response.json()
        ai_output = result['choices'][0]['message']['content']
    except Exception as e:
        return f"材料生成失败：{str(e)}", 500

    lines = ai_output.strip().split('\n')
    materials = []
    code = ''

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('验证码：'):
            code = line.replace('验证码：', '').strip()
            continue
        if line.startswith('【画面想象】'):
            content = line.replace('【画面想象】', '').strip()
            materials.append({'type': 'visual', 'prefix': '【画面想象】', 'content': content})
        elif line.startswith('【要点记忆】'):
            content = line.replace('【要点记忆】', '').strip()
            materials.append({'type': 'verbal', 'prefix': '【要点记忆】', 'content': content})

    if not code:
        code = str(random.randint(1000, 9999))

    visual_count = sum(1 for m in materials if m['type'] == 'visual')
    verbal_count = sum(1 for m in materials if m['type'] == 'verbal')

    return render_template_string(HTML_TEMPLATE, score=score, materials=materials, code=code, visual_count=visual_count, verbal_count=verbal_count)

@app.route('/')
def index():
    return "实验材料生成服务正在运行。请使用 /generate?score=数字 或 /survey 访问。"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

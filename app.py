import os
import random
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# 系统提示词
SYSTEM_PROMPT = """你是一个严格按照规则执行的材料组装器，不是学习导师。你的任务是：根据用户输入的映射分数（0-100的整数），从预置的20个标准化信息点中，按比例组装视觉引导和语言引导两种形式的提示。

【输入说明】
用户会输入一个0到100之间的整数。数字越接近0，表示视觉加工倾向越强；数字越接近100，表示语言加工倾向越强；50表示视觉和语言均衡。

【组装规则】
1. 材料总数为20条提示，不能多也不能少。
2. 语言形式提示的数量 = 20 × (映射分数 / 100)，结果四舍五入取整。
3. 视觉形式提示的数量 = 20 - 语言形式提示的数量。
4. 如果映射分数为50，则各生成10条语言形式和10条视觉形式的提示。
5. 每个信息点只输出一种形式的提示——要么是视觉引导，要么是语言引导。绝对不能对同一个信息点同时输出两种形式。
6. 从20个信息点中随机选择指定数量的信息点作为语言形式提示，其余信息点作为视觉形式提示。

【输出格式】
这是强制要求，必须严格遵守，不允许有任何例外：

1. 必须输出正好20条学习提示，不能多也不能少。
2. 先汇报比例，格式如下：
   "根据你的记忆偏好（映射分数：X分），为你生成了以下专属学习材料：
   视觉引导提示：X条
   语言引导提示：X条"
3. 然后逐条输出提示。每条视觉形式提示以\"【画面想象】\"为前缀，每条语言形式提示以\"【要点记忆】\"为前缀。
4. 将两类提示混合随机排列，不要连续排列超过3条同类型提示。
5. 最后一行输出：\"验证码：XXXX\"（4位随机数字）

【预置信息点库】
以下是20个信息点，每个信息点提供视觉引导形式和语言引导形式两种版本：

1. 条状生物身体细长如锥，体表带有金属银白色光泽
视觉引导：请在脑海中构建一个画面：一条细长的生物从深色海水中穿行而过。它的身体从头至尾逐渐收窄，游动时身体微微摆动，体表反射出明亮的金属银白色光泽，在昏暗的水体中格外醒目。
语言引导：请记住这个要点：条状生物的外形与体色——身形细长呈锥形，体表带有金属银白色光泽。

2. 蜘蛛状深海生物躯干呈红棕色
视觉引导：请在脑海中构建一个画面：在幽暗的海底，一只形态似蜘蛛的生物伏在沉积物上，它的主体躯干呈现出浓郁的红棕色，在深色背景的衬托下显得格外突出，细长的步足向四周伸展开来。
语言引导：请记住这个要点：蜘蛛状生物的色彩特征——躯干主体为红棕色。

3. 视频开头出现了一个球状透明生物，身上有蓝灰色的发光体
视觉引导：请在脑海中构建一个画面：视频最开始，一个近乎全透明的球状生物悬浮在深暗的海水中。球体表面零星分布着蓝灰色的发光点，幽微的蓝灰色光芒在球体周围弥散开来，在深色水体中形成可见的光晕。
语言引导：请记住这个要点：视频最先出现的生物形态与特征——球状、近乎透明、体表带有蓝灰色发光体。

4. 会发光的人造物体出现了2次
视觉引导：请在脑海中构建一个画面：在幽暗深海的背景中，一个带有稳定光亮的金属质感人造物从画面边缘首次进入视野，不久后同样的物体再次出现，两次出现时其光亮在画面中都显得格外刺眼。
语言引导：请记住这个要点：会发光的人造物体的出现次数——视频中该类物体一共出现2次。

5. 蜘蛛状生物的腿部肢体有一对明显长于另外三对
视觉引导：请在脑海中构建一个画面：蜘蛛状生物静伏在海底。八条步足向四周完全展开铺平，其中位于前方或侧方的一对步足明显延伸得更远，其末端位置显著超出其余三对步足，在海底形成一个不对称的放射状轮廓。
语言引导：请记住这个要点：蜘蛛状生物步足的长度差异——存在一对步足明显长于其余三对。

6. 蜘蛛状生物的腿上都生长着触须
视觉引导：请在脑海中构建一个画面：贴近观察蜘蛛状生物伸展开的步足，每一根腿的表面都能看到细小的触须。它们从腿的表面向外微微伸出，在幽暗的海水中随水流轻轻摆动。
语言引导：请记住这个要点：蜘蛛状生物腿部的附属结构——所有步足均生长有细小触须。

7. 整段视频共出现了六种形态不同的海洋生物
视觉引导：请在脑海中构建一个画面：随着视频播放，一种又一种形态各异的海洋生物依次登场，有的圆润透明，有的细长如锥，有的张着伞状身体，逐一数过去，一共出现了六种外形样貌彼此不同的生物。
语言引导：请记住这个要点：视频中海洋生物的种类总数——总共出现 6种 形态各异的生物。

8. 蓝色光芒出现时，光呈现一明一暗的闪烁状态
视觉引导：请在脑海中构建一个画面：在漆黑深海的背景中，一道蓝色光芒亮起。光线并非稳定持续，而是以固定周期交替增强和减弱，在黑暗水体中形成规律性的亮度波动。
语言引导：请记住这个要点：蓝色光芒的发光动态——光线呈现一明一暗的闪烁状态。

9. 纺锤状生物头部张开时，边缘褶皱颜色发生变化
视觉引导：请在脑海中构建一个画面：纺锤状生物悬在水中。它的头部向外张开，原本收拢的边缘褶皱随之展开。在头部张开的瞬间，褶皱区域的色彩发生了可见的变化，深色背景使这一变化更易被注意到。
语言引导：请记住这个要点：纺锤状生物头部的动态特征——头部张开时，边缘褶皱的颜色会发生改变。

10. 半透明浮游生物体内有一个橘红色物体
视觉引导：请在脑海中构建一个画面：一只近乎透明的浮游生物在幽暗海水中浮动。透过其透明的躯体，可以清晰地看到内部正中央包裹着一个明亮的橘红色球状物，在透明组织的映衬下与周围形成鲜明对比。
语言引导：请记住这个要点：浮游生物的透明度与内部结构——身体半透明，体内可见一个橘红色物体。

11. 半透明浮游生物有两个侧足
视觉引导：请在脑海中构建一个画面：浮游生物的透明躯体两侧，各伸出一条短短的侧足，左右对称地向斜后方展开，在浮动过程中轻轻划动海水，两根侧足清晰可辨。
语言引导：请记住这个要点：半透明浮游生物的肢体数量——身体两侧共有 2根侧足。

12. 球状生物外部有白色丝状结构
视觉引导：请在脑海中构建一个画面：球状生物悬停在水中，许多细长稀疏的白色丝状物从球体的外表面向外伸展，随水流发生可见的飘动。
语言引导：请记住这个要点：球状生物的外部结构特征——球体表面生有白色丝状结构。

13. 水母伞缘边缘有多条短小触手
视觉引导：请在脑海中构建一个画面：水母的圆形伞盖边缘，排列着一圈短小的触手。触手长度均匀，从伞缘向下垂落，在水中随水流的运动发生可见的摆动。
语言引导：请记住这个要点：水母伞缘的附属结构——伞盖边缘生长有多条短小触手。

14. 伞形水母整体呈橘黄褐色，伞盖内侧布满细密放射状纹路
视觉引导：请在脑海中构建一个画面：一只伞形水母悬浮在深海中。整体色调为均匀的橘黄褐色。伞盖内侧分布着大量细密的纹路，从中心向边缘呈辐射状延伸，布满整个伞盖内表面。
语言引导：请记住这个要点：伞形水母的体色与内部纹理——整体橘黄褐色；伞盖内侧分布大量细密放射状纹路。

15. 水母伞体几乎完全透明，内部器官清晰可见
视觉引导：请在脑海中构建一个画面：水母的伞体通透度极高。透过伞体可以清晰地辨认出内部各类器官的轮廓和相对位置，伞体本身几乎不遮挡视线。
语言引导：请记住这个要点：水母伞体的透明度特征——伞体接近全透明，内部器官清晰可见。

16. 橙红色筒状生物上部边缘呈波浪褶皱状
视觉引导：请在脑海中构建一个画面：一只橙红色的筒状生物竖立在海水中，它上端边缘并非平直，而是呈现出波浪状起伏的褶皱，边缘轮廓高低错落分布。
语言引导：请记住这个要点：筒状生物的外形特征——整体橙红色，上部边缘呈波浪褶皱状。

17. 条状生物以S型姿势迅速离开画面
视觉引导：请在脑海中构建一个画面：条状生物的身体弯折成S形曲线，通过左右交替的扭动快速向前移动，随后移出画面范围。
语言引导：请记住这个要点：条状生物的运动方式——身体呈S形弯曲，快速游动并离开画面。

18. 条状生物头部尖锐，前端有尖细
视觉引导：请在脑海中构建一个画面：条状生物的头部呈锥形收窄。最前端延伸出一段细长的尖细结构，在头部前方清晰可见。
语言引导：请记住这个要点：条状生物的头部形态——头部尖锐，前端有尖细的突出物。

19. 视频中出现的蜘蛛状生物向上推动了3次
视觉引导：请在脑海中构建一个画面：蜘蛛状生物伏在海底。身体向上方推动一次，短暂停顿后再推动一次，随后进行第三次推动，之后恢复静止。三次向上推动的动作序列清晰可辨。
语言引导：请记住这个要点：蜘蛛状生物的动作次数——向上推动的动作一共发生3次。

20. 蜘蛛状生物有八条步足
视觉引导：请在脑海中构建一个画面：蜘蛛状生物悬浮在海中，八条细长的步足从躯干周围向四面八方伸展开来，在空间上形成均匀的放射状分布。
语言引导：请记住这个要点：蜘蛛状生物的步足数量——该生物共有 8条步足。

【绝对禁令】
- 每个信息点只能出现一次，只能以视觉形式或语言形式中的一种呈现，绝对不能两种形式都输出。
- 禁止生成信息点库之外的任何知识内容。
- 禁止添加评价性语句（如\"这部分很重要\"）。
- 禁止提问。
- 禁止修改信息点的核心事实。
- 如果用户输入的不是0-100的数字，只输出\"请输入0-100之间的数字\"。"""

# HTML页面模板
# ========== 量表页面模板 ==========
SURVEY_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>记忆偏好评估</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #f0f2f5;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }
        .container {
            background: white;
            max-width: 750px;
            width: 100%;
            padding: 30px 25px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-top: 20px;
        }
        h1 { text-align: center; color: #2c3e50; font-size: 24px; margin-bottom: 6px; }
        .subtitle { text-align: center; color: #95a5a6; font-size: 14px; margin-bottom: 20px; }
        .instruction {
            background: #f7f9fc;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 25px;
            font-size: 14px;
            color: #555;
            line-height: 1.8;
            border-left: 4px solid #667eea;
        }
        .instruction strong { color: #2c3e50; }
        .question-item { padding: 16px 0; border-bottom: 1px solid #ecf0f1; }
        .question-item:last-child { border-bottom: none; }
        .question-text { font-size: 15px; color: #2c3e50; margin-bottom: 10px; line-height: 1.6; }
        .question-text .qnum { color: #667eea; font-weight: 700; }
        .options { display: flex; gap: 6px; flex-wrap: wrap; padding-left: 4px; }
        .options label {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 3px;
            font-size: 14px;
            padding: 6px 14px;
            border-radius: 8px;
            background: #f5f6fa;
            cursor: pointer;
            transition: 0.2s;
            border: 2px solid transparent;
            user-select: none;
        }
        .options label:hover { background: #e8ecf1; }
        .options input[type="radio"] { accent-color: #667eea; width: 16px; height: 16px; margin: 0; }
        .options label:has(input:checked) { background: #eef1ff; border-color: #667eea; }
        .btn-submit {
            display: block;
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 25px;
            transition: 0.3s;
        }
        .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(102,126,234,0.4); }
        .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .error-msg { color: #e74c3c; background: #fde8e8; padding: 12px 18px; border-radius: 8px; margin-top: 15px; font-size: 14px; display: none; }
        .error-msg.show { display: block; }
        .loading-text { text-align: center; color: #667eea; font-size: 16px; margin-top: 20px; display: none; }
        .loading-text.show { display: block; }
        @media (max-width: 500px) {
            .container { padding: 20px 15px; }
            .options label { padding: 5px 10px; font-size: 13px; }
            .question-text { font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 记忆偏好评估</h1>
        <p class="subtitle">请根据您的实际情况作答</p>
        <div class="instruction">
            <p><strong>评分说明：</strong></p>
            <p>1 = 完全不符合 &nbsp;&nbsp; 2 = 比较不符合 &nbsp;&nbsp; 3 = 有点不符合 &nbsp;&nbsp; 4 = 一般/不确定</p>
            <p>5 = 有点符合 &nbsp;&nbsp; 6 = 比较符合 &nbsp;&nbsp; 7 = 完全符合</p>
            <p style="margin-top:6px;color:#888;font-size:13px;">请逐题作答，答案没有对错之分。</p>
        </div>
        <div id="questions">
            {% for q in questions %}
            <div class="question-item">
                <div class="question-text">
                    <span class="qnum">{{ loop.index }}.</span> {{ q }}
                </div>
                <div class="options">
                    {% for i in range(1, 8) %}
                    <label>
                        <input type="radio" name="q{{ loop.parent.loop.index }}" value="{{ i }}" required>
                        {{ i }}
                    </label>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="error-msg" id="errorMsg">请完成所有题目的作答。</div>
        <div class="loading-text" id="loadingText">⏳ 正在生成您的专属学习材料，请稍候...</div>
        <button class="btn-submit" id="submitBtn">提交并生成学习材料</button>
    </div>
    <script>
        document.getElementById('submitBtn').addEventListener('click', function() {
            var btn = this;
            var errorMsg = document.getElementById('errorMsg');
            var loadingText = document.getElementById('loadingText');
            var answers = [];
            var allAnswered = true;
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
                    allAnswered = false;
                    break;
                }
            }
            if (!allAnswered) {
                errorMsg.classList.add('show');
                return;
            }
            errorMsg.classList.remove('show');
            btn.disabled = true;
            btn.textContent = '⏳ 生成中...';
            loadingText.classList.add('show');
            var url = '/generate_from_survey?q1=' + answers[0] +
                      '&q2=' + answers[1] +
                      '&q3=' + answers[2] +
                      '&q4=' + answers[3] +
                      '&q5=' + answers[4] +
                      '&q6=' + answers[5] +
                      '&q7=' + answers[6] +
                      '&q8=' + answers[7] +
                      '&q9=' + answers[8] +
                      '&q10=' + answers[9];
            window.location.href = url;
        });
    </script>
</body>
</html>
"""


# ============================================================
# 路由1：显示量表页面
# ============================================================
@app.route('/survey')
def survey():
    """显示记忆偏好量表页面"""
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


# ============================================================
# 路由2：从量表提交生成学习材料
# ============================================================
@app.route('/generate_from_survey')
def generate_from_survey():
    """从量表提交生成学习材料"""
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
    mapScore = ((v_mean - o_mean + 6) / 12) * 100
    mapScore = round(mapScore, 2)

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
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
        return f"材料生成失败，请稍后重试。错误信息：{str(e)}", 500

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
            materials.append({
                'type': 'visual',
                'prefix': '【画面想象】',
                'content': content
            })
        elif line.startswith('【要点记忆】'):
            content = line.replace('【要点记忆】', '').strip()
            materials.append({
                'type': 'verbal',
                'prefix': '【要点记忆】',
                'content': content
            })
        elif line.startswith('根据你的记忆偏好'):
            continue
        elif '视觉引导提示' in line or '语言引导提示' in line:
            continue

    visual_count = sum(1 for m in materials if m['type'] == 'visual')
    verbal_count = sum(1 for m in materials if m['type'] == 'verbal')

    if not code:
        code = str(random.randint(1000, 9999))

    return render_template_string(
        HTML_TEMPLATE,
        score=mapScore,
        materials=materials,
        code=code,
        visual_count=visual_count,
        verbal_count=verbal_count
    )


# ============================================================
# 原有的路由（保留，作为备用）
# ============================================================
@app.route('/generate')
def generate():
    """直接从分数生成学习材料（备用入口）"""
    score_str = request.args.get('score', '50')
    try:
        score = int(score_str)
        if score < 0 or score > 100:
            return "请输入0-100之间的数字", 400
    except ValueError:
        return "请输入0-100之间的数字", 400

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
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
        return f"材料生成失败，请稍后重试。错误信息：{str(e)}", 500

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
            materials.append({
                'type': 'visual',
                'prefix': '【画面想象】',
                'content': content
            })
        elif line.startswith('【要点记忆】'):
            content = line.replace('【要点记忆】', '').strip()
            materials.append({
                'type': 'verbal',
                'prefix': '【要点记忆】',
                'content': content
            })
        elif line.startswith('根据你的记忆偏好'):
            continue
        elif '视觉引导提示' in line or '语言引导提示' in line:
            continue

    visual_count = sum(1 for m in materials if m['type'] == 'visual')
    verbal_count = sum(1 for m in materials if m['type'] == 'verbal')

    if not code:
        code = str(random.randint(1000, 9999))

    return render_template_string(
        HTML_TEMPLATE,
        score=score,
        materials=materials,
        code=code,
        visual_count=visual_count,
        verbal_count=verbal_count
    )


@app.route('/')
def index():
    return "实验材料生成服务正在运行。请使用 /generate?score=数字 来获取学习材料。"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

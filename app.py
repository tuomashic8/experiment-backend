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
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>你的专属学习材料</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            padding: 30px 20px;
            max-width: 750px;
            margin: 0 auto;
            background-color: #f0f2f5;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 22px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.35);
        }
        .header h1 {
            font-size: 22px;
            font-weight: 700;
        }
        .header .sub {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 6px;
        }
        .header .stats {
            font-size: 13px;
            opacity: 0.85;
            margin-top: 4px;
            background: rgba(255,255,255,0.15);
            display: inline-block;
            padding: 4px 16px;
            border-radius: 20px;
        }
        .timer-container {
            position: sticky;
            top: 10px;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            margin-bottom: 16px;
        }
        .timer-box {
            background: linear-gradient(135deg, #4A90D9, #357ABD);
            color: white;
            padding: 10px 26px;
            border-radius: 50px;
            font-size: 22px;
            font-weight: 700;
            box-shadow: 0 4px 15px rgba(74, 144, 217, 0.4);
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        .timer-box.time-up {
            background: linear-gradient(135deg, #27AE60, #1E8449);
            box-shadow: 0 4px 15px rgba(39, 174, 96, 0.4);
        }
        .timer-box .icon { font-size: 20px; }
        .material {
            background: white;
            padding: 16px 20px;
            margin: 12px 0;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            line-height: 1.9;
            font-size: 15px;
            color: #2c3e50;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.15s;
        }
        .material:hover { transform: translateX(4px); }
        .material.visual { border-left-color: #4CAF50; }
        .material.verbal { border-left-color: #2196F3; }
        .material .prefix {
            font-weight: 700;
            display: inline-block;
            margin-right: 6px;
        }
        .material.visual .prefix { color: #4CAF50; }
        .material.verbal .prefix { color: #2196F3; }
        .code-box {
            background: #fff8e1;
            border: 2px dashed #f39c12;
            border-radius: 12px;
            padding: 18px 20px;
            margin: 20px 0 16px 0;
            text-align: center;
        }
        .code-box p {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 6px;
        }
        .code-box .code {
            font-size: 34px;
            font-weight: 900;
            color: #e74c3c;
            letter-spacing: 8px;
            background: white;
            padding: 6px 28px;
            border-radius: 8px;
            display: inline-block;
            border: 1px solid #f39c12;
        }
        .btn-close {
            display: none;
            background: linear-gradient(135deg, #27AE60, #1E8449);
            color: white;
            border: none;
            padding: 14px 44px;
            border-radius: 50px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px auto 6px auto;
            box-shadow: 0 4px 15px rgba(39, 174, 96, 0.35);
            transition: all 0.3s ease;
            width: fit-content;
        }
        .btn-close.show { display: block; }
        .btn-close:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(39, 174, 96, 0.5);
        }
        .btn-close:active { transform: translateY(0); }
        .footer-tip {
            text-align: center;
            font-size: 13px;
            color: #95a5a6;
            margin-top: 20px;
            padding-top: 14px;
            border-top: 1px solid #ecf0f1;
        }
        .footer-tip .highlight { color: #e74c3c; font-weight: 600; }
        @media (max-width: 500px) {
            .header h1 { font-size: 18px; }
            .timer-box { font-size: 18px; padding: 8px 18px; }
            .code-box .code { font-size: 26px; letter-spacing: 4px; }
            .material { font-size: 14px; padding: 14px 16px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 你的专属学习材料</h1>
        <div class="sub">映射分数：{{ score }} 分</div>
        <div class="stats">视觉引导：{{ visual_count }} 条 &nbsp;·&nbsp; 语言引导：{{ verbal_count }} 条</div>
    </div>
    <div class="timer-container">
        <div class="timer-box" id="timerBox">
            <span class="icon">⏱️</span>
            <span id="timerDisplay">03:00</span>
        </div>
    </div>
    <div id="materialsContainer">
        {% for item in materials %}
        <div class="material {{ item.type }}">
            <span class="prefix">{{ item.prefix }}</span>{{ item.content }}
        </div>
        {% endfor %}
    </div>
    <div class="code-box">
        <p>🔑 学习完成后，请返回问卷页面输入以下验证码：</p>
        <div class="code">{{ code }}</div>
    </div>
    <button class="btn-close" id="closeBtn" onclick="closePage()">
        ✅ 已完成学习，关闭此页面
    </button>
    <div class="footer-tip">
        <span class="highlight">⏳ 请耐心等待倒计时结束</span> · 学习时间：3分钟
    </div>
    <script>
        (function() {
            const TOTAL_SECONDS = 180;
            const timerDisplay = document.getElementById('timerDisplay');
            const timerBox = document.getElementById('timerBox');
            const closeBtn = document.getElementById('closeBtn');
            const materialsContainer = document.getElementById('materialsContainer');

            let remaining = TOTAL_SECONDS;
            let timerId = null;
            let isTimeUp = false;

            function formatTime(seconds) {
                const m = String(Math.floor(seconds / 60)).padStart(2, '0');
                const s = String(seconds % 60).padStart(2, '0');
                return m + ':' + s;
            }

            function updateDisplay() {
                timerDisplay.textContent = formatTime(remaining);
            }

            function onTimeUp() {
                if (isTimeUp) return;
                isTimeUp = true;

                if (timerId) {
                    clearInterval(timerId);
                    timerId = null;
                }

                timerBox.classList.add('time-up');
                timerDisplay.textContent = '✅ 时间到！';

                // 隐藏学习材料
                if (materialsContainer) {
                    materialsContainer.style.display = 'none';
                }

                closeBtn.classList.add('show');

                const footer = document.querySelector('.footer-tip');
                if (footer) {
                    footer.innerHTML = '✅ 学习时间结束，材料已隐藏。请关闭此页面，返回问卷继续作答。';
                }
            }

            function startTimer() {
                if (remaining <= 0) {
                    onTimeUp();
                    return;
                }
                updateDisplay();

                timerId = setInterval(function() {
                    remaining -= 1;
                    if (remaining <= 0) {
                        remaining = 0;
                        updateDisplay();
                        onTimeUp();
                    } else {
                        updateDisplay();
                    }
                }, 1000);
            }

            window.closePage = function() {
                window.close();
                setTimeout(function() {
                    document.body.innerHTML = `
                        <div style="text-align:center;padding:80px 20px;font-family:sans-serif;">
                            <h2 style="color:#27AE60;">✅ 学习已完成</h2>
                            <p style="color:#555;margin-top:15px;">请手动关闭此浏览器标签页，返回问卷继续作答。</p>
                            <p style="color:#999;font-size:14px;margin-top:10px;">验证码：<strong style="color:#e74c3c;">{{ code }}</strong></p>
                        </div>
                    `;
                }, 300);
            };

            if (remaining <= 0) {
                onTimeUp();
            } else {
                startTimer();
            }
        })();
    </script>
</body>
</html>
"""


@app.route('/generate')
def generate():
    """生成个性化学习材料"""
    score_str = request.args.get('score', '50')

    try:
        score = int(score_str)
        if score < 0 or score > 100:
            return "请输入0-100之间的数字", 400
    except ValueError:
        return "请输入0-100之间的数字", 400

    # 调用 DeepSeek API
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

    # 解析AI输出，分离材料内容和验证码
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
            # 这是汇报比例的说明行，跳过
            continue
        elif '视觉引导提示' in line or '语言引导提示' in line:
            # 这也是汇报比例的行，跳过
            continue

    # 统计数量
    visual_count = sum(1 for m in materials if m['type'] == 'visual')
    verbal_count = sum(1 for m in materials if m['type'] == 'verbal')

    # 如果AI没有生成验证码，手动生成一个
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

from typing import List
from CupGraspClass import zcup
from SerialRoboArm import SerialArmControllerClass
import time
import numpy as np
from openai import OpenAI
from typing import List
import sys
import requests
import ast
import re
import json
import os
# --- 强制禁用代理环境变量，尤其对于本地连接 ---
# 移除常见的代理环境变量
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None) # 确保所有类型的代理都被清除

# 明确告诉 requests 库，对于这些地址（本地回环），不要使用代理
os.environ['NO_PROXY'] = '127.0.0.1,localhost'
# 改正
RED = 4
BLUE = 2
YELLOW = 3
OTHER = 1
# client = OpenAI(api_key="sk-7f60db8ef22f4ca2a16af1e528186c3f", base_url="https://api.deepseek.com")
# ===============================
# 本地 Ollama 控制机械臂
# ===============================
# OLLAMA_URL = "http://127.0.0.1:50011/api/chat"
# OLLAMA_MODEL = "tinyllama"
DEEPSEEK_API_KEY = "sk-7f60db8ef22f4ca2a16af1e528186c3f" # 您的 DeepSeek API Key
DEEPSEEK_BASE_URL = "https://api.deepseek.com" # DeepSeek API 的 Base URL
DEEPSEEK_MODEL = "deepseek-chat" # 或者 "deepseek-coder", 具体取决于您想用的模型
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# --- AI决策的个性化提示语 ---
TASK_ACTION_MESSAGES = {
    "start_find_red_cup": "🤖 我决定：启动视觉系统，开始寻找红色杯子。",
    "grab_red_cup": "🤖 我决定：红色杯子已定位，准备执行抓取动作。",
    "start_scan_for_other_cup": "🤖 我决定：红色杯子已抓取，开始扫视环境，寻找另一个接收水的杯子。",
    "pour_into_other_cup": "🤖 我决定：目标杯子已找到，开始执行倒水操作。",
    "return_red_cup": "🤖 我决定：倒水完成，将红色杯子放回初始位置。",
    "task_complete": "✅ 任务完成：所有操作均已顺利执行！",
    "abort_task": "❌ 任务中止：遇到问题或指令无法执行。",
}

SCAN_STRATEGY_MESSAGES = {
    "move_y": "🤖 我决定：沿 Y 轴移动，增量为 {delta_y}。", # 这是一个格式字符串，需要传入 delta_y
    "reset_y_to_start": "🤖 我决定：将 Y 轴重置到初始扫视位置。",
    "adjust_step": "🤖 我决定：调整扫视步长为 {new_step}，进行更精细的探索。", # 需要传入 new_step
    "found": "✅ 目标已找到！扫视任务完成。",
    "fail": "❌ 扫视失败：在所有尝试后仍无法找到目标。",
}

ai_task_coordinator_prompt = """
你是一个任务协调者AI，负责根据当前任务状态和人类操作员的指令，规划机械臂的下一步高层级动作。
你的目标是每次只提供一个最直接、最合适的下一步动作。
严格地，你必须只输出一个JSON对象，这个JSON对象表示一个动作。不要包含任何解释、说明、对话、Markdown 代码块之外的文本、或者未来的步骤规划。**
你每次只给出立即执行的下一步。不要猜测后续步骤。
如果操作员的指令不明确，或者当前状态无法执行任何有效动作，则返回中止任务的动作。
有效的你可以输出的动作类型及其JSON格式示例：
1. 开始寻找红色杯子: `{"action": "start_find_red_cup", "reason": "开始寻找操作员指定的红色杯子。"}`
2. 抓取红色杯子: `{"action": "grab_red_cup", "reason": "红色杯子已定位，准备抓取。"}`
3. 开始扫描寻找另一个杯子: `{"action": "start_scan_for_other_cup", "reason": "红色杯子已抓取，准备寻找另一个杯子进行倒水。"}`
4. 将水倒入另一个杯子: `{"action": "pour_into_other_cup", "reason": "两个杯子都已定位，执行倒水操作。"}`
5. 放回红色杯子: `{"action": "return_red_cup", "reason": "倒水完成，将红色杯子放回初始位置。"}`
6. 任务完成: `{"action": "task_complete", "reason": "所有指令已完成，任务成功。"}`
7. 中止任务: `{"action": "abort_task", "reason": "无法执行或指令无效。"}`

你的决策应基于我提供的当前任务状态和操作员的最新指令。
你必须严格按照 JSON 格式输出，并且只输出 JSON 对象，不要包含任何其他文字。

指令理解：
1.  {"action": "start_find_red_cup"}：开始寻找红色杯子的阶段。通常在任务开始时由操作员触发。
2.  {"action": "grab_red_cup"}：在红色杯子已找到并定位后，执行抓取红色杯子的动作。
3.  {"action": "start_scan_for_other_cup"}：在红色杯子已抓取后，开始扫视并寻找接收水的杯子（OTHER）。
4.  {"action": "pour_into_other_cup"}：在接收水的杯子（OTHER）已找到并定位后，将机械臂中已抓取的红色杯子中的水倒入接收杯。
5.  {"action": "return_red_cup"}：在倒水操作完成后，将红色杯子放回原位。
6.  {"action": "task_complete"}：所有任务阶段已成功完成。
7.  {"action": "abort_task", "reason": "<原因描述>"}：某个阶段失败，无法继续，需要中止整个任务。

重要提示：
*   我将为你提供一个 `current_task_state` 来描述整个流程的当前进展。
*   你还会收到一个 `human_instruction`，这是操作员直接输入的自然语言指令。
*   你需要综合这两部分信息，给出最合适的 `action`。
"""


def get_task_action_from_ai(current_task_state: str, human_instruction: str) -> dict:
    """
    询问 AI 下一步的高层级任务动作，接收人工指令。
    Args:
        current_task_state: 描述当前任务总体状态的字符串。
        human_instruction: 人类操作员输入的自然语言指令。
    Returns:
        AI 返回的 JSON 格式动作指令，例如 {"action": "proceed_to_pour"}。
    """
    # 构造用户消息，包含当前上下文和人工指令
    user_message = (
        f"当前任务总体状态是：'{current_task_state}'。\n"
        f"人类操作员的指令是：'{human_instruction}'。\n"
        f"请只给出立即执行的下一步动作的JSON对象。"
    )

    messages_payload = [
        {"role": "system", "content": ai_task_coordinator_prompt},
        # --- Few-shot 示例 (强烈建议保留或增加，以确保格式) ---
        {"role": "user", "content": "当前任务总体状态是：'任务开始，等待操作员指令'。人类操作员的指令是：'开始找红杯'。"},
        {"role": "assistant",
         "content": '{"action": "start_find_red_cup", "reason": "根据操作员指令，开始寻找红色杯子。"}'},

        {"role": "user", "content": user_message},  # 您的实际请求
    ]
    content = ""  # 将这一行添加到 try 块的外面，函数的顶部
    try:
        # --- 使用 OpenAI 客户端进行 API 调用 ---
        # client.chat.completions.create 方法会自动处理 URL、Headers 和 JSON 序列化
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages_payload,
            temperature=0.0,  # 与之前 payload 中的 options["temperature"] 对应
            stream=False,  # 与之前 payload 中的 stream 对应
            timeout=60  # OpenAI 客户端也支持 timeout 参数
        )

        # --- 从响应中提取内容 ---
        # OpenAI 兼容 API 的标准响应结构
        content = response.choices[0].message.content

        # --- 解析 JSON ---
        # 但为了最初的鲁棒性，可以暂时保留，如果 DeepSeek 总是返回纯 JSON，则可以移除。
        json_string = content.strip()
        # 如果模型偶尔还是会用Markdown代码块包裹，可以使用以下逻辑：
        # json_match = re.search(r"```json\n([\s\S]*?)\n```", content)
        # if json_match:
        #     json_string = json_match.group(1).strip()
        #     print(f"✅ 成功从模型输出中提取 JSON (通过Markdown): {json_string}")
        # else:
        #     json_string = content.strip()
        #     print(f"✅ 成功从模型输出中获取 JSON (直接): {json_string}")

        task_action = json.loads(json_string)

        # --- 动作有效性检查 (保持不变) ---
        valid_actions = [
            "start_find_red_cup", "grab_red_cup", "start_scan_for_other_cup",
            "pour_into_other_cup", "return_red_cup", "task_complete", "abort_task"
        ]
        if task_action.get("action") not in valid_actions:
            print(f"⚠️ AI 任务协调者返回了不允许的动作 '{task_action.get('action')}'。强制中止任务。")
            return {"action": "abort_task", "reason": "Invalid AI task action"}
        # --- 新增的打印 AI 决策的逻辑 ---
        action_message = TASK_ACTION_MESSAGES.get(task_action["action"],
                                                      f"🤖 我决定：执行未知动作 '{task_action['action']}'。")
        print(action_message)
        # --- 打印结束 ---

        return task_action
    except Exception as e:
        print(f"⚠️ 调用 Ollama 任务协调者出错或解析 AI 输出失败: {e}. AI返回原始文本: {content}. 强制中止任务。")
        return {"action": "abort_task", "reason": f"AI communication error: {e}"}


# 新的 AI 系统提示词，用于引导 AI 输出扫视策略的 JSON
ai_system_prompt_for_scan = """
你现在是一个机械臂的智能 Y 轴扫视策略规划器，你的核心任务是系统性地、高效地沿 Y 轴（即机械臂底盘转动方向）查找一个目标。
机械臂的 X 轴和 Z 轴将保持固定不变，你绝对不能尝试改变 X 轴或 Z 轴的坐标。
严格地，你必须只输出一个JSON对象，不要包含任何其他文字，不要解释，不要总结，不要包含Markdown代码块（```json或```），不要重复我的输入。
你每次只给出一个立即执行的动作策略。


你的决策应基于以下策略和原则：
1.  从粗到精的探索：
    *   在最初的尝试阶段，优先使用较大的步长 (`delta_y`) 快速覆盖 Y 轴的广阔区域。
    *   如果大步长尝试多次后仍未发现目标，应建议减小扫视步长 (`adjust_step`) 进行更精细的搜索。
2.  全面覆盖 Y 轴并系统性往返：
    *   系统性地探索 Y 轴的整个范围 (大约从 -180 到 180)。
    *   通常从初始 Y 轴位置（例如 -14）开始向一个方向扫描。
    *   当扫描到 Y 轴某一边界附近（例如 Y > 140 或 Y < -140），且该方向已探索完毕但未找到目标时，应考虑返回初始 Y 轴位置，然后向另一个方向扫描。即如果之前增量为正，之后增量就为负，反之一样。
3.  响应反馈：
    *   如果相机成功检测到目标，你应该立即判断为 `{"action": "found"}`。
    *   如果相机未能检测到目标，你需要调整策略继续探索。

你可以给出以下指令，每次只能返回一个 JSON 对象，不要包含任何其他文字：
1.  {"action": "move_y", "delta_y": <数值>}：在当前 Y 轴位置上，增量移动 delta_y (例如：80, -80, 30, -30)。
    *   Y 轴的有效范围是 [-180, 180]。
    *   请确保 `delta_y` 是当前扫视步长 `current_step` 的整数倍或其合理倍数。
2.  {"action": "reset_y_to_start"}：将 Y 轴移动到初始扫视点（-14）。这个操作用于当一个方向的扫描完成后，需要回到起点开始反向扫描时。此操作仅用于机械臂重新定位，不预期在此位置找到目标，因此无需立即进行相机检测。
3.  {"action": "adjust_step", "new_step": <数值>}：建议用户代码减小扫视步长。例如：{"action": "adjust_step", "new_step": 30}。
    *   `new_step` 必须是正整数，且应小于当前的 `current_step`，但**不能小于 10** (例如：80 -> 40 -> 20 -> 10)。
4.  {"action": "found"}：目标已确认找到，停止所有扫视策略规划。
5.  {"action": "fail"}：在用尽了所有合理 Y 轴扫视策略（包括大步长和小步长，以及来回覆盖）后，仍无法找到目标，建议停止。

当前固定参数：X 轴固定在 183，Z 轴固定在 242。
你的目标是最大限度地提高目标发现的效率和成功率。
初始 Y 轴位置通常是 -14。
---
以下是一些扫视策略的示例：

# 示例1: 初始探索，从起点向 Y 轴正方向移动
用户: 当前机械臂位置 [x:183, y:-14, z:242]。 上次相机检测是否成功：False。 已尝试 0 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "move_y", "delta_y": 80}

# 示例2: 继续向 Y 轴正方向探索
用户: 当前机械臂位置 [x:183, y:66, z:242]。 上次相机检测是否成功：False。 已尝试 1 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "move_y", "delta_y": 80}

# 示例3: Y 轴已达正向探索边界 (例如 146)，此方向探索完毕，需要返回起点。此处是定位，无需检测。
用户: 当前机械臂位置 [x:183, y:146, z:242]。 上次相机检测是否成功：False。 已尝试 2 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "reset_y_to_start"}

# 示例4: 返回起点后，开始向 Y 轴负方向探索
用户: 当前机械臂位置 [x:183, y:-14, z:242]。 上次相机检测是否成功：False。 已尝试 3 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "move_y", "delta_y": -80}

# 示例5: 继续向 Y 轴负方向探索
用户: 当前机械臂位置 [x:183, y:-94, z:242]。 上次相机检测是否成功：False。 已尝试 4 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "move_y", "delta_y": -80}

# 示例6: Y 轴已达负向探索边界 (例如 -174)，此方向探索完毕，但大步长未果，考虑缩小步长。此处是定位，无需检测。
用户: 当前机械臂位置 [x:183, y:-174, z:242]。 上次相机检测是否成功：False。 已尝试 5 次 Y 轴扫视。当前 Y 轴扫视步长为 80。
助理: {"action": "adjust_step", "new_step": 40}

# 示例7: 步长已缩小，返回起点，开始以小步长向 Y 轴正方向探索
用户: 当前机械臂位置 [x:183, y:-14, z:242]。 上次相机检测是否成功：False。 已尝试 6 次 Y 轴扫视。当前 Y 轴扫视步长为 40。
助理: {"action": "move_y", "delta_y": 40}

# 示例8: 在小步长探索中，目标被找到
用户: 当前机械臂位置 [x:183, y:46, z:242]。 上次相机检测是否成功：True。 已尝试 7 次 Y 轴扫视。当前 Y 轴扫视步长为 40。
助理: {"action": "found"}

# 示例9: Y 轴所有合理策略（大小步长，往返）都已用尽，仍未找到
用户: 当前机械臂位置 [x:183, y:-14, z:242]。 上次相机检测是否成功：False。 已尝试 25 次 Y 轴扫视。当前 Y 轴扫视步长为 10。
助理: {"action": "fail"}
"""


def get_scan_strategy_from_ai(current_x, current_y, current_z, detection_successful_in_last_attempt, attempts,
                              current_step):
    """
    询问 AI 下一步的扫视策略，专注于 Y 轴，并返回 JSON 格式的动作指令。
    """
    # 构造用户消息，包含当前上下文
    user_message = (
        f"当前机械臂位置 [x:{current_x}, y:{current_y}, z:{current_z}]。 "  # X, Z 告诉 AI 它们是固定的
        f"上次相机检测是否成功：{detection_successful_in_last_attempt}。 "
        f"已尝试 {attempts} 次 Y 轴扫视。当前 Y 轴扫视步长为 {current_step}。 "
        f"请根据这些信息，给出下一步的 Y 轴扫视动作策略，只返回一个JSON对象。"
    )

    messages_payload = [
        {"role": "system", "content": ai_system_prompt_for_scan},
        # 这里的 Few-shot 示例已经非常完善，可以直接使用
        # 如果模型仍旧输出额外文本，可以考虑把 Few-shot 示例中的 assistant 部分也改成严格纯JSON
        {"role": "user", "content": user_message},
    ]

    content = ""  # 初始化 content 变量

    try:
        # 使用 DeepSeek API 客户端调用
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,  # 使用 DeepSeek 模型名称
            messages=messages_payload,  # 传递消息列表
            temperature=0.2,  # 保持温度设置
            stream=False,  # 仍然不需要流式输出
            timeout=60  # DeepSeek 响应快，60秒通常足够
        )

        # 从响应中提取内容
        content = response.choices[0].message.content

        # 尝试从 content 中提取 JSON 字符串。
        # 鉴于 DeepSeek 能力较强，且提示词足够严格，可能直接返回纯JSON。
        # 但保留正则表达式解析以增强鲁棒性，应对模型偶尔的“失误”。
        json_string = content.strip()  # 默认先尝试直接解析
        json_match = re.search(r"```json\n([\s\S]*?)\n```", content)
        if json_match:
            json_string = json_match.group(1).strip()
            print(f"✅ 从模型输出中提取 JSON (通过Markdown): {json_string}") # 调试用
        else:
            print(f"✅ 从模型输出中获取 JSON (直接): {json_string}") # 调试用

        strategy = json.loads(json_string)

        # 严格验证 AI 输出 (保持不变)
        if strategy["action"] not in ["move_y", "reset_y_to_start", "adjust_step", "found", "fail"]:
            print(f"⚠️ AI 返回了不允许的动作 '{strategy['action']}'。使用默认 Y 轴移动策略。")
            raise ValueError("Invalid AI action")
        # --- 新增的打印 AI 决策的逻辑 ---
        action_type = strategy["action"]
        if action_type == "move_y":
            print(SCAN_STRATEGY_MESSAGES["move_y"].format(delta_y=strategy.get("delta_y", "未知")))
        elif action_type == "adjust_step":
            print(SCAN_STRATEGY_MESSAGES["adjust_step"].format(new_step=strategy.get("new_step", "未知")))
        else:
            print(SCAN_STRATEGY_MESSAGES.get(action_type, f"🤖 我决定：执行未知扫视动作 '{action_type}'。"))
            # --- 打印结束 ---

        return strategy
    except Exception as e:
        print(f"⚠️ 调用 Ollama 出错或解析 AI 输出失败: {e}. AI返回原始文本: {content}. 使用默认 Y 轴移动策略。")
        if attempts < 8:  # 假设前8次用当前步长
            # 默认交替左右移动，防止AI卡死在某个方向
            delta_y = current_step if (attempts % 2 == 0) else -current_step
            return {"action": "move_y", "delta_y": delta_y}
        elif attempts < 12:  # 再多尝试几次后缩小步长
            return {"action": "adjust_step", "new_step": max(10, current_step / 2)}
        else:  # 实在不行，就认为失败
            return {"action": "fail"}


if __name__ == '__main__':
    grasp_entity = zcup()
    armController_right = SerialArmControllerClass(serial_port="COM5", baud_rate=115200)
    time.sleep(4)  # 等待机械臂初始化
    armController_right.coord_ctrl(183, -14, 242, 140)
    time.sleep(3)
    # 定义一些常量，保持一致性
    OFFSET_X = 170
    OFFSET_Y = -14
    OFFSET_Z = 240
    INITIAL_ARM_X = 183
    INITIAL_ARM_Y = -14
    INITIAL_ARM_Z = 242  # 这应该是扫视时的Z值

    # --- 任务协调主循环 ---
    current_overall_task_state = "任务开始，等待操作员指令"
    red_cup_location = None  # 用于存储红杯的位置
    other_cup_location = None  # 用于存储其他杯子的位置
    is_red_cup_grasped = False  # 新增状态变量
    print("--- 机械臂倒水任务启动 ---")

    while True:
        print(f"\n--- 当前任务总体状态: {current_overall_task_state} ---")

        # 询问操作员下一步指令
        human_instruction = input(
            "请操作员输入下一步指令（例如：'开始找红杯', '抓取红杯', '找另一个杯子', '倒水', '放回红杯', '任务完成'）：")

        # 将操作员指令和当前状态传递给 AI 任务协调者
        task_action_from_ai = get_task_action_from_ai(current_overall_task_state, human_instruction)

        action_type = task_action_from_ai.get("action")

        if action_type == "start_find_red_cup":
            print("\n>>> AI 指示：开始寻找红色杯子的阶段。")

            # --- 寻找 RED 杯子 ---
            print("开始寻找红色杯子...")
            camera_data = None
            for i in range(3):  # 尝试多次识别红杯
                camera_data = grasp_entity.get_location(RED)
                if camera_data is not None and all(value != 0 for value in camera_data):
                    print(f"✅ 成功找到红色杯子！数据: {camera_data}")
                    break
                else:
                    print(f"❌ 未能找到红色杯子，第 {i + 1} 次尝试。")
                time.sleep(1)  # 每次识别间隔

            if camera_data is None or all(value == 0 for value in camera_data):
                print("红色杯子未找到。")
                current_overall_task_state = "失败：红色杯子未找到，等待操作员决策"
            else:
                red_cup_location = [
                    -camera_data[1] * 1000 + OFFSET_X + 180,
                    camera_data[0] * 1000 + OFFSET_Y - 47,
                    -camera_data[2] * 1000 + OFFSET_Z + 195
                ]
                # 安全钳位（与之前相同）
                if 0 in red_cup_location: print("警告: 坐标包含0"); sys.exit()
                red_cup_location[0] = max(100, min(400, red_cup_location[0]))
                red_cup_location[1] = max(-180, min(180, red_cup_location[1]))
                red_cup_location[2] = max(50, min(400, red_cup_location[2]))
                print(f"计算红色杯子抓取位置: {red_cup_location}")
                current_overall_task_state = "红色杯子已定位，等待操作员抓取指令"

        elif action_type == "grab_red_cup":
            if red_cup_location is None:
                print("⚠️ 红色杯子位置未知，无法执行抓取倒水操作。请先定位红色杯子。")
                current_overall_task_state = "错误：未定位红色杯子，无法执行抓取倒水"
                continue

            print("\n>>> AI 指示：执行抓取红色杯子并倒水的动作。")
            # 抓取动作
            armController_right.coord_ctrl(280, -10, 280, 90)  # 回到安全位
            time.sleep(3)
            armController_right.coord_ctrl(red_cup_location[0], red_cup_location[1], red_cup_location[2], 90, 180)  # 接近
            time.sleep(3)
            armController_right.coord_ctrl(red_cup_location[0], red_cup_location[1], red_cup_location[2], 90, 260)  # 抓取
            time.sleep(6)
            armController_right.coord_ctrl(277, red_cup_location[1], 277, 90, 260)  # 抬起
            time.sleep(3)
            is_red_cup_grasped = True  # 标记红杯已被抓取

            current_overall_task_state = "红色杯子已抓取完毕，等待操作员指令寻找接收杯"

        elif action_type == "start_scan_for_other_cup":
            print("\n>>> AI 指示：开始扫视并寻找接收水的杯子 (OTHER)。")

            # --- 寻找 OTHER 杯子 (原来的 AI 扫视逻辑) ---
            current_arm_x = INITIAL_ARM_X
            current_arm_y = INITIAL_ARM_Y
            current_arm_z = INITIAL_ARM_Z

            print(f"移动机械臂到 Y 轴扫视初始位置 [X:{current_arm_x}, Y:{current_arm_y}, Z:{current_arm_z}]...")
            armController_right.coord_ctrl(current_arm_x, current_arm_y, current_arm_z, 150, 270)
            time.sleep(5)

            scan_step = 80
            scan_attempts = 0
            max_scan_attempts = 15
            detection_successful_in_last_attempt = False
            camera_data2 = None  # 用于存储最终检测到的 OTHER 杯子数据

            print("\n--- 启动智能 Y 轴扫视查找目标杯子 (OTHER) ---")

            while camera_data2 is None or any(value == 0 for value in camera_data2):
                if scan_attempts >= max_scan_attempts:
                    print(f"‼️ Y 轴扫视尝试达到最大次数 {max_scan_attempts} 仍未识别到目标。")
                    break

                print(f"\n--- Y 轴扫视尝试 #{scan_attempts + 1} ---")
                perform_camera_scan_this_iter = True

                ai_strategy = get_scan_strategy_from_ai(
                    current_arm_x, current_arm_y, current_arm_z,
                    detection_successful_in_last_attempt, scan_attempts, scan_step
                )

                if ai_strategy["action"] == "move_y":
                    current_arm_y += ai_strategy.get("delta_y", scan_step if (scan_attempts % 2 == 0) else -scan_step)
                    print(f"AI 建议：Y 轴增量移动 {ai_strategy.get('delta_y', 'default_step')}。当前 Y={current_arm_y}")
                elif ai_strategy["action"] == "reset_y_to_start":
                    current_arm_y = INITIAL_ARM_Y
                    print(f"AI 建议：Y 轴重置到初始扫视点 {current_arm_y}。")
                    perform_camera_scan_this_iter = False
                elif ai_strategy["action"] == "adjust_step":
                    new_step = ai_strategy.get("new_step", scan_step / 2)
                    scan_step = max(10, new_step)
                    print(f"AI 建议：调整扫视步长为 {scan_step}。")
                    perform_camera_scan_this_iter = False
                elif ai_strategy["action"] == "found":
                    print("AI 认为目标已定位，尝试最后一次识别。")
                elif ai_strategy["action"] == "fail":
                    print("AI 判断多次 Y 轴扫视失败，无法找到目标。强制退出扫视。")
                    perform_camera_scan_this_iter = False
                    break

                current_arm_y = max(-180, min(180, current_arm_y))

                if ai_strategy["action"] in ["move_y", "reset_y_to_start"]:
                    print(f"机械臂移动到 Y 轴扫视位置 [X:{current_arm_x}, Y:{current_arm_y}, Z:{current_arm_z}]...")
                    armController_right.coord_ctrl(current_arm_x, current_arm_y, current_arm_z, 150, 270)
                    time.sleep(5)
                else:
                    if not perform_camera_scan_this_iter and ai_strategy["action"] not in ["fail"]:
                        scan_attempts += 1
                        detection_successful_in_last_attempt = False
                        continue

                if perform_camera_scan_this_iter:
                    temp_camera_data = None
                    max_detection_attempts_cam = 2
                    print(f"机械臂稳定，开始摄像头识别目标 (OTHER)...")
                    for j in range(max_detection_attempts_cam):
                        temp_camera_data = grasp_entity.get_location(OTHER)
                        if temp_camera_data is not None and all(v != 0 for v in temp_camera_data):
                            print(f"✅ 第 {j + 1} 次尝试，摄像头成功识别到目标！")
                            break
                        else:
                            print(f"❌ 第 {j + 1} 次尝试，摄像头未能识别到目标。")
                        time.sleep(1)

                    if temp_camera_data is not None and all(v != 0 for v in temp_camera_data):
                        camera_data2 = temp_camera_data
                        detection_successful_in_last_attempt = True
                        print("✨ 目标 OTHER 已成功定位！")
                        break
                    else:
                        detection_successful_in_last_attempt = False
                        print("继续 Y 轴扫视...")
                else:
                    detection_successful_in_last_attempt = False
                    print("本次操作为重新定位或步长调整，跳过相机检测。")

                scan_attempts += 1

            if camera_data2 is None or any(value == 0 for value in camera_data2):
                print("接收水的杯子 (OTHER) 未找到。")
                current_overall_task_state = "失败：接收水的杯子未找到，等待操作员决策"
            else:
                other_cup_location = [
                    -camera_data2[1] * 1000 + OFFSET_X - 100,
                    camera_data2[0] * 1000 + OFFSET_Y - 177,
                    -camera_data2[2] * 1000 + OFFSET_Z + 255
                ]
                # 安全钳位（与之前相同）
                if 0 in other_cup_location: print("警告: 坐标包含0"); sys.exit()
                other_cup_location[0] = max(100, min(360, other_cup_location[0]))
                other_cup_location[1] = max(-180, min(180, other_cup_location[1]))
                other_cup_location[2] = max(50, min(400, other_cup_location[2]))
                print(f"计算接收水的杯子倒水位置: {other_cup_location}")
                current_overall_task_state = "接收水的杯子 (OTHER) 已定位，等待操作员倒水指令"

        elif action_type == "pour_into_other_cup":
            if not is_red_cup_grasped:  # 确保红杯被抓取
                print("⚠️ 红色杯子未被抓取。请先抓取。")
                current_overall_task_state = "错误：红色杯子未抓取，无法倒水"
                continue
            if other_cup_location is None:
                print("⚠️ 接收水的杯子位置未知，无法执行倒水操作。请先定位接收水的杯子。")
                current_overall_task_state = "错误：未定位接收杯子，无法倒水"
                continue

            print("\n>>> AI 指示：将红色杯子中的水倒入接收水的杯子。")
            # 倒水动作
            armController_right.coord_ctrl(277, other_cup_location[1], 277, 90, 260)  # 移动到目标杯上方
            time.sleep(6)
            armController_right.coord_ctrl(other_cup_location[0], other_cup_location[1], other_cup_location[2], 220,
                                           260)  # 倒水姿态
            time.sleep(4)
            armController_right.coord_ctrl(other_cup_location[0], other_cup_location[1], other_cup_location[2], 220,
                                           250)  # 倾倒
            time.sleep(6)

            print("倒水操作完成！")
            current_overall_task_state = "已将水倒入接收杯，等待操作员放回红杯指令"

        elif action_type == "return_red_cup":
            if not is_red_cup_grasped:
                print("⚠️ 红色杯子未被抓取。无法放回。")
                current_overall_task_state = "错误：红色杯子未抓取，无法放回"
                continue

            print("\n>>> AI 指示：将红色杯子放回原位。")
            # 放回杯子
            armController_right.coord_ctrl(277, -14, 277, 90, 260)  # 回到安全位
            time.sleep(4)
            armController_right.coord_ctrl(red_cup_location[0], red_cup_location[1], red_cup_location[2], 90,
                                           260)  # 接近原位
            time.sleep(4)
            armController_right.coord_ctrl(red_cup_location[0], red_cup_location[1], red_cup_location[2], 90, 180)  # 放下
            time.sleep(3)
            armController_right.coord_ctrl(277, -14, 277, 90, 180)  # 回到初始安全位

            print("红色杯子已放回原位。")
            # ... 放回动作后 ...
            is_red_cup_grasped = False  # 标记红杯已放回
            current_overall_task_state = "所有操作完成，等待操作员结束任务"

        elif action_type == "task_complete":
            print("\n>>> AI 指示：所有任务已成功完成。程序将退出。")
            break  # 退出主循环

        elif action_type == "abort_task":
            reason = task_action_from_ai.get("reason", "未知原因")
            print(f"\n‼️ AI 指示：任务中止。原因: {reason}")
            sys.exit(1)  # 强制程序退出并带上错误码

        else:  # 兜底，防止AI返回未知动作
            print(f"\n‼️ AI 任务协调者返回了未知的动作 '{action_type}'。中止任务。")
            sys.exit(1)









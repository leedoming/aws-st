import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import pandas as pd
import random

# Pandas를 사용하여 CSV 파일 읽기
df = pd.read_csv('recipe_q.csv', encoding='utf-8', header=0)

# 슬랙 앱 토큰 설정
bot_token = '_your bot token_'  # 본인의 슬랙 봇 토큰으로 대체해야 합니다.
app_token = '_your app token_'  # 본인의 슬랙 앱 토큰으로 대체해야 합니다.

app = App(
    token=bot_token,
    signing_secret='_your signing secret_'  # Slack 앱 설정에서 가져온 signing secret으로 대체해야 합니다.
)

# 슬랙 이벤트 처리 함수
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
import re
import boto3
from slack_bolt.adapter.socket_mode import SocketModeHandler
import json

app = App(token=bot_token)
slack_client = WebClient(token=bot_token)

# 사용자 입력을 저장할 딕셔너리
user_inputs = {}
responses = [] * 3
gender = ""


# 메시지 이벤트 처리 함수
@app.message(re.compile('식단'))
def regex(message, say):
    say("눈송플레이크 팀의 기초대사량 맞춤 식단 추천 챗봇입니다.")
    handle_age_input(message["channel"])


def handle_age_input(channel_id):
    try:
        blocks = [
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "age_input"
                },
                "label": {
                    "type": "plain_text",
                    "text": "나이"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "다음"
                        },
                        "action_id": "age_next"
                    }
                ]
            }
        ]
        response = slack_client.chat_postMessage(channel=channel_id, blocks=blocks)
        return response
    except SlackApiError as e:
        print(f"메시지 전송 오류: {e.response['error']}")


# 나이 입력 액션 이벤트 처리 함수
@app.action("age_next")
def age_next_action(ack, body):
    ack()

    # 사용자 입력을 저장하고 다음 입력 필드 보여주기
    key = list(body["state"]["values"].keys())[0]
    user_inputs["age"] = body["state"]["values"][key]["age_input"]["value"]
    handle_weight_input(body["container"]["channel_id"])


def handle_weight_input(channel_id):
    try:
        blocks = [
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "weight_input"
                },
                "label": {
                    "type": "plain_text",
                    "text": "체중"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "다음"
                        },
                        "action_id": "weight_next"
                    }
                ]
            }
        ]
        response = slack_client.chat_postMessage(channel=channel_id, blocks=blocks)
        return response
    except SlackApiError as e:
        print(f"메시지 전송 오류: {e.response['error']}")


# 체중 입력 액션 이벤트 처리 함수
@app.action("weight_next")
def weight_next_action(ack, body):
    ack()

    # 사용자 입력을 저장하고 다음 입력 필드 보여주기
    key = list(body["state"]["values"].keys())[0]
    user_inputs["weight"] = body["state"]["values"][key]["weight_input"]["value"]
    handle_height_input(body["container"]["channel_id"])


def handle_height_input(channel_id):
    try:
        blocks = [
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "height_input"
                },
                "label": {
                    "type": "plain_text",
                    "text": "키"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "완료"
                        },
                        "action_id": "height_next"
                    }
                ]
            }
        ]
        response = slack_client.chat_postMessage(channel=channel_id, blocks=blocks)
        return response
    except SlackApiError as e:
        print(f"메시지 전송 오류: {e.response['error']}")


# 체중 입력 액션 이벤트 처리 함수
@app.action("height_next")
def height_next_action(ack, body):
    ack()

    # 사용자 입력을 저장하고 응답 전송
    key = list(body["state"]["values"].keys())[0]
    user_inputs["height"] = body["state"]["values"][key]["height_input"]["value"]
    handle_gender_input(body["container"]["channel_id"])


def handle_gender_input(channel_id):
    try:
        blocks = [
            {"type": "actions",
             "elements": [
                 {
                     "type": "button",
                     "text": {
                         "type": "plain_text",
                         "text": "여성",
                         "emoji": True
                     },
                     "value": "click_me_123",
                     "action_id": "actionId-0"
                 },
                 {
                     "type": "button",
                     "text": {
                         "type": "plain_text",
                         "text": "남성",
                         "emoji": True
                     },
                     "value": "click_me_123",
                     "action_id": "actionId-1"
                 }
             ]
             }
        ]
        response = slack_client.chat_postMessage(channel=channel_id, blocks=blocks)
        return response
    except SlackApiError as e:
        print(f"메시지 전송 오류: {e.response['error']}")

#기초대사량 계산 및 메시지 출력 함수
def calculate_diet(user_inputs, gender):
    age = float(user_inputs.get('age'))
    weight = float(user_inputs.get('weight'))
    height = float(user_inputs.get('height'))

    if gender == "여성":
        # Harris-Benedict 공식을 이용한 기초대사량 계산 (여성)
        bmr = 65 + (9.6 * weight) + (1.8 * height) - (4.7 * age)
    elif gender == "남성":
        # Harris-Benedict 공식을 이용한 기초대사량 계산 (남성)
        bmr = 66 + (13.7 * weight) + (5 * height) - (6.8 * age)

    breakfast_ratio = 0.3
    lunch_ratio = 0.4
    dinner_ratio = 0.3

    # 'calories' 열에 있는 값을 숫자로 변환하되, 무효한 값은 NaN으로 대체
    df['calories'].astype(float)
    df['name'].astype(str)
    str(df['idx'])

    # NaN 값이 있는 행 제거
    df.dropna(subset=['calories'], inplace=True)

    # 아침, 점심, 저녁에 할당되는 칼로리 계산
    breakfast_calories = bmr * breakfast_ratio
    lunch_calories = bmr * lunch_ratio
    dinner_calories = bmr * dinner_ratio

    # 칼로리 범위에 맞는 레시피 필터링
    breakfast_candidates = df[(df['calories'] >= breakfast_calories * 0.8) & (df['calories'] <= breakfast_calories * 1.1)]
    lunch_candidates = df[(df['calories'] >= lunch_calories * 0.8) & (df['calories'] <= lunch_calories * 1.1)]
    dinner_candidates = df[(df['calories'] >= dinner_calories * 0.8) & (df['calories'] <= dinner_calories * 1.1)]

    # 랜덤으로 아침, 점심, 저녁 레시피 선택
    breakfast_choice = random.choice(breakfast_candidates.index)
    lunch_choice = random.choice(lunch_candidates.index)
    dinner_choice = random.choice(dinner_candidates.index)

    # 선택된 레시피 정보 및 링크 가져오기
    breakfast_recipe = df.loc[breakfast_choice]
    lunch_recipe = df.loc[lunch_choice]
    dinner_recipe = df.loc[dinner_choice]

    link = "https://ottogi.okitchen.co.kr/category/detail.asp?idx="

    message = f"기초대사량 ({gender}): {bmr:.2f} kcal/day\n"
    message += "아침 레시피 추천: " + breakfast_recipe['name'] + f" ({breakfast_recipe['calories']} kcal)" + "\n"
    message += "아침 레시피 링크: " + link + str(breakfast_recipe['idx']) + "\n"
    message += "점심 레시피 추천: " + lunch_recipe['name'] + f" ({lunch_recipe['calories']} kcal)" + "\n"
    message += "점심 레시피 링크: " + link + str(lunch_recipe['idx']) + "\n"
    message += "저녁 레시피 추천: " + dinner_recipe['name'] + f" ({dinner_recipe['calories']} kcal)" + "\n"
    message += "저녁 레시피 링크: " + link + str(dinner_recipe['idx'])

    return message

# 성별 입력 액션 이벤트 처리 함수
@app.action("actionId-0")
def gender_female_action(ack, body, say):
    ack()
    gender = "여성"
    message = calculate_diet(user_inputs, gender)
    say(message)

# 성별 입력 액션 이벤트 처리 함수
@app.action("actionId-1")
def gender_male_action(ack, body, say):
    ack()
    gender = "남성"
    message = calculate_diet(user_inputs, gender)
    say(message)

if __name__ == "__main__":
    handler = SocketModeHandler(app_token=app_token, app=app)
    handler.start()

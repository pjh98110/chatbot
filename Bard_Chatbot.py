import streamlit as st
from streamlit_chat import message
from bardapi import Bard
import os
import requests
import pandas as pd


DATA_PATH = "./"

# 데이터 불러오는 함수(캐싱)
@st.cache_data(ttl=900)  # 캐싱 데코레이터
def load_csv(path):
    return pd.read_csv(path)

# 데이터 불러오기
data = load_csv(f"{DATA_PATH}predicted_data.csv")


API_KEY = st.sidebar.text_input(":blue[Enter Your OPENAI API-KEY :key:]", 
                placeholder="Bard API 키를 입력하세요! (sk-...)",
                type="password", key= "password", help="[바드 API KEY 가져오는 방법] 구글 로그아웃 --> 로그인 --> bard.google.com --> F12(개발자 모드) --> 애플리케이션 --> 쿠키(bard.google.com) --> __Secure-1PSID --> 값을 복사하기 입력하기")

os.environ["_BARD_API_KEY"] = API_KEY


session = requests.Session()
session.headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }
session.cookies.set("__Secure-1PSID", os.getenv("_BARD_API_KEY")) 




# 질문-답변 로직 구성
# 'generated'와 'past' 키 초기화
st.session_state.setdefault('generated', [{'type': 'normal', 'data': "원하시는 지역을 입력해주세요."}])
st.session_state.setdefault('past', ['인구수 추세와 정보를 알고 싶어, 어떻게 하면 될까?'])
st.session_state.setdefault('chat_stage', 1)



st.markdown(f"""
            <span style='font-size: 30px;'>
            <div style=" color: #19a83b">
                <strong> 인구수 예측 Chatbot </strong>
            </div>
            """, unsafe_allow_html=True)
st.divider()


chat_placeholder = st.empty()



def on_btn_click():
    st.session_state['past'] = ['인구수 추세와 정보를 알고 싶어, 어떻게 하면 될까?']
    st.session_state['generated'] = [{'type': 'normal', 'data': "원하시는 지역을 입력해주세요."}]
    st.session_state['chat_stage'] = 1

if 'user_input' not in st.session_state: # user_input 키 초기화
    st.session_state['user_input'] = ""

def on_input_change():
    user_input = st.session_state.user_input
    st.session_state.past.append(user_input)
    # 사용자 입력 후, 입력 필드 초기화
    st.session_state['user_input'] = ""

    # target 키 초기화
    st.session_state.setdefault('target', '')   

    if st.session_state['chat_stage'] == 1:
        st.session_state['target'] = user_input
        try:
            input_str = st.session_state['target'] # 화성시
            target = data[data["월별"] == "24-10-01"]["총인구"].values[0] 
            # 화성시 인구예측 모델로 예측한 약 100만명의 총인구 달성하는 시점
            target_str = f"""24년 10월 1일 {input_str}의 총인구는 {target}명으로 예측되며, {input_str}의 
            총인구가 증가하는 이유는 수도권 외부 유입, 아동친화도시, 산업단지 개발, 관광지 개발 등이 있으며 
            앞으로 {input_str} 미래 총인구가 증가하는 이유에 대해 자세하게 설명해줘""" 
            # 인구예측 모델분석결과와 예시를 Bard API에 함께 전달
            
            bard = Bard(token=os.environ["_BARD_API_KEY"], token_from_browser=True, session=session, timeout=30)
            response = bard.get_answer(target_str)
            st.session_state['generated'].append({"type": "normal", "data": response['content']})
                
        except Exception as e:
            st.error(f"API 요청 중 오류가 발생했습니다.쿠키를 초기화하고 새로운 API 키를 입력해 주세요. ")
            response = {'content': 'API 요청에 문제가 발생했습니다. 쿠키를 초기화하고 새로운 API 키를 입력해 주세요..'}

with chat_placeholder.container():
    for i in range(len(st.session_state['generated'])):
        message(st.session_state['past'][i], is_user=True, key=f"{i}_user")
        message(
            st.session_state['generated'][i]['data'],
            key=f"{i}",
            allow_html=True,
            is_table=True if st.session_state['generated'][i]['type'] == 'table' else False
        )
    
    st.button("대화 초기화", on_click=on_btn_click, key="clear_key")

with st.container():
    st.text_input("챗봇과 대화하기:", value=st.session_state['user_input'], on_change=on_input_change, key="user_input", help="대화 초기화 버튼을 누르면 초기화면으로 돌아옵니다.")

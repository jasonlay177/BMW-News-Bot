import base64
from datetime import datetime, timedelta
import os
import urllib.parse
import xml.etree.ElementTree as ET
import google.generativeai as genai
import requests

# 1. API 키 및 설정 (GitHub Secret에서 가져옴)
api_key = os.environ.get("GEMINI_API_KEY")
public_api_key = os.environ.get("PUBLIC_API_KEY")  # 공공데이터포털 인증키

# 워드프레스 연동 정보 설정
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

if not api_key or not public_api_key:
    raise ValueError("필요한 API 키(Gemini 또는 공공데이터)가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


def get_real_estate_data():
    print("🏠 국토교통부 아파트 실거래가 데이터를 수집하는 중...")

    # 조회 기준년월 (예: 전달 데이터 조회)
    target_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m")
    # 예시 법정동 코드: 서울특별시 강남구 (지역 코드는 필요에 따라 변경 가능)
    lawd_cd = "11680"

    # 국토교통부 아파트매매 실거래가 오픈API 엔드포인트
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

    # 🔑 핵심: 인코딩된 키를 가져와서 파이썬으로 디코딩(Decoding)합니다!
    decoded_service_key = urllib.parse.unquote(public_api_key)
    
    params = {
        "serviceKey": decoded_service_key,  # 👈 디코딩된 키를 파라미터에 전달
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": target_date,
        "numOfRows": "10",
    }

    try:
        # requests가 자동으로 다시 인코딩하는 것을 방지하기 위해
        # params 대신 url에 직접 파라미터를 조합해서 보내는 방법도 안전합니다.
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ 공공데이터 API 호출 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")  # 에러 원인 확인용
            return None

        # XML 응답 파싱
        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        if not items:
            print("⚠️ 수집된 실거래가 데이터가 없습니다.")
            return None

        data_list = []
        for item in items:
            apt_name = (
                item.find("aptNm").text
                if item.find("aptNm") is not None
                else "정보 없음"
            )
            deal_amount = (
                item.find("dealAmount").text.strip()
                if item.find("dealAmount") is not None
                else "정보 없음"
            )
            area = (
                item.find("excluUseAr").text
                if item.find("excluUseAr") is not None
                else "정보 없음"
            )
            floor = (
                item.find("floor").text
                if item.find("floor") is not None
                else "정보 없음"
            )
            dong = (
                item.find("umdNm").text
                if item.find("umdNm") is not None
                else "정보 없음"
            )

            data_list.append(
                f"단지명: {apt_name} ({dong}), 전용면적: {area}㎡, 층수: {floor}층, 거래금액: {deal_amount}만원"
            )

        return "\n".join(data_list)

    except Exception as e:
        print(f"❌ 데이터 처리 중 오류 발생: {e}")
        return None


def summarize_real_estate(raw_data):
    print("🤖 Gemini AI가 부동산 실거래가 동향 분석 및 리포트 작성 중...")
    prompt = f"""
    당신은 전문 부동산 애널리스트입니다. 아래의 국토교통부 아파트 실거래가 원본 데이터를 바탕으로,
    무주택자와 실거주 투자자들이 이해하기 쉽도록 '주간 부동산 실거래가 동향 리포트' 웹 블로그 포스트를 작성해 주세요.
    
    반드시 아래의 구조와 규칙을 지켜서 순수 HTML 태그 문자열만 반환해 주세요. (Markdown 백틱 ```html ... ``` 절대 사용 금지)

    [포스팅 구성 및 작성 규칙]
    - 도입부 박스 생성:
      <div style="background-color: #f7fafc; padding: 15px 20px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; margin-bottom: 0; color: #2d3748;">🏠 주요 지역 아파트 실거래가 트렌드</h3>
      </div>
       
    - 본문: 수집된 거래 내역을 바탕으로 주요 단지의 시세 특징을 분석해 주세요.
      - <h3> 태그를 사용하여 주요 단지별 거래 소식을 보기 좋게 정리해 주세요.
      - 본문 내용은 <ul>과 <li> 태그를 사용하여 가격대와 면적별 특징을 핵심 요약해 주세요.
      - 중요한 가격이나 면적 수치는 <strong> 태그로 강조해 주세요.
      - 마지막에는 무주택자나 매수 대기자를 위한 간단한 조언 한 줄을 덧붙여 주세요.

    [실거래가 원본 데이터]
    {raw_data}
    """
    response = model.generate_content(prompt)
    return response.text


def post_to_wordpress(title, summary_text):
    print("📝 스타일이 적용된 부동산 포스팅을 워드프레스에 전송하는 중...")

    if not WP_URL or not WP_USER or not WP_APP_PASSWORD:
        print("⚠️ 워드프레스 설정(Secret)이 누락되어 포스팅을 건너뜁니다.")
        return

    api_url = f"{WP_URL}/wp-json/wp/v2/posts"
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }

    data = {
        "title": title,
        "content": summary_text,
        "status": "publish",
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 201:
            print("✨ 성공적으로 부동산 포스팅이 완료되었습니다!")
        else:
            print(f"❌ 포스팅 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 통신 중 오류 발생: {e}")


if __name__ == "__main__":
    raw_data = get_real_estate_data()
    if not raw_data:
        print("수집된 부동산 데이터가 없습니다.")
    else:
        summary = summarize_real_estate(raw_data)
        
        today_date = datetime.now().strftime("%Y년 %m월")
        post_title = f"🏠 [{today_date}] 주요 지역 아파트 실거래가 및 시장 동향 리포트"

        post_to_wordpress(post_title, summary)

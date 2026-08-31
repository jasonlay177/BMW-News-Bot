import base64
from datetime import datetime
import os
import feedparser
import google.generativeai as genai
import requests  # 워드프레스 REST API 통신용 라이브러리

# 1. API 키 및 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")

# 워드프레스 연동 정보 설정
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

if not api_key:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")  # 안정적인 모델 버전


def get_ev_trend_data():
    print("🔋 친환경차 및 전기차 보급/충전 인프라 관련 최신 트렌드 수집 중...")
    
    # 구글 뉴스 RSS를 통해 최신 전기차 보조금, 충전소, 보급 현황 관련 뉴스 수집
    rss_url = (
        "https://news.google.com/rss/search?q=%EC%A0%84%EA%B8%B0%EC%B0%A8+%EB%B3%B4%EC%A1%B0%EA%B8%88+%EC%B6%A9%EC%A0%84%EC%86%8C&hl=ko&gl=KR&ceid=KR:ko"
    )
    feed = feedparser.parse(rss_url)

    news_list = []
    for entry in feed.entries[:5]:
        news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

    return "\n".join(news_list)


def summarize_ev_report(news_text):
    print("🤖 AI 자동차 전문 기자가 전기차 보조금 및 인프라 리포트를 작성 중...")
    prompt = f"""
    당신은 전문 자동차 기자입니다. 아래의 최신 전기차 보조금 및 인프라 관련 뉴스 데이터를 바탕으로, 
    전기차 예비 구매자들이 가장 궁금해할 '전국 지역별 전기차 보급 현황 및 보조금 가이드' 웹 블로그 포스트를 작성해 주세요.
    작성 시 본인은 'AI 자동차 전문 기자'라는 점을 명확히 밝혀주세요.
    
    반드시 아래의 구조와 HTML 표(Table) 형식을 포함하여 순수 HTML 태그 문자열만 반환해 주세요. (Markdown 백틱 ```html ... ``` 절대 사용 금지)

    [포스팅 구성 및 작성 규칙]
    - 도입부: AI 자동차 전문 기자 소개 및 올해 전기차 구매 지원금 요약 개요
    - 본문 내 가상의 지역별 보조금/보급 현황 요약 표 삽입:
      <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
        <thead>
          <tr style="background-color: #f7fafc; border-bottom: 2px solid #e2e8f0;">
            <th style="padding: 10px; text-align: left;">구분 (지역/항목)</th>
            <th style="padding: 10px; text-align: center;">국고 보조금 / 평균 충전 인프라</th>
            <th style="padding: 10px; text-align: right;">지자체 보조금 현황</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom: 1px solid #edf2f7;">
            <td style="padding: 10px;">서울시</td>
            <td style="padding: 10px; text-align: center;"><strong>기준 금액 적용</strong></td>
            <td style="padding: 10px; text-align: right;">예산 소진 임박 / 확인 필요</td>
          </tr>
          <tr style="border-bottom: 1px solid #edf2f7;">
            <td style="padding: 10px;">경기도</td>
            <td style="padding: 10px; text-align: center;"><strong>충전 인프라 확충 중</strong></td>
            <td style="padding: 10px; text-align: right;">지자체별 상이</td>
          </tr>
        </tbody>
      </table>
    - 상세 내용: 수집된 최신 뉴스를 바탕으로 핵심 포인트 3가지를 <ul>과 <li> 태그로 정리해 주세요.
    - 마무리: 예비 오너들을 위한 실용적인 조언 한 줄 덧붙이기.

    [뉴스 원본 참고 자료]
    {news_text}
    """
    response = model.generate_content(prompt)
    return response.text


def post_to_wordpress(title, summary_text):
    print("📝 스타일이 적용된 전기차 리포트를 워드프레스에 전송하는 중...")

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
            print("✨ 친환경차 리포트 워드프레스 포스팅 완료!")
        else:
            print(f"❌ 포스팅 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 통신 중 오류 발생: {e}")


if __name__ == "__main__":
    news_data = get_ev_trend_data()  
    if not news_data:
        print("수집된 데이터가 없습니다.")
    else:
        summary = summarize_ev_report(news_data)
        print("\n" + "=" * 40)
        print("✨ [전기차 보급 및 보조금 리포트 요약 결과]")
        print("=" * 40)
        print(summary)

        today_date = datetime.now().strftime("%Y년 %m월 %d일")
        post_title = f" 전국 지역별 전기차 보조금 및 충전 인프라 가이드 ({today_date})"

        post_to_wordpress(post_title, summary)

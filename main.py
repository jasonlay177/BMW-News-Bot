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
model = genai.GenerativeModel("gemini-3.5-flash")  # 안정적인 모델 버전


def get_bmw_news():
    print("🚗 BMW 관련 최신 자동차 뉴스를 수집하는 중...")
    # 구글 뉴스 RSS에서 BMW 관련 최신 뉴스 검색 (한국어 기준)
    rss_url = (
        "https://news.google.com/rss/search?q=BMW&hl=ko&gl=KR&ceid=KR:ko"
    )
    feed = feedparser.parse(rss_url)

    news_list = []
    # 최신 뉴스 5개를 수집합니다.
    for entry in feed.entries[:5]:
        news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

    return "\n".join(news_list)


def summarize_bmw_news(news_text):
    print("🤖 AI 자동차 전문 기자가 BMW 최신 뉴스 5가지를 심층 분석 중...")
    prompt = f"""
    당신은 전문 자동차 기자입니다. 아래의 최신 BMW 관련 뉴스 원본 데이터를 바탕으로, 
    독자들과 자동차 애호가들이 가장 먼저 확인해야 할 '오늘의 BMW 이슈 브리핑' 웹 블로그 포스트를 작성해 주세요.
    작성 시 본인은 'AI 자동차 전문 기자'라는 점을 명확히 밝혀주세요.
    사실에 기반하여 작성하되, 객관적이고 깊이 있는 분석 내용을 담아주세요.
    
    반드시 아래의 구조와 규칙을 지켜서 순수 HTML 태그 문자열만 반환해 주세요. (Markdown 백틱 ```html ... ``` 절대 사용 금지)

    [포스팅 구성 및 작성 규칙]
    - 도입부: AI 자동차 전문 기자 소개 및 오늘 다룰 BMW 핵심 이슈 안내
    - 본문: 수집된 BMW 뉴스를 파급 효과 및 중요도가 **높은 순서(임팩트 1위부터 5위)**로 엄선하여 정리
        - 총 5가지 뉴스를 순서대로 나열해 주세요.
        - 각 뉴스 제목은 <h3> 태그를 사용하고 앞에 순위를 붙여주세요. (예: <h3>1: [뉴스 제목]</h3>)
        - 본문 내용은 <ul>과 <li> 태그를 사용하여 핵심 요약 2~3가지로 정돈해 주세요.
        - 중요한 자동차 기술, 모델명, 수치 등은 <strong> 태그로 강조해 주세요.
        - 각 뉴스 마지막 줄에 관련 모델이나 핵심 키워드를 괄호 안에 표기해 주세요. (예: (BMW iX3))

    [뉴스 원본 참고 자료]
    {news_text}
    """
    response = model.generate_content(prompt)
    return response.text


# 워드프레스 자동 포스팅 함수
def post_to_wordpress(title, summary_text):
    print("📝 스타일이 적용된 BMW 포스팅을 워드프레스에 전송하는 중...")

    if not WP_URL or not WP_USER or not WP_APP_PASSWORD:
        print("⚠️ 워드프레스 설정(Secret)이 누락되어 포스팅을 건너뜁니다.")
        return

    api_url = f"{WP_URL}/wp-json/wp/v2/posts"

    # Basic Auth 인증 헤더 생성
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
            print("✨ 멋지게 꾸며진 BMW 워드프레스 포스팅 완료!")
        else:
            print(f"❌ 포스팅 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 통신 중 오류 발생: {e}")


if __name__ == "__main__":
    news_data = get_bmw_news()  
    if not news_data:
        print("수집된 BMW 뉴스가 없습니다.")
    else:
        summary = summarize_bmw_news(news_data)
        print("\n" + "=" * 40)
        print("✨ [오늘의 BMW 뉴스 요약 결과]")
        print("=" * 40)
        print(summary)

        # 포스팅 제목 생성 (오늘 날짜 포함)
        today_date = datetime.now().strftime("%Y년 %m월 %d일")
        post_title = f"🚗 [AI 자동차 기자] 오늘의 BMW 핵심 뉴스 브리핑 ({today_date})"

        # 워드프레스 포스팅 실행
        post_to_wordpress(post_title, summary)

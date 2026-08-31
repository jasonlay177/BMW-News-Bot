import base64
from datetime import datetime
import os
import feedparser
import google.generativeai as genai
import requests  # 워드프레스 REST API 통신용 라이브러리

# 1. API 키 및 설정 (GitHub Secret에서 안전하게 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")

# 이메일 관련 변수 (현재는 주석 처리됨)
# sender_email = os.environ.get("MY_EMAIL")
# email_password = os.environ.get("EMAIL_PASSWORD")
# receiver_email = os.environ.get("RECEIVER_EMAIL")

# 워드프레스 연동 정보 설정 (요청하신 변수명 적용)
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

if not api_key:
  raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")  # 안정적인 모델 버전


def get_economic_news():
  print("📈 오늘의 주요 경제 뉴스를 수집하는 중...")
  # 구글 뉴스 RSS에서 경제 관련 최신 뉴스 검색
  rss_url = (
      "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C&hl=ko&gl=KR&ceid=KR:ko"
  )
  feed = feedparser.parse(rss_url)

  news_list = []
  # 상위 5개의 뉴스를 수집하도록 넉넉히 가져옵니다
  for entry in feed.entries[:5]:
    news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")

  return "\n".join(news_list)


def summarize_news(news_text):
  print(
      "🤖 Gemini AI가 미국 증시 마감 분석 및 국내 주요 경제 뉴스 임팩트 순"
      " 선별 중..."
  )
  prompt = f"""
    당신은 전문 수석 애널리스트입니다. 아래의 원본 뉴스와 전일 글로벌 시장의 흐름을 바탕으로, 
    오늘 국내 투자자들이 가장 먼저 확인해야 할 '프리미엄 모닝 브리핑' 웹 블로그 포스트를 작성해 주세요.
    본인을 소개할때는 AI 애널리스트라는 걸 밝혀주고요.
    
    반드시 아래의 구조와 규칙을 지켜서 순수 HTML 태그 문자열만 반환해 주세요. (Markdown 백틱 ```html ... ``` 절대 사용 금지)

    [포스팅 구성 및 작성 규칙]
         
    3. 본문: 주식 시장에 미치는 파급 효과가 **가장 큰 순서(임팩트 1위부터 5위)**로 엄선한 국내외 주요 경제 뉴스
       - 총 5가지 뉴스를 순서대로 나열해 주세요.
       - 각 뉴스 제목은 <h3> 태그를 사용하고 앞에 순위(예: 1, 2...)를 붙여주세요. (예: <h3>1: 타이틀내용</h3>)
       - 본문 내용은 <ul>과 <li> 태그를 사용하여 핵심 요약 2~3가지로 정리해 주세요.
       - 중요한 경제 키워드나 수치는 <strong> 태그로 강조해 주세요.
       - 각 뉸스 마지막에 한줄 추가하여 해당뉴스에 영향을 가장 많이 받는 국내 상장사 하나를 () 안에 넣어주세요. (예: (삼성전자))

    [뉴스 원본 참고 자료]
    {news_text}
    """
  response = model.generate_content(prompt)
  return response.text


# [주석 처리] 기존 GitHub Pages용 HTML 파일 생성 함수
# def save_to_html(summary_text):
#     ...


# [주석 처리] 기존 이메일 발송 함수
# def send_email(summary_text):
#     ...


# 워드프레스 자동 포스팅 함수
def post_to_wordpress(title, summary_text):
  print("📝 스타일이 적용된 포스팅을 워드프레스에 전송하는 중...")

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

  # Gemini가 이미 HTML 태그를 포함해서 주므로 replace 없이 그대로 사용합니다!
  data = {
      "title": title,
      "content": summary_text,
      "status": "publish",
      # "categories": [1] # 필요하다면 워드프레스의 카테고리 ID 번호를 넣을 수 있습니다.
  }

  try:
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 201:
      print("✨ 멋지게 꾸며진 워드프레스 포스팅 완료!")
    else:
      print(f"❌ 포스팅 실패: {response.status_code}, {response.text}")
  except Exception as e:
    print(f"❌ 통신 중 오류 발생: {e}")

 
if __name__ == "__main__":
  news_data = get_economic_news()  # 함수 이름 변경 반영
  if not news_data:
    print("수집된 뉴스가 없습니다.")
  else:
    summary = summarize_news(news_data)
    print("\n" + "=" * 40)
    print("✨ [오늘의 경제 뉴스 요약 결과]")
    print("=" * 40)
    print(summary)

    # 포스팅 제목 생성 (오늘 날짜 포함)
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    post_title = f" 오늘의 경제 뉴스 브리핑 ({today_date})"

    # 워드프레스 포스팅 실행
    post_to_wordpress(post_title, summary)

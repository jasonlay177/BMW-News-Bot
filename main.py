import os
import feedparser
import google.generativeai as genai

# 1. Gemini API 키 설정 (GitHub에 안전하게 숨겨둔 키를 가져옵니다)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다!")

genai.configure(api_key=api_key)
# 최신 Gemini 모델 지정
model = genai.GenerativeModel('gemini-1.5-flash')

def get_bmw_news():
    print("🚗 BMW 최신 뉴스를 수집하는 중...")
    # 구글 뉴스 RSS에서 'BMW' 검색 결과 가져오기 (한국어)
    rss_url = "https://news.google.com/rss/search?q=BMW&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    # 가장 최신 뉴스 3개만 가져오기
    news_list = []
    for entry in feed.entries[:3]:
        news_list.append(f"제목: {entry.title}\n링크: {entry.link}\n")
    
    return "\n".join(news_list)

def summarize_news(news_text):
    print("🤖 Gemini AI가 뉴스를 요약하는 중...")
    prompt = f"""
    다음은 최근 BMW 관련 뉴스 목록입니다. 
    이 내용들을 바탕으로 블로그 독자들이 읽기 쉽도록 핵심 내용 3가지를 뽑아 친근하고 깔끔한 어조로 요약해 주세요.

    [뉴스 원본]
    {news_text}
    """
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    # 뉴스 가져오기
    news_data = get_bmw_news()
    if not news_data:
        print("수집된 뉴스가 없습니다.")
    else:
        # AI 요약하기
        summary = summarize_news(news_data)
        print("\n" + "="*40)
        print("✨ [BMW 뉴스 요약 결과]")
        print("="*40)
        print(summary)

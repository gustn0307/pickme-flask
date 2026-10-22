import os
import json
from google import genai
from google.genai import types

class ChatService:
    
    @staticmethod
    def validate_input(text):
        """기본적인 빈 입력만 체크"""
        if not text or not text.strip():
            return False, "내용을 입력해 주세요."
        if len(text.strip()) <= 1:
            return False, "조금 더 자세히 입력해 주세요."
        return True, ""

    @staticmethod
    def get_ai_response(message, tone="empathy"):
        """
        Gemini API 호출을 시도하되, 쿼터 초과나 에러 발생 시 
        자동으로 스마트 폴백(시뮬레이션)으로 전환하여 서비스 중단 방지
        """
        api_key = os.environ.get("GEMINI_API_KEY")

        # API 키가 없거나 형식이 잘못된 경우 바로 폴백
        if not api_key or api_key.startswith("your_"):
            return ChatService._get_smart_fallback(message, tone)

        try:
            client = genai.Client(api_key=api_key)

            system_instruction = """
            당신은 의사결정 지원 및 상담 AI 서비스 'PickMe AI'입니다. 
            사용자의 입력 문맥을 스스로 깊이 있게 이해하고 분석하여, 반드시 아래 JSON 구조로만 응답하세요. 백틱(```) 없이 순수 JSON만 반환하세요.

            [판단 기준]
            1. is_crisis (boolean): 자살, 자해 등 생명과 직결된 위기 상황인지 여부.
            2. is_harmful (boolean): 타인에게 피해를 주는 행위, 범죄 모의, 불법, 폭력 등 비윤리적 내용인지 여부.
            3. is_general_chat (boolean): 진지한 선택이나 고민 상담이 아닌, 단순 인사, 일상 잡담, 챗봇 정체성 질문("너 누구야" 등)인지 여부.
            4. reply (string): 
               - is_crisis가 true면: 따뜻한 위로와 함께 자살예방 상담전화(1393) 등 안내.
               - is_harmful이 true면: 타인에게 피해를 주는 내용은 상담할 수 없다는 거부 메시지.
               - is_general_chat이 true면: PickMe AI는 선택/고민 상담 전문 서비스임을 알리고 구체적인 고민을 유도하는 메시지.
               - 정상적인 고민이면: 사용자의 성향(tone)에 맞춰 답변 작성 및 하단에 선택지 2개 정리.
            5. parsed_data (object or null): 정상적인 고민일 때만 {"title": "고민 제목", "category": "카테고리", "options": ["선택지1", "선택지2"]} 작성. 위기/유해/잡담인 경우 반드시 null 설정.
            """

            prompt = f"사용자 성향(tone): {tone}\n사용자 입력: {message}"

            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    response_mime_type="application/json"
                ),
            )

            result_data = json.loads(response.text)

            if result_data.get("is_crisis"):
                return {
                    "reply": (
                        "많이 힘들고 지치셨군요. 지금 겪고 계신 고통은 혼자 감내하기 버거울 수 있습니다.\n"
                        "전문가의 도움을 받을 수 있는 상담 기관을 안내해 드립니다.\n\n"
                        "• **보건복지상담센터**: 129\n"
                        "• **정신건강 상담전화**: 1577-0199\n"
                        "• **자살예방 상담전화**: 1393"
                    ),
                    "parsed_data": None,
                    "is_crisis": True
                }

            if result_data.get("is_harmful"):
                return {
                    "reply": "🚫 **상담이 제한된 요청입니다.**\n타인에게 피해를 주거나 법적/윤리적으로 문제가 되는 내용은 상담을 제공하지 않습니다.",
                    "parsed_data": None,
                    "is_crisis": False
                }

            if result_data.get("is_general_chat"):
                return {
                    "reply": result_data.get("reply", "PickMe AI는 중요한 선택과 고민을 돕는 서비스입니다. 구체적인 고민을 말씀해 주세요!"),
                    "parsed_data": None,
                    "is_crisis": False
                }

            return {
                "reply": result_data.get("reply", "상담 내용이 정리되었습니다."),
                "parsed_data": result_data.get("parsed_data"),
                "is_crisis": False
            }

        except Exception as e:
            print(f"Gemini API Quota/Error (Auto Fallback Active): {e}")
            # 쿼터 초과(429)나 기타 에러 발생 시 자동으로 스마트 폴백 실행
            return ChatService._get_smart_fallback(message, tone)

    @staticmethod
    def _get_smart_fallback(message, tone):
        """API 호출 불가 시(쿼터 초과 등) 문맥을 대략적으로 파악해 처리하는 안전 폴백"""
        msg = message.strip().lower()

        # 간단한 잡담/인사 판별
        chat_keywords = ["안녕", "반가워", "날씨", "너 누구", "너 뭐야", "테스트", "test", "하이", "헬로"]
        if any(kw in msg for kw in chat_keywords) or len(msg) < 4:
            return {
                "reply": "PickMe AI는 여러분의 **중요한 선택과 고민**을 분석하고 해결책을 돕는 의사결정 지원 서비스입니다. 현재 겪고 계신 고민이나 비교해야 할 선택지를 구체적으로 말씀해 주세요!",
                "parsed_data": None,
                "is_crisis": False
            }

        # 유해 키워드 판별
        harmful_keywords = ["죽여", "복수", "불법", "사기", "마약", "도박"]
        if any(kw in msg for kw in harmful_keywords):
            return {
                "reply": "🚫 **상담이 제한된 요청입니다.** 타인에게 피해를 주는 내용은 상담을 제공하지 않습니다.",
                "parsed_data": None,
                "is_crisis": False
            }

        # 정상적인 고민인 경우 결정 도우미 데이터 생성
        prefix = "많이 고민되셨겠어요. 함께 고민해 드릴게요. ☕\n" if tone == "empathy" else "요청하신 사안에 대한 분석 결과입니다.\n"
        
        response_body = (
            f"말씀해주신 '{message}'에 대해 검토해 보았습니다.\n"
            "• 선택지 1: 적극적인 도전 및 실행\n"
            "• 선택지 2: 신중한 검토 및 현상 유지\n"
            "아래 버튼을 눌러 결정 도우미에서 더 자세히 비교해 보세요!"
        )

        parsed_data = {
            "title": f"고민: {message[:12]}...",
            "category": "일반 고민",
            "options": ["적극적 실행", "신중한 검토"]
        }

        return {
            "reply": prefix + response_body,
            "parsed_data": parsed_data,
            "is_crisis": False
        }
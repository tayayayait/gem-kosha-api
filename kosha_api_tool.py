import requests
import json
from urllib.parse import urlencode

def search_safety_laws(search_keyword: str, category: str = "0") -> str:
    """
    안전보건공단 안전보건법령 스마트검색 API를 호출하여 결과를 반환하는 함수입니다.
    Gem이 이 함수를 '도구'로 사용하게 됩니다.

    Args:
        search_keyword (str): 검색할 키워드 (예: '사다리', '추락').
        category (str): 검색 항목 코드 (기본값: '0' - 전체).
                         가이드 문서에 따라 '1': 법, '6': 미디어, '7': KOSHA GUIDE 등으로 지정 가능합니다.

    Returns:
        str: 검색 결과를 보기 쉽게 정리한 문자열입니다. 오류 발생 시 오류 메시지를 반환합니다.
    """
    # ==============================================================================
    # TODO: 공공데이터포털에서 발급받은 '본인의' 일반 인증키(URL Encode)를 입력하세요.
    # 아래는 예시 키이며, 실제로 작동하지 않습니다.
    service_key = "Tm9U4A4bvXGp8V3BL5wMFSc3vKZqECQ95p6DaEcNh9Hm00HIe0wpxkz3f11Vsgvx8sB6sCN6sg7izcBesPFP3Q=="
    # ==============================================================================

    # API 요청을 위한 기본 URL과 파라미터 설정 (가이드 문서 기반)
    endpoint = "http://apis.data.go.kr/B552468/srch/smartSearch" [cite: 3]
    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '5',  # 결과는 5개만 가져오도록 설정 (필요시 조절) 
        'searchValue': search_keyword, # 사용자가 입력한 검색어 
        'category': category # 검색할 카테고리 
    }

    # API 요청 URL 생성
    request_url = f"{endpoint}?{urlencode(params)}"
    
    print(f"Requesting URL: {request_url}") # Gem이 코드를 실행할 때 확인용으로 로그를 남깁니다.

    try:
        # API 요청 보내기
        response = requests.get(request_url, timeout=10)
        
        # HTTP 에러가 발생하면 예외 처리
        response.raise_for_status()

        # 응답 데이터를 JSON으로 파싱
        data = response.json()

        # API 응답 헤더에서 결과 코드 확인 (가이드 문서 기반) 
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            return f"API 호출 오류: {header.get('resultMsg')} (코드: {header.get('resultCode')})"

        # 결과 데이터 추출
        body = data.get("response", {}).get("body", {})
        items = body.get("items", {}).get("item", []) [cite: 13, 18]
        total_count = body.get("totalCount", 0) [cite: 13]

        if not items:
            return f"'{search_keyword}'에 대한 검색 결과가 없습니다."

        # 최종 결과를 보기 좋은 문자열로 가공
        result_text = f"✅ '{search_keyword}'에 대한 안전보건법령 검색 결과 (총 {total_count}건 중 상위 5건)\n\n"
        for i, item in enumerate(items):
            # <em> 태그를 굵은 글씨(**)로 바꿔서 가독성을 높입니다.
            title = item.get('title', '제목 없음').replace("<em class='smart'>", "**").replace("</em>", "**") [cite: 21]
            content = item.get('highlight_content', '내용 없음').replace("<em class='smart'>", "**").replace("</em>", "**") [cite: 21]
            link = item.get('filepath', '링크 없음') [cite: 21]
            
            result_text += f"📄 **{i+1}. {title}**\n"
            result_text += f"   - 내용: {content}\n"
            result_text += f"   - 원문 링크: {link}\n\n"

        return result_text

    except requests.exceptions.RequestException as e:
        # 네트워크 또는 HTTP 오류 처리
        return f"네트워크 요청 중 오류가 발생했습니다: {e}"
    except json.JSONDecodeError:
        # JSON 파싱 오류 처리
        return f"API 응답을 처리하는 데 실패했습니다. 서버 응답: {response.text}"
    except Exception as e:
        return f"알 수 없는 오류가 발생했습니다: {e}"

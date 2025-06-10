import os
import requests
import json
from urllib.parse import urlencode
import time

# --- 기존 함수 (단일 카테고리 또는 전체 검색용) ---
def search_safety_laws(search_keyword: str, category: int = 0) -> str:
    # ... (이전과 동일한 코드가 여기에 위치합니다) ...
    # (이 함수는 그대로 두어 단일/전체 검색이 필요할 때 사용합니다)
    """KOSHA 안전보건 스마트검색 프록시 API를 호출하여 산업안전보건 관련 자료를 검색합니다."""
    service_key = os.getenv('KOSHA_API_KEY')
    if not service_key:
        return "API 호출 오류: 서비스 키가 설정되지 않았습니다."

    endpoint = "https://kosha-proxy.vercel.app/api/proxy"
    params = {
        'serviceKey': service_key, 'searchValue': search_keyword, 'category': category,
        'numOfRows': 7, 'maxPage': 5, 'lightMode': True, 'dedup': True, 'onError': 'fallback'
    }

    # ... (이하 모든 코드는 이전 답변과 동일) ...
    # (413 에러 처리 및 재시도 로직 포함)
    for attempt in range(3):
        try:
            # ... (API 호출 및 결과 처리) ...
            request_url = f"{endpoint}?{urlencode(params, doseq=True)}"
            response = requests.get(request_url, timeout=20)
            if response.status_code == 413:
                params['numOfRows'] -= 1
                params['maxPage'] -= 1
                if params['numOfRows'] < 1 or params['maxPage'] < 1: return "API 오류: 응답 용량 초과"
                time.sleep(1)
                continue
            response.raise_for_status()
            data = response.json()
            # ... (결과 파싱 및 텍스트 반환) ...
            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00": return f"API 오류: {header.get('resultMsg')}"
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if not items: return f"'{search_keyword}'(카테고리:{category}) 검색 결과 없음."
            # ... (결과 포맷팅) ...
            return "결과..." # 실제로는 포맷팅된 텍스트
        except Exception as e:
            return f"오류 발생: {e}"
    return "API 호출 실패."


# --- 새로 추가된 함수 (주요 법규 동시 검색용) ---
def search_main_laws(search_keyword: str) -> str:
    """
    사용자가 원하는 핵심 법규들(산업안전보건법, 시행령, 관련 규칙)에 대해
    순차적으로 검색을 실행하고 모든 결과를 종합하여 반환합니다.

    Args:
        search_keyword (str): '추락', '보호구' 등 검색할 키워드.

    Returns:
        str: 여러 법규에서 찾은 결과를 종합하여 정리한 문자열.
    """
    # 1. 검색할 카테고리 코드 목록 정의 
    target_categories = {
        1: "산업안전보건법",
        2: "산업안전보건법 시행령",
        4: "산업안전보건 기준에 관한 규칙"
    }
    
    all_results = []
    seen_doc_ids = set() # 문서 ID를 기준으로 전체 중복을 제거하기 위한 집합

    print(f"'{search_keyword}'에 대한 주요 법규 검색을 시작합니다 (대상: {list(target_categories.values())})")

    # 2. 정의된 각 카테고리에 대해 순차적으로 API 호출
    for code, name in target_categories.items():
        print(f"'{name}'(코드:{code}) 에서 검색 중...")
        
        # 기존에 만든 단일 검색 함수를 재활용하여 호출
        single_result_str = search_safety_laws(search_keyword, category=code)
        
        # search_safety_laws 함수가 실제로는 JSON 문자열을 반환한다고 가정하고 파싱
        # (실제로는 search_safety_laws가 JSON 객체를 반환하도록 수정하거나, 아래처럼 문자열에서 데이터를 추출해야 함)
        # 여기서는 간단히, search_safety_laws가 결과 리스트를 반환한다고 가정하고 코드를 작성하겠습니다.
        # (실제 적용을 위해서는 search_safety_laws의 반환 형태 수정이 필요)
        
        # 임시 방편: search_safety_laws가 파싱 가능한 JSON 문자열을 반환한다고 가정
        # 실제로는 search_safety_laws를 수정하여 JSON 객체나 리스트를 직접 반환하게 하는 것이 가장 좋습니다.
        # 아래는 개념 설명을 위한 코드입니다.
        
        # --- 개념 설명용 코드 ---
        # 실제로는 search_safety_laws 함수를 수정하여 item 리스트를 직접 반환받는 것이 좋습니다.
        # 예시: items = search_safety_laws(..., return_type='json')
        # 여기서는 search_safety_laws가 있다고 가정하고 로직을 설명합니다.
        
        # search_safety_laws를 호출하여 결과 'items' 리스트를 직접 얻는다고 가정
        items = _get_items_from_api(search_keyword, code) # 내부 헬퍼 함수를 호출한다고 가정

        if items:
            for item in items:
                doc_id = item.get("doc_id")
                if doc_id and doc_id not in seen_doc_ids:
                    all_results.append(item)
                    seen_doc_ids.add(doc_id)
    
    # 3. 종합된 결과가 없는 경우
    if not all_results:
        return f"'{search_keyword}'에 대한 주요 법규(법, 시행령, 규칙)에서 검색된 내용이 없습니다."

    # 4. 모든 결과를 종합하여 최종 문자열 생성
    final_text = f"✅ '{search_keyword}'에 대한 주요 법규 종합 검색 결과 (총 {len(all_results)}건)\n\n"
    for i, item in enumerate(all_results):
        title = item.get('title', '제목 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        content = item.get('highlight_content', '내용 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        link = item.get('filepath', '링크 없음')
        
        final_text += f"📄 **{i+1}. {title}**\n"
        final_text += f"   - 내용: {content}\n"
        final_text += f"   - 원문 링크: {link}\n\n"

    return final_text

# search_main_laws를 위한 내부 헬퍼 함수 (실제로는 search_safety_laws를 수정하는 것을 권장)
def _get_items_from_api(search_keyword: str, category: int) -> list:
    """API를 호출하고 결과에서 'items' 리스트만 추출하여 반환하는 내부 함수"""
    service_key = os.getenv('KOSHA_API_KEY')
    if not service_key: return []
    endpoint = "https://kosha-proxy.vercel.app/api/proxy"
    params = {'serviceKey': service_key, 'searchValue': search_keyword, 'category': category, 'numOfRows': 7, 'maxPage': 5, 'lightMode': True, 'dedup': True, 'onError': 'fallback'}
    
    try:
        response = requests.get(f"{endpoint}?{urlencode(params, doseq=True)}", timeout=20)
        response.raise_for_status()
        data = response.json()
        if data.get("response", {}).get("header", {}).get("resultCode") == "00":
            return data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    except Exception:
        return []
    return []

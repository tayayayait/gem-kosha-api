import os
import requests
import json
import time
from urllib.parse import urlencode
from typing import List, Dict, Any

# --- 1. [핵심 수정] API 호출을 전담하는 내부 함수 ---
def _fetch_law_items(search_keyword: str, category: int) -> List[Dict[str, Any]]:
    """
    KOSHA API를 호출하여 순수한 결과 데이터('items' 리스트)를 반환합니다.
    API 호출, 에러 처리, 재시도 로직을 모두 이 함수에서 전담합니다.
    """
    service_key = os.getenv('KOSHA_API_KEY', "Tm9U4A4bvXGp8V3BL5wMFSc3vKZqECQ95p6DaEcNh9Hm00HIe0wpxkz3f11Vsgvx8sB6sCN6sg7izcBesPFP3Q==")
    if not service_key:
        print("API 호출 오류: 서비스 키가 설정되지 않았습니다.")
        return []

    # [수정 1] 접속 주소를 공식 API 명세에 맞게 변경
    endpoint = "https://apis.data.go.kr/B552468/srch/smartSearch"

    # [수정 2] 요청 파라미터를 공식 API 명세에 맞게 수정
    # - 불필요한 파라미터(maxPage, lightMode, dedup, onError) 제거
    # - 필수 파라미터 'pageNo' 추가
    params = {
        'serviceKey': service_key,
        'searchValue': search_keyword,
        'category': category,
        'numOfRows': 10, # 공식 가이드 예시에 맞춰 10으로 설정 
        'pageNo': 1,     # 필수 값이므로 기본값 1로 설정 
    }

    # [수정 3] 프록시 서버에 특화된 413 에러 처리 로직을 일반적인 요청 재시도로 변경
    for attempt in range(3):
        try:
            request_url = f"{endpoint}?{urlencode(params, doseq=True)}"
            response = requests.get(request_url, timeout=20)

            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()

            # 공공데이터 포털의 에러 응답 형식 확인 (OpenAPI_ServiceResponse)
            if data.get("OpenAPI_ServiceResponse"):
                header = data.get("OpenAPI_ServiceResponse", {}).get("cmmMsgHeader", {})
                if header.get("returnReasonCode") != "00":
                    print(f"API 오류: {header.get('returnAuthMsg')} (코드: {header.get('returnReasonCode')})")
                    return[]

            # 제공기관의 에러 응답 형식 확인 (response)
            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00":
                print(f"API 오류: {header.get('resultMsg')} (코드: {header.get('resultCode')})")
                return []
            
            # 정상 응답 처리
            return data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        except requests.exceptions.RequestException as e:
            print(f"네트워크 요청 오류 발생 (시도 {attempt + 1}/3): {e}")
            time.sleep(1) # 재시도 전 1초 대기
        except json.JSONDecodeError:
            print(f"API 응답 JSON 파싱 오류. 응답: {response.text}")
            return []
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")
            return []
            
    print("API 호출 최종 실패.")
    return []

# --- 2. [수정 없음] 단일 카테고리 검색 및 결과 포맷팅 함수 ---
def search_safety_laws(search_keyword: str, category: int = 0) -> str:
    """
    지정된 단일 카테고리에서 법규를 검색하고, 결과를 사람이 읽기 좋은 문자열로 반환합니다.
    """
    print(f"'{search_keyword}'에 대한 단일 검색을 시작합니다 (카테고리: {category})...")
    items = _fetch_law_items(search_keyword, category)

    if not items:
        return f"'{search_keyword}'에 대한 검색 결과가 없습니다 (카테고리: {category})."

    total_count = len(items)
    result_text = f"✅ '{search_keyword}' 검색 결과 (카테고리: {category}, 총 {total_count}건)\n\n"
    for i, item in enumerate(items):
        title = item.get('title', '제목 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        content = item.get('highlight_content', '내용 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        link = item.get('filepath', '링크 없음')
        
        result_text += f"📄 **{i+1}. {title}**\n"
        result_text += f"   - 내용: {content}\n"
        result_text += f"   - 원문 링크: {link}\n\n"

    return result_text

# --- 3. [수정 없음] 주요 법규 동시 검색 및 결과 종합 함수 ---
def search_main_laws(search_keyword: str) -> str:
    """
    주요 법규(법, 시행령, 규칙)에 대해 순차적으로 검색하고 모든 결과를 종합하여 반환합니다.
    """
    target_categories = {
        1: "산업안전보건법",
        2: "산업안전보건법 시행령",
        4: "산업안전보건 기준에 관한 규칙"
    }
    
    all_results = []
    seen_doc_ids = set()

    print(f"'{search_keyword}'에 대한 주요 법규 종합 검색을 시작합니다...")

    for code, name in target_categories.items():
        print(f"-> '{name}'(코드:{code}) 에서 검색 중...")
        items = _fetch_law_items(search_keyword, category=code)
        
        if not items:
            continue

        for item in items:
            doc_id = item.get("doc_id")
            if not doc_id or doc_id in seen_doc_ids:
                continue
            
            all_results.append(item)
            seen_doc_ids.add(doc_id)
    
    if not all_results:
        return f"'{search_keyword}'에 대한 주요 법규(법, 시행령, 규칙)에서 검색된 내용이 없습니다."

    total_count = len(all_results)
    final_text = f"✅ '{search_keyword}'에 대한 주요 법규 종합 검색 결과 (총 {total_count}건)\n\n"
    for i, item in enumerate(all_results):
        title = item.get('title', '제목 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        content = item.get('highlight_content', '내용 없음').replace("<em class='smart'>", "**").replace("</em>", "**")
        link = item.get('filepath', '링크 없음')
        
        final_text += f"📄 **{i+1}. {title}**\n"
        final_text += f"   - 내용: {content}\n"
        final_text += f"   - 원문 링크: {link}\n\n"

    return final_text

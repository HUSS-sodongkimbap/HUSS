# youth_policy_server.py — 청소년정책 MCP 서버
import os
import ssl
from typing import Any, Dict, Optional, Tuple, Iterable

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("youth-policy-mcp")

# 청소년정책 API
BASE_URL = (os.getenv("YOUTH_BASE_URL") or "https://www.youthcenter.go.kr/go/ythip/getPlcy").rstrip("/")
API_KEY = (os.getenv("YOUTH_API_KEY") or "55930c52-9e2e-42ba-9aec-f562fc10cd09").strip()

def _client_candidates() -> Iterable[Tuple[str, httpx.Client]]:
    """TLS/SSL 환경에 따라 순차적으로 시도할 httpx.Client 후보들."""
    # 1) 기본값
    yield "default", httpx.Client(http2=False, timeout=20, trust_env=True)

    # 2) TLS 1.2 이상 + 낮은 보안 레벨
    try:
        tls = ssl.create_default_context()
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            tls.set_ciphers("DEFAULT:@SECLEVEL=1")
        except Exception:
            pass
        yield "tls12_seclevel1", httpx.Client(verify=tls, http2=False, timeout=20, trust_env=True)
    except Exception:
        pass

    # 3) 최후 수단: 인증서 검증 비활성화
    yield "insecure", httpx.Client(verify=False, http2=False, timeout=20, trust_env=True)


def _try_get(url: str, params: Dict[str, Any]):
    """위의 후보 클라이언트들을 순서대로 시도. 성공하면 (mode, response) 반환."""
    last_err: Optional[Exception] = None
    for mode, client in _client_candidates():
        try:
            with client as c:
                resp = c.get(url, params=params)
                return mode, resp
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("No HTTP client candidates available")


def call_youth_api(
    page_num: int = 1,
    page_size: int = 10,
    page_type: str = "1",  # 1:목록, 2:상세
    return_type: str = "json",
    filters: Optional[Dict[str, Any]] = None,
):
    """청소년정책 API 호출"""
    if not API_KEY:
        return {
            "status": "error",
            "message": "YOUTH_API_KEY is missing in .env",
            "request_url": BASE_URL,
        }

    params: Dict[str, Any] = {
        "apiKeyNm": API_KEY,
        "pageNum": page_num,
        "pageSize": page_size,
        "pageType": page_type,
        "rtnType": return_type,
    }
    
    if filters:
        params.update(filters)

    try:
        mode, resp = _try_get(BASE_URL, params)
        req_url = str(resp.request.url)
        status_code = resp.status_code
        resp.raise_for_status()
        
        try:
            json_data = resp.json()
            
            # 응답 데이터 정규화 (항상 policies와 total_count 추가)
            result_section = json_data.get("result", {})
            policies = result_section.get("youthPolicyList", [])
            pagging_info = result_section.get("pagging", {})
            total_count = pagging_info.get("totCount", 0)
            
            # API 응답 구조에 맞게 데이터 정규화
            response = {
                "status": "ok",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "data": json_data,
                "policies": policies,
                "total_count": total_count,
                "page_info": pagging_info
            }
            
            # API 오류 체크
            if json_data.get("resultCode") != 200:
                response["api_error"] = json_data.get('resultMessage', 'Unknown API error')
            
            return response
            
        except Exception as parse_error:
            return {
                "status": "error",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "text": resp.text,
                "parse_error": str(parse_error)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_url": BASE_URL,
        }


@mcp.tool()
def searchYouthPolicies(
    pageNum: int = 1,
    pageSize: int = 10,
    policyKeyword: Optional[str] = None,
    policyName: Optional[str] = None,
    regionCode: Optional[str] = None,  # 법정시군구코드 (5자리)
    largeCategoryName: Optional[str] = None,  # 정책대분류명
    middleCategoryName: Optional[str] = None,  # 정책중분류명
    policyExplanation: Optional[str] = None,  # 정책설명
    **kwargs
):
    """
    청소년정책 검색
    - pageNum, pageSize: 페이징
    - policyKeyword: 정책키워드명 (콤마로 구분)
    - policyName: 정책명
    - regionCode: 법정시군구코드 5자리 (예: 11000)
    - largeCategoryName: 정책대분류명 (콤마로 구분)
    - middleCategoryName: 정책중분류명 (콤마로 구분)
    - policyExplanation: 정책설명
    """
    filters = {}
    
    if policyKeyword:
        filters["plcyKywdNm"] = policyKeyword
    if policyName:
        filters["plcyNm"] = policyName
    if regionCode:
        filters["zipCd"] = regionCode
    if largeCategoryName:
        filters["lclsfNm"] = largeCategoryName
    if middleCategoryName:
        filters["mclsfNm"] = middleCategoryName
    if policyExplanation:
        filters["plcyExplnCn"] = policyExplanation
    
    # 추가 kwargs 필터
    for key, value in kwargs.items():
        if value is not None:
            filters[key] = value
    
    return call_youth_api(
        page_num=pageNum,
        page_size=pageSize,
        page_type="1",  # 목록
        return_type="json",
        filters=filters
    )


@mcp.tool()
def getYouthPolicyDetail(
    policyNumber: str,
    **kwargs
):
    """
    청소년정책 상세 조회
    - policyNumber: 정책번호 (필수)
    """
    filters = {"plcyNo": policyNumber}
    
    # 추가 kwargs 필터
    for key, value in kwargs.items():
        if value is not None:
            filters[key] = value
    
    return call_youth_api(
        page_num=1,
        page_size=1,
        page_type="2",  # 상세
        return_type="json",
        filters=filters
    )


@mcp.tool()
def searchPoliciesByRegion(
    regionCode: str,
    pageNum: int = 1,
    pageSize: int = 20,
    categories: Optional[str] = None,  # 대분류명들 (콤마로 구분)
    **kwargs
):
    """
    지역별 청소년정책 검색
    - regionCode: 법정시군구코드 5자리 (예: 11110 - 종로구)
    - categories: 관심 분야 (예: "일자리,주거,교육")
    """
    filters = {"zipCd": regionCode}
    
    if categories:
        filters["lclsfNm"] = categories
    
    # 추가 kwargs 필터
    for key, value in kwargs.items():
        if value is not None:
            filters[key] = value
    
    return call_youth_api(
        page_num=pageNum,
        page_size=pageSize,
        filters=filters
    )


@mcp.tool()
def searchPoliciesByKeywords(
    keywords: str,  # 콤마로 구분된 키워드들
    pageNum: int = 1,
    pageSize: int = 20,
    regionCode: Optional[str] = None,
    **kwargs
):
    """
    키워드 기반 청소년정책 검색
    - keywords: 검색 키워드들 (콤마로 구분, 예: "취업,창업,주거지원")
    - regionCode: 선택적 지역 필터
    """
    filters = {"plcyKywdNm": keywords}
    
    if regionCode:
        filters["zipCd"] = regionCode
    
    # 추가 kwargs 필터
    for key, value in kwargs.items():
        if value is not None:
            filters[key] = value
    
    return call_youth_api(
        page_num=pageNum,
        page_size=pageSize,
        filters=filters
    )


@mcp.tool()
def ping():
    """헬스체크"""
    return {"status": "ok", "message": "youth policy server pong"}


def main():
    try:
        names = [t.name for t in mcp._tools]
        print("[YOUTH POLICY SERVER] tools:", names, flush=True)
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()
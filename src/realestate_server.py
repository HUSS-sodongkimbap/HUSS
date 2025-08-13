# realestate_server.py — 부동산 실거래가 MCP 서버
import os
import ssl
from typing import Any, Dict, Optional, Tuple, Iterable

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("realestate-mcp")

# 국토교통부 부동산 실거래가 API
BASE_URL = (os.getenv("MOLIT_BASE_URL") or "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade").rstrip("/")
API_KEY = (os.getenv("MOLIT_API_KEY") or "").strip()

def _client_candidates() -> Iterable[Tuple[str, httpx.Client]]:
    """
    TLS/SSL 환경에 따라 순차적으로 시도할 httpx.Client 후보들.
    """
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
    """
    위의 후보 클라이언트들을 순서대로 시도. 성공하면 (mode, response) 반환.
    """
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


def call_molit_api(
    endpoint: str = "getRTMSDataSvcAptTrade",
    lawdcd: str = "",  # 법정동코드 (LAWD_CD)
    deal_ymd: str = "",  # 계약년월 (DEAL_YMD)
    page_no: int = 1,
    num_rows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    if not API_KEY:
        return {
            "status": "error",
            "message": "MOLIT_API_KEY is missing in .env",
            "request_url": f"{BASE_URL}/{endpoint}",
        }

    url = f"{BASE_URL}/{endpoint}" if endpoint else BASE_URL
    params: Dict[str, Any] = {
        "serviceKey": API_KEY,
        "pageNo": page_no,
        "numOfRows": num_rows,
        "LAWD_CD": lawdcd,
        "DEAL_YMD": deal_ymd,
    }
    if filters:
        params.update(filters)

    try:
        mode, resp = _try_get(url, params)
        req_url = str(resp.request.url)
        status_code = resp.status_code
        resp.raise_for_status()
        try:
            return {
                "status": "ok",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "data": resp.json(),
            }
        except Exception:
            return {
                "status": "ok",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "text": resp.text,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_url": url,
        }


@mcp.tool()
def getApartmentTrades(
    lawdcd: str,
    deal_ymd: str,
    pageNo: int = 1,
    numOfRows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    아파트 실거래가 조회
    - lawdcd: 법정동코드 5자리 (예: 11110)
    - deal_ymd: 계약년월 YYYYMM (예: 202506)
    - pageNo, numOfRows: 페이지/행 수
    - filters: 추가 필터 파라미터
    """
    return call_molit_api(
        endpoint="getRTMSDataSvcAptTrade",
        lawdcd=lawdcd,
        deal_ymd=deal_ymd,
        page_no=pageNo,
        num_rows=numOfRows,
        filters=filters
    )


@mcp.tool()
def getOfficeTrades(
    lawdcd: str,
    deal_ymd: str,
    pageNo: int = 1,
    numOfRows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    오피스텔 실거래가 조회
    - lawdcd: 법정동코드 5자리
    - deal_ymd: 계약년월 YYYYMM
    """
    return call_molit_api(
        endpoint="OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcOffiTrade",
        lawdcd=lawdcd,
        deal_ymd=deal_ymd,
        page_no=pageNo,
        num_rows=numOfRows,
        filters=filters
    )


@mcp.tool()
def getHouseTrades(
    lawdcd: str,
    deal_ymd: str,
    pageNo: int = 1,
    numOfRows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    단독/다가구 실거래가 조회
    - lawdcd: 법정동코드 5자리
    - deal_ymd: 계약년월 YYYYMM
    """
    return call_molit_api(
        endpoint="OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcSHRent",
        lawdcd=lawdcd,
        deal_ymd=deal_ymd,
        page_no=pageNo,
        num_rows=numOfRows,
        filters=filters
    )


@mcp.tool()
def ping():
    """헬스체크"""
    return {"status": "ok", "message": "realestate server pong"}


def main():
    try:
        names = [t.name for t in mcp._tools]
        print("[REALESTATE SERVER] tools:", names, flush=True)
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()
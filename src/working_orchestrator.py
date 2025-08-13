# working_orchestrator.py — 작동하는 간단한 오케스트레이터
import asyncio
import json
from typing import Dict, Any, Optional

# 서버 모듈 직접 import
import server
import realestate_server


class SimpleOrchestrator:
    """MCP 서버들을 직접 함수 호출로 연동하는 간단한 오케스트레이터"""
    
    def __init__(self):
        self.recruitment_server = server
        self.realestate_server = realestate_server
    
    def get_available_tools(self) -> Dict[str, list]:
        """사용 가능한 모든 도구 목록"""
        return {
            'recruitment': [
                {'name': 'listRecruitments', 'description': '공공기관 채용정보 목록 조회'},
                {'name': 'getRecruitmentDetail', 'description': '채용정보 상세 조회'},
                {'name': 'ping', 'description': '헬스체크'}
            ],
            'realestate': [
                {'name': 'getApartmentTrades', 'description': '아파트 실거래가 조회'},
                {'name': 'getOfficeTrades', 'description': '오피스텔 실거래가 조회'},
                {'name': 'getHouseTrades', 'description': '단독/다가구 실거래가 조회'},
                {'name': 'ping', 'description': '헬스체크'}
            ]
        }
    
    def call_recruitment_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """채용정보 서버 도구 호출"""
        try:
            if tool_name == 'listRecruitments':
                return {
                    "status": "success",
                    "server": "recruitment",
                    "tool": tool_name,
                    "result": self.recruitment_server.listRecruitments(**arguments)
                }
            elif tool_name == 'getRecruitmentDetail':
                return {
                    "status": "success", 
                    "server": "recruitment",
                    "tool": tool_name,
                    "result": self.recruitment_server.getRecruitmentDetail(**arguments)
                }
            elif tool_name == 'ping':
                return {
                    "status": "success",
                    "server": "recruitment", 
                    "tool": tool_name,
                    "result": self.recruitment_server.ping()
                }
            else:
                return {
                    "status": "error",
                    "server": "recruitment",
                    "tool": tool_name,
                    "message": f"알 수 없는 도구: {tool_name}"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": "recruitment",
                "tool": tool_name,
                "message": str(e)
            }
    
    def call_realestate_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """부동산 서버 도구 호출"""
        try:
            if tool_name == 'getApartmentTrades':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name,
                    "result": self.realestate_server.getApartmentTrades(**arguments)
                }
            elif tool_name == 'getOfficeTrades':
                return {
                    "status": "success",
                    "server": "realestate", 
                    "tool": tool_name,
                    "result": self.realestate_server.getOfficeTrades(**arguments)
                }
            elif tool_name == 'getHouseTrades':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name, 
                    "result": self.realestate_server.getHouseTrades(**arguments)
                }
            elif tool_name == 'ping':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name,
                    "result": self.realestate_server.ping()
                }
            else:
                return {
                    "status": "error",
                    "server": "realestate",
                    "tool": tool_name,
                    "message": f"알 수 없는 도구: {tool_name}"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": "realestate",
                "tool": tool_name,
                "message": str(e)
            }
    
    def comprehensive_region_search(self, region_code: str, deal_ymd: str = "202506"):
        """지역 통합 검색 - 채용정보 + 부동산 정보"""
        print(f"🔍 지역 통합 검색 시작: {region_code}")
        
        results = {}
        
        # 1. 채용정보 조회
        print("  📋 채용정보 조회 중...")
        recruitment_result = self.call_recruitment_tool(
            'listRecruitments',
            {'pageNo': 1, 'numOfRows': 5}
        )
        results['recruitment'] = recruitment_result
        
        # 2. 부동산 아파트 실거래가 조회
        print("  🏠 아파트 실거래가 조회 중...")
        apt_result = self.call_realestate_tool(
            'getApartmentTrades',
            {
                'lawdcd': region_code,
                'deal_ymd': deal_ymd,
                'pageNo': 1,
                'numOfRows': 5
            }
        )
        results['apartment_trades'] = apt_result
        
        # 3. 오피스텔 실거래가 조회 (선택적)
        print("  🏢 오피스텔 실거래가 조회 중...")
        office_result = self.call_realestate_tool(
            'getOfficeTrades',
            {
                'lawdcd': region_code,
                'deal_ymd': deal_ymd,
                'pageNo': 1,
                'numOfRows': 3
            }
        )
        results['office_trades'] = office_result
        
        print("✅ 지역 통합 검색 완료")
        return results


def test_ping():
    """빠른 연결 테스트"""
    print("🏓 Ping 테스트...")
    orchestrator = SimpleOrchestrator()
    
    # 채용정보 서버 ping
    result1 = orchestrator.call_recruitment_tool('ping', {})
    if result1['status'] == 'success':
        print("  ✅ 채용정보 서버: 연결됨")
    else:
        print(f"  ❌ 채용정보 서버: {result1['message']}")
    
    # 부동산 서버 ping
    result2 = orchestrator.call_realestate_tool('ping', {})
    if result2['status'] == 'success':
        print("  ✅ 부동산 서버: 연결됨")
    else:
        print(f"  ❌ 부동산 서버: {result2['message']}")
    
    return result1['status'] == 'success' and result2['status'] == 'success'


def main():
    print("=" * 60)
    print("🚀 간단한 MCP 오케스트레이터 테스트")
    print("=" * 60)
    
    # 1. Ping 테스트
    if not test_ping():
        print("❌ 서버 연결 실패. 프로그램 종료.")
        return
    
    # 2. 사용 가능한 도구 목록
    orchestrator = SimpleOrchestrator()
    tools = orchestrator.get_available_tools()
    
    print("\n📋 사용 가능한 도구들:")
    for server_name, server_tools in tools.items():
        print(f"\n🔧 {server_name} 서버:")
        for tool in server_tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    # 3. 통합 검색 테스트
    print("\n" + "=" * 50)
    print("🚀 종로구 통합 검색 테스트")
    print("=" * 50)
    
    results = orchestrator.comprehensive_region_search(
        region_code="11110",  # 종로구 법정동코드
        deal_ymd="202506"     # 2025년 6월
    )
    
    # 4. 결과 출력
    print("\n📊 검색 결과:")
    for category, result in results.items():
        print(f"\n🔹 {category}:")
        if result['status'] == 'success':
            print(f"  ✅ 성공")
            
            # 결과 데이터 분석
            result_data = result['result']
            
            if isinstance(result_data, dict):
                if result_data.get('status') == 'ok':
                    data = result_data.get('data', {})
                    if isinstance(data, dict) and 'response' in data:
                        body = data['response'].get('body', {})
                        if 'items' in body:
                            items = body['items']
                            if isinstance(items, dict) and 'item' in items:
                                item_list = items['item']
                                if isinstance(item_list, list):
                                    print(f"  📝 데이터 개수: {len(item_list)}개")
                                    if len(item_list) > 0:
                                        print(f"  📄 첫 번째 항목 키: {list(item_list[0].keys())}")
                                else:
                                    print(f"  📝 단일 데이터 항목")
                        else:
                            print(f"  📝 응답 구조: {list(body.keys()) if isinstance(body, dict) else 'Unknown'}")
                    else:
                        print(f"  📝 데이터 타입: {type(data)}")
                else:
                    print(f"  ⚠️ API 응답: {result_data.get('message', 'Unknown status')}")
            else:
                print(f"  📝 결과 타입: {type(result_data)}")
        else:
            print(f"  ❌ 실패: {result.get('message', 'Unknown error')}")
    
    # 5. 결과 저장
    print(f"\n💾 전체 결과를 working_results.json에 저장합니다...")
    with open('working_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 테스트 완료! 🎉")


if __name__ == "__main__":
    main()
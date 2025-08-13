# simple_test.py — 간단한 MCP 서버 테스트
import asyncio
import sys

async def test_server_import():
    """서버 파일들이 정상적으로 import되는지 테스트"""
    print("📁 서버 파일 import 테스트...")
    
    try:
        print("  - server.py import 중...")
        import server
        print("  ✅ server.py import 성공")
        
        # 서버의 tools 확인
        if hasattr(server, 'mcp') and hasattr(server.mcp, '_tools'):
            tools = [t.name for t in server.mcp._tools]
            print(f"  📋 사용 가능한 도구: {tools}")
        
    except Exception as e:
        print(f"  ❌ server.py import 실패: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("  - realestate_server.py import 중...")
        import realestate_server
        print("  ✅ realestate_server.py import 성공")
        
        # 서버의 tools 확인
        if hasattr(realestate_server, 'mcp') and hasattr(realestate_server.mcp, '_tools'):
            tools = [t.name for t in realestate_server.mcp._tools]
            print(f"  📋 사용 가능한 도구: {tools}")
        
    except Exception as e:
        print(f"  ❌ realestate_server.py import 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_api_keys():
    """API 키 설정 테스트"""
    print("\n🔑 API 키 설정 테스트...")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 채용정보 API 키
    recruitment_key = os.getenv("DATA_GO_KR_KEY")
    if recruitment_key:
        print(f"  ✅ 채용정보 API 키: {recruitment_key[:20]}...")
    else:
        print("  ❌ 채용정보 API 키 없음")
    
    # 부동산 API 키
    realestate_key = os.getenv("MOLIT_API_KEY")
    if realestate_key:
        print(f"  ✅ 부동산 API 키: {realestate_key[:20]}...")
    else:
        print("  ❌ 부동산 API 키 없음")


async def test_api_call():
    """실제 API 호출 테스트"""
    print("\n🌐 API 호출 테스트...")
    
    try:
        # 채용정보 API 직접 호출
        import server
        result = server.call_api(path="list", page_no=1, num_rows=2)
        
        if result['status'] == 'ok':
            print("  ✅ 채용정보 API 호출 성공")
            print(f"  📊 응답 상태: {result.get('status_code')}")
        else:
            print(f"  ❌ 채용정보 API 호출 실패: {result.get('message')}")
            
    except Exception as e:
        print(f"  ❌ 채용정보 API 테스트 실패: {e}")
    
    try:
        # 부동산 API 직접 호출
        import realestate_server
        result = realestate_server.call_molit_api(
            lawdcd="11110",
            deal_ymd="202506",
            page_no=1,
            num_rows=2
        )
        
        if result['status'] == 'ok':
            print("  ✅ 부동산 API 호출 성공")
            print(f"  📊 응답 상태: {result.get('status_code')}")
        else:
            print(f"  ❌ 부동산 API 호출 실패: {result.get('message')}")
            
    except Exception as e:
        print(f"  ❌ 부동산 API 테스트 실패: {e}")


async def main():
    print("=" * 50)
    print("🔍 MCP 서버 진단 테스트")
    print("=" * 50)
    
    await test_server_import()
    await test_api_keys()
    await test_api_call()
    
    print("\n" + "=" * 50)
    print("✅ 진단 테스트 완료")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
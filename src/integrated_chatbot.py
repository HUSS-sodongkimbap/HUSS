# integrated_chatbot.py — 채용+부동산 통합 챗봇
import asyncio
import json
import re
from typing import Dict, Any, List, Optional

# 우리가 만든 working_orchestrator import
from working_orchestrator import SimpleOrchestrator


class IntegratedChatbot:
    def __init__(self):
        self.orchestrator = SimpleOrchestrator()
        self.state = {
            "raw": False,
            "max_results": 10,
            "region_code": "11110",  # 기본: 종로구
            "deal_ymd": "202506",     # 기본: 2025년 6월
            "job_field": None         # 직무 분야 필터
        }
        
        # API 명세서의 정확한 직무 분야 매핑 (추가 키워드 없이)
        self.job_fields = {
            "사업관리": "R600001",
            "경영.회계.사무": "R600002",
            "금융.보험": "R600003",
            "교육.자연.사회과학": "R600004",
            "법률.경찰.소방.교도.국방": "R600005",
            "보건.의료": "R600006",
            "사회복지.종교": "R600007",
            "문화.예술.디자인.방송": "R600008",
            "운전.운송": "R600009",
            "영업판매": "R600010",
            "경비.청소": "R600011",
            "이용.숙박.여행.오락.스포츠": "R600012",
            "음식서비스": "R600013",
            "건설": "R600014",
            "기계": "R600015",
            "재료": "R600016",
            "화학": "R600017",
            "섬유.의복": "R600018",
            "전기.전자": "R600019",
            "정보통신": "R600020",
            "식품가공": "R600021",
            "인쇄.목재.가구.공예": "R600022",
            "환경.에너지.안전": "R600023",
            "농림어업": "R600024",
            "연구": "R600025"
        }
    
    def print_help(self):
        print("""
🤖 통합 챗봇 명령어 가이드

[자연어 검색]
  채용정보 찾아줘                    → 채용정보만 검색
  아파트 실거래가 알려줘             → 부동산 정보만 검색  
  종로구에서 일하고 살 곳 찾아줘      → 채용+부동산 통합 검색
  청년 인턴 모집하는 곳 있어?         → 청년인턴 채용정보 검색
  강남 IT 개발자 채용               → 지역+직무 조합 검색
  
[설정 명령어]
  /region <법정동코드>               → 지역 설정 (예: /region 11680)
  /date <YYYYMM>                    → 부동산 거래 년월 설정
  /jobs <숫자>                      → 채용정보 결과 개수 설정 (예: /jobs 10)
  /field <분야명>                   → 직무 분야 설정 (예: /field it)
  /raw on|off                       → 원문 데이터 보기 토글
  /show                            → 현재 설정 보기
  /help                            → 도움말
  /exit                            → 종료


[지역 코드 참고]
  11110: 종로구    11680: 강남구    11170: 용산구
  11200: 성동구    11215: 광진구    11290: 성북구
  42150: 강릉시    44131: 천안시    44790: 청양군
""".strip())
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 분석해서 의도 파악"""
        text = user_input.lower().replace(" ", "")
        
        intent = {
            "type": "unknown",
            "search_jobs": False,
            "search_realestate": False,
            "filters": {},
            "region_mentioned": None
        }
        
        # 지역 감지
        region_mapping = {
            "종로": "11110", "종로구": "11110",
            "강남": "11680", "강남구": "11680", 
            "용산": "11170", "용산구": "11170",
            "성동": "11200", "성동구": "11200",
            "광진": "11215", "광진구": "11215",
            "천안": "44131", "천안시": "44131",
            "강릉": "42150", "강릉시": "42150",
            "청양": "44790", "청양군": "44790",
        }
        
        for region_name, code in region_mapping.items():
            if region_name in text:
                intent["region_mentioned"] = code
                break
        
        # 검색 유형 감지
        job_keywords = ["채용", "구인", "일자리", "취업", "인턴", "공채", "모집", "구직", "일하", "근무", "직장"]
        realestate_keywords = ["아파트", "부동산", "실거래가", "매매", "집", "주택", "오피스텔"]
        living_keywords = ["살곳", "살", "거주", "이사", "정착", "생활"]
        
        has_job = any(keyword in text for keyword in job_keywords)
        has_realestate = any(keyword in text for keyword in realestate_keywords + living_keywords)
        
        # "살 곳"은 부동산이지만, "일하고 살"은 통합검색으로 처리
        if "일하고" in text and "살" in text:
            intent["type"] = "comprehensive"
            intent["search_jobs"] = True
            intent["search_realestate"] = True
        elif has_job and has_realestate:
            intent["type"] = "comprehensive"
            intent["search_jobs"] = True
            intent["search_realestate"] = True
        elif has_job:
            intent["type"] = "jobs_only"
            intent["search_jobs"] = True
        elif has_realestate:
            intent["type"] = "realestate_only"
            intent["search_realestate"] = True
        elif any(keyword in text for keyword in ["통합", "전체", "모든", "다"]):
            intent["type"] = "comprehensive" 
            intent["search_jobs"] = True
            intent["search_realestate"] = True
        
        # 채용 필터 감지
        if "청년" in text and "인턴" in text:
            intent["filters"]["hireTypeLst"] = "R1050,R1060,R1070"
        elif "정규직" in text:
            intent["filters"]["hireTypeLst"] = "R1010"
        elif "계약직" in text or "비정규" in text:
            intent["filters"]["hireTypeLst"] = "R1040"
        
        if "학력무관" in text:
            intent["filters"]["acbgCondLst"] = "R7010"
        elif "대졸" in text or "4년제" in text:
            intent["filters"]["acbgCondLst"] = "R7050"
        
        # 직무 분야 필터 감지 (정확한 API 분야명만 사용)
        for field_name, code in self.job_fields.items():
            if field_name in text:
                intent["filters"]["ncsCdLst"] = code
                break
        
        return intent
    
    def get_region_name(self, region_code: str) -> str:
        """지역 코드를 지역명으로 변환"""
        code_to_name = {
            "11110": "종로구", "11680": "강남구", "11170": "용산구",
            "11200": "성동구", "11215": "광진구", "44131": "천안시",
            "42150": "강릉시", "44790": "청양군"
        }
        return code_to_name.get(region_code, f"지역코드 {region_code}")
    
    def format_job_results(self, results: List[Dict], limit: int = 5, region_name: str = "") -> str:
        """채용정보 결과를 보기 좋게 포맷"""
        if not results:
            if region_name:
                return f"📋 **{region_name} 지역의 채용정보를 찾을 수 없습니다.**\n\n💡 **제안:**\n- 인근 도시나 도 단위로 검색해보세요\n- 원격근무 가능한 직종을 찾아보세요\n- 지역 중소기업이나 농업 관련 일자리도 고려해보세요"
            return "📋 채용정보를 찾을 수 없습니다."
        
        output = [f"📋 **채용정보** (총 {len(results)}건 중 상위 {min(limit, len(results))}건)\n"]
        
        for i, job in enumerate(results[:limit], 1):
            title = job.get("recrutPbancTtl", "제목 없음")
            company = job.get("instNm", "기관명 없음")
            hire_type = job.get("hireTypeNmLst", "")
            region = job.get("workRgnNmLst", "")
            deadline = job.get("pbancEndYmd", "")
            recruit_count = job.get("recrutNope", "")
            qualification = job.get("aplyQlfcCn", "")
            preference = job.get("prefCondCn", "")
            ncs_field = job.get("ncsCdNmLst", "")
            
            # 날짜 포맷팅
            if deadline and len(deadline) == 8:
                deadline = f"{deadline[:4]}.{deadline[4:6]}.{deadline[6:]}"
            
            output.append(f"{'='*50}")
            output.append(f"📍 **{i}. {company}** ({hire_type})")
            output.append(f"📌 **{title}**")
            output.append("")
            
            # 기본 정보
            if recruit_count:
                output.append(f"👥 **모집인원**: {recruit_count}명")
            if region:
                output.append(f"🌍 **근무지역**: {region}")
            if deadline:
                output.append(f"⏰ **마감일**: {deadline}")
            if ncs_field:
                output.append(f"🔧 **직무분야**: {ncs_field}")
            
            output.append("")
            
            # 자격요건 (간소화해서 표시)
            if qualification:
                qual_short = qualification.replace('\r\n', ' ').replace('\n', ' ')[:200]
                if len(qualification) > 200:
                    qual_short += "..."
                output.append(f"📋 **자격요건**: {qual_short}")
                output.append("")
            
            # 우대사항
            if preference:
                pref_short = preference.replace('\r\n', ' ').replace('\n', ' ')[:100]
                if len(preference) > 100:
                    pref_short += "..."
                output.append(f"⭐ **우대사항**: {pref_short}")
                output.append("")
            
        return "\n".join(output)
    
    def filter_jobs_by_region(self, jobs: List[Dict], target_region_code: str) -> List[Dict]:
        """채용정보를 지역별로 필터링"""
        # 법정동코드 → 지역명 매핑
        region_mapping = {
            "11110": ["종로", "서울"],
            "11680": ["강남", "서울"], 
            "11170": ["용산", "서울"],
            "11200": ["성동", "서울"],
            "11215": ["광진", "서울"],
            "44131": ["천안", "충남"],
            "42150": ["강릉", "강원"],
            "44790": ["청양", "충남", "충청"]
        }
        
        if target_region_code not in region_mapping:
            return jobs  # 매핑 없으면 전체 반환
        
        target_keywords = region_mapping[target_region_code]
        filtered_jobs = []
        
        for job in jobs:
            work_region = job.get("workRgnNmLst", "").replace(" ", "")
            # 지역명이 포함되어 있으면 필터링
            if any(keyword in work_region for keyword in target_keywords):
                filtered_jobs.append(job)
        
        # 필터링된 결과가 없으면 원본 반환 (너무 엄격하지 않게)
        return filtered_jobs if filtered_jobs else jobs
    
    def format_realestate_results(self, apt_data: List[Dict], limit: int = 5) -> str:
        """부동산 결과를 보기 좋게 포맷"""
        if not apt_data:
            return "🏠 부동산 거래 정보를 찾을 수 없습니다."
        
        output = [f"🏠 **아파트 실거래가** (총 {len(apt_data)}건 중 상위 {min(limit, len(apt_data))}건)\n"]
        
        for i, apt in enumerate(apt_data[:limit], 1):
            name = apt.get("aptNm", "아파트명 없음")
            price = apt.get("dealAmount", "가격정보없음")
            area = apt.get("excluUseAr", "면적정보없음")
            floor = apt.get("floor", "층수정보없음")
            year = apt.get("buildYear", "건축년도없음")
            dong = apt.get("umdNm", "동정보없음")
            
            # 가격 포맷팅 (만원 → 억원)
            if price and price.replace(",", "").isdigit():
                price_int = int(price.replace(",", ""))
                if price_int >= 10000:
                    eok = price_int // 10000
                    man = price_int % 10000
                    if man > 0:
                        price_formatted = f"{eok}억 {man:,}만원"
                    else:
                        price_formatted = f"{eok}억원"
                else:
                    price_formatted = f"{price_int:,}만원"
            else:
                price_formatted = price
            
            output.append(f"{i}. **{name}** ({dong})")
            output.append(f"   💰 {price_formatted} | {area}㎡ | {floor}층 | {year}년")
            output.append("")
        
        return "\n".join(output)
    
    async def handle_search(self, intent: Dict[str, Any]) -> str:
        """검색 의도에 따라 적절한 검색 수행"""
        region_code = intent.get("region_mentioned") or self.state["region_code"]
        
        results = []
        
        try:
            if intent["search_jobs"] and intent["search_realestate"]:
                # 통합 검색
                print("🔍 통합 검색 중...")
                # 지역 필터링을 위해 더 많은 데이터 요청
                data = {}
                
                # 채용정보 직접 조회 (더 많은 결과)
                job_result = self.orchestrator.call_recruitment_tool(
                    'listRecruitments',
                    {
                        'pageNo': 1, 
                        'numOfRows': 50,  # 지역 필터링을 위해 많이 가져오기
                        'filters': intent.get("filters")
                    }
                )
                data["recruitment"] = job_result
                
                # 부동산 정보 조회
                apt_result = self.orchestrator.call_realestate_tool(
                    'getApartmentTrades',
                    {
                        'lawdcd': region_code,
                        'deal_ymd': self.state["deal_ymd"],
                        'pageNo': 1,
                        'numOfRows': 10
                    }
                )
                data["apartment_trades"] = apt_result
                
                # 채용정보 포맷팅
                if data["recruitment"]["status"] == "success":
                    recruitment_result = data["recruitment"]["result"]
                    if isinstance(recruitment_result, dict) and "data" in recruitment_result:
                        job_data = recruitment_result["data"].get("result", [])
                        # 지역별 필터링 적용
                        filtered_jobs = self.filter_jobs_by_region(job_data, region_code)
                        results.append(self.format_job_results(filtered_jobs, 3))
                    else:
                        results.append("📋 채용정보를 불러올 수 없습니다.")
                else:
                    results.append(f"📋 채용정보 검색 실패: {data['recruitment'].get('message', '알 수 없는 오류')}")
                
                # 부동산정보 포맷팅  
                if data["apartment_trades"]["status"] == "success":
                    apt_result = data["apartment_trades"]["result"]
                    if isinstance(apt_result, dict) and "text" in apt_result:
                        apt_text = apt_result["text"]
                        apt_data = self.parse_apartment_xml(apt_text)
                        results.append(self.format_realestate_results(apt_data, 3))
                    else:
                        results.append("🏠 부동산 정보를 불러올 수 없습니다.")
                else:
                    results.append(f"🏠 부동산 검색 실패: {data['apartment_trades'].get('message', '알 수 없는 오류')}")
                
            elif intent["search_jobs"]:
                # 채용정보만 검색
                print("📋 채용정보 검색 중...")
                job_result = self.orchestrator.call_recruitment_tool(
                    'listRecruitments',
                    {
                        'pageNo': 1, 
                        'numOfRows': 500,  # 필터링 고려해서 많이 가져오기
                        'filters': {**intent.get("filters", {}), 
                                   **({} if self.state["job_field"] is None else {"ncsCdLst": self.state["job_field"]})}
                    }
                )
                
                if job_result["status"] == "success":
                    job_data = job_result["result"].get("data", {}).get("result", [])
                    # 지역이 지정된 경우 필터링
                    if intent.get("region_mentioned"):
                        job_data = self.filter_jobs_by_region(job_data, intent["region_mentioned"])
                        region_name = self.get_region_name(intent["region_mentioned"])
                        results.append(self.format_job_results(job_data, region_name=region_name))
                    else:
                        results.append(self.format_job_results(job_data))
                
            elif intent["search_realestate"]:
                # 부동산정보만 검색
                print("🏠 부동산 검색 중...")
                apt_result = self.orchestrator.call_realestate_tool(
                    'getApartmentTrades',
                    {
                        'lawdcd': region_code,
                        'deal_ymd': self.state["deal_ymd"],
                        'pageNo': 1,
                        'numOfRows': self.state["max_results"]
                    }
                )
                
                if apt_result["status"] == "success":
                    apt_text = apt_result["result"].get("text", "")
                    apt_data = self.parse_apartment_xml(apt_text)
                    results.append(self.format_realestate_results(apt_data))
        
        except Exception as e:
            return f"❌ 검색 중 오류가 발생했습니다: {str(e)}"
        
        if results:
            return "\n\n".join(results)
        else:
            return "❌ 검색 결과를 찾을 수 없습니다."
    
    def parse_apartment_xml(self, xml_text: str) -> List[Dict]:
        """XML 형태의 아파트 데이터를 파싱"""
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(xml_text)
            items = root.findall('.//item')
            
            apt_list = []
            for item in items:
                apt_data = {}
                for child in item:
                    apt_data[child.tag] = child.text.strip() if child.text else ""
                apt_list.append(apt_data)
            
            return apt_list
        except Exception as e:
            print(f"XML 파싱 오류: {e}")
            return []

    async def run(self):
        """챗봇 메인 실행 루프"""
        print("🤖 인구소멸위기 지역 통합 지원 챗봇이 시작되었습니다!")
        print("채용정보와 부동산 정보를 통합 검색할 수 있습니다.\n")
        
        # 직무 분야 안내
        print("📋 **검색 가능한 직무 분야:**")
        print("=" * 60)
        fields_list = [
            "사업관리", "경영.회계.사무", "금융.보험", "교육.자연.사회과학",
            "법률.경찰.소방.교도.국방", "보건.의료", "사회복지.종교", "문화.예술.디자인.방송",
            "운전.운송", "영업판매", "경비.청소", "이용.숙박.여행.오락.스포츠",
            "음식서비스", "건설", "기계", "재료", "화학", "섬유.의복",
            "전기.전자", "정보통신", "식품가공", "인쇄.목재.가구.공예",
            "환경.에너지.안전", "농림어업", "연구"
        ]
        
        # 4열로 정렬해서 출력
        for i in range(0, len(fields_list), 4):
            row = fields_list[i:i+4]
            print("  ".join(f"{field:<15}" for field in row))
        print("=" * 60)
        print("💡 사용법: '강남 정보통신 일자리', '/field 보건의료' 등\n")
        
        self.print_help()
        
        while True:
            try:
                user_input = input("\n💬 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 챗봇을 종료합니다. 좋은 하루 되세요!")
                break
            
            if not user_input:
                continue
            
            # 명령어 처리
            if user_input.lower() in ["/exit", "exit", "quit", "종료"]:
                print("👋 챗봇을 종료합니다. 좋은 하루 되세요!")
                break
                
            elif user_input.lower() in ["/help", "help", "도움말"]:
                self.print_help()
                continue
                
            elif user_input.lower() == "/show":
                print("📊 현재 설정:")
                print(json.dumps(self.state, indent=2, ensure_ascii=False))
                continue
                
            elif user_input.startswith("/region "):
                region_code = user_input.split(" ", 1)[1].strip()
                self.state["region_code"] = region_code
                print(f"📍 지역이 {region_code}로 설정되었습니다.")
                continue
                
            elif user_input.startswith("/date "):
                date = user_input.split(" ", 1)[1].strip()
                self.state["deal_ymd"] = date
                print(f"📅 거래 년월이 {date}로 설정되었습니다.")
                continue
                
            elif user_input.startswith("/raw "):
                arg = user_input.split(" ", 1)[1].strip().lower()
                if arg in ("on", "off"):
                    self.state["raw"] = (arg == "on")
                    print(f"🔧 원문 보기가 {'켜졌습니다' if self.state['raw'] else '꺼졌습니다'}.")
                continue
                
            elif user_input.startswith("/jobs "):
                # 더 많은 채용정보 보기
                try:
                    count = int(user_input.split(" ", 1)[1].strip())
                    self.state["max_results"] = min(count, 50)  # 최대 50개로 제한
                    print(f"📊 채용정보 결과 개수가 {self.state['max_results']}개로 설정되었습니다.")
                except:
                    print("❌ 사용법: /jobs <숫자> (예: /jobs 10)")
                continue
                
            elif user_input.startswith("/field "):
                # 직무 분야 설정
                field_name = user_input.split(" ", 1)[1].strip()
                if field_name in self.job_fields:
                    self.state["job_field"] = self.job_fields[field_name]
                    print(f"🔧 직무 분야가 '{field_name}'로 설정되었습니다.")
                elif field_name == "전체":
                    self.state["job_field"] = None
                    print("🔧 직무 분야 필터가 해제되었습니다.")
                else:
                    print("❌ 사용 가능한 분야:")
                    fields = list(self.job_fields.keys())[:20]  # 처음 20개만 표시
                    for i in range(0, len(fields), 4):
                        row = fields[i:i+4]
                        print("  ".join(f"{field:<15}" for field in row))
                    print("...")
                    print("💡 전체 목록은 /help 참고 | 사용법: /field <분야명> 또는 /field 전체")
                continue
            
            # 자연어 검색 처리
            intent = self.analyze_user_intent(user_input)
            print(f"🔍 분석된 의도: {intent}")  # 디버깅용
            
            if intent["type"] == "unknown":
                print("🤔 무엇을 도와드릴까요? 채용정보나 부동산 정보를 검색해보세요!")
                print("예: '종로구 채용정보 찾아줘', '강남구 아파트 실거래가 알려줘'")
                continue
            
            # 검색 실행
            result = await self.handle_search(intent)
            print(result)


async def main():
    chatbot = IntegratedChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
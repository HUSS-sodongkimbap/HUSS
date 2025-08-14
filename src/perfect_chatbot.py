# perfect_chatbot.py — 완벽한 통합 챗봇 (정책 조회 추가)
import asyncio
import json
import re
from typing import Dict, Any, List, Optional

# 확장된 오케스트레이터 import
from enhanced_orchestrator import EnhancedOrchestrator


class PerfectChatbot:
    def __init__(self):
        self.orchestrator = EnhancedOrchestrator()
        self.state = {
            "raw": False,
            "max_results": 10,
            "region_code": "11110",  # 기본: 종로구
            "deal_ymd": "202506",     # 기본: 2025년 6월
            "job_field": None         # 직무 분야 필터
        }
        
        # API 명세서의 정확한 직무 분야 매핑 (기존 코드 그대로)
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
        
        # 직무 분야 키워드 매핑 (자연어 인식용)
        self.job_keywords = {
            "통신": "정보통신", "IT": "정보통신", "개발": "정보통신", "프로그래밍": "정보통신",
            "의료": "보건.의료", "병원": "보건.의료", "간호": "보건.의료",
            "교육": "교육.자연.사회과학", "선생님": "교육.자연.사회과학", "강사": "교육.자연.사회과학",
            "경영": "경영.회계.사무", "회계": "경영.회계.사무", "사무": "경영.회계.사무",
            "건설": "건설", "건축": "건설",
            "연구": "연구", "개발": "연구"
        }
    
    def print_help(self):
        print("""
🤖 통합 챗봇 명령어 가이드

[자연어 검색]
  "종로구에서 통신 관련 일자리와 아파트 매물, 정책 알려줘"
  "강남구 의료 분야 채용공고와 실거래가 보여줘"
  "천안시 IT 일자리와 주거 정보, 청년 정책 검색해줘"
  "청양군 정책만 알려줘"
  "종로구 아파트 실거래가만 보여줘"
  
[설정 명령어]
  /region <법정동코드>               → 지역 설정 (예: /region 11680)
  /date <YYYYMM>                    → 부동산 거래 년월 설정
  /jobs <숫자>                      → 채용정보 결과 개수 설정
  /field <분야명>                   → 직무 분야 설정
  /show                            → 현재 설정 보기
  /help                            → 도움말
  /exit                            → 종료

[지역 코드 참고]
  11110: 종로구    11680: 강남구    11170: 용산구
  44131: 천안시    42150: 강릉시    44790: 청양군
""".strip())
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 분석해서 의도 파악 (정책 검색 추가)"""
        text = user_input.lower().replace(" ", "")
        
        intent = {
            "type": "unknown",
            "search_jobs": False,
            "search_realestate": False,
            "search_policies": False,  # 정책 검색 추가
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
        job_keywords = ["채용", "구인", "일자리", "취업", "인턴", "공채", "모집", "구직", "직장"]
        realestate_keywords = ["아파트", "부동산", "실거래가", "매매", "집", "주택", "오피스텔", "매물"]
        policy_keywords = ["정책", "지원", "혜택", "복지", "청년정책", "청소년정책"]  # 정책 키워드 추가
        living_keywords = ["살곳", "살", "거주", "이사", "정착", "생활"]
        
        has_job = any(keyword in text for keyword in job_keywords)
        has_realestate = any(keyword in text for keyword in realestate_keywords + living_keywords)
        has_policy = any(keyword in text for keyword in policy_keywords)  # 정책 검색 감지
        
        # 검색 유형 결정 (정책 추가)
        search_count = sum([has_job, has_realestate, has_policy])
        
        if search_count >= 2:  # 2개 이상이면 통합 검색
            intent["type"] = "comprehensive"
            intent["search_jobs"] = has_job
            intent["search_realestate"] = has_realestate
            intent["search_policies"] = has_policy
        elif has_job:
            intent["type"] = "jobs_only"
            intent["search_jobs"] = True
        elif has_realestate:
            intent["type"] = "realestate_only"
            intent["search_realestate"] = True
        elif has_policy:  # 정책만 검색
            intent["type"] = "policies_only"
            intent["search_policies"] = True
        elif any(keyword in text for keyword in ["통합", "전체", "모든", "다"]):
            intent["type"] = "comprehensive" 
            intent["search_jobs"] = True
            intent["search_realestate"] = True
            intent["search_policies"] = True
        
        # 채용 필터 감지 (기존과 동일)
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
        
        # 직무 분야 필터 감지 (키워드 매핑 추가)
        detected_field = None
        
        # 1. 정확한 분야명 매칭
        for field_name, code in self.job_fields.items():
            if field_name in text:
                detected_field = code
                break
        
        # 2. 키워드 매핑으로 매칭
        if not detected_field:
            for keyword, field_name in self.job_keywords.items():
                if keyword in text and field_name in self.job_fields:
                    detected_field = self.job_fields[field_name]
                    break
        
        if detected_field:
            intent["filters"]["ncsCdLst"] = detected_field
        
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
        """채용정보 결과를 보기 좋게 포맷 (지역 관련성 표시 추가)"""
        if not results:
            if region_name:
                return f"📋 **{region_name} 지역의 채용정보를 찾을 수 없습니다.**\n\n💡 **제안:**\n- 인근 도시나 도 단위로 검색해보세요\n- 원격근무 가능한 직종을 찾아보세요"
            return "📋 채용정보를 찾을 수 없습니다."
        
        output = [f"📋 **채용정보** (총 {len(results)}건, 지역 관련성 순)\n"]
        
        for i, job in enumerate(results[:limit], 1):
            title = job.get("recrutPbancTtl", "제목 없음")
            company = job.get("instNm", "기관명 없음")
            hire_type = job.get("hireTypeNmLst", "")
            region = job.get("workRgnNmLst", "")
            deadline = job.get("pbancEndYmd", "")
            ncs_field = job.get("ncsCdNmLst", "")
            
            # 날짜 포맷팅
            if deadline and len(deadline) == 8:
                deadline = f"{deadline[:4]}.{deadline[4:6]}.{deadline[6:]}"
            
            # 지역 표시 방식 개선
            region_display = region
            if region:
                region_count = region.count(',') + 1
                if region_count >= 10:
                    region_display = f"전국 ({region_count}개 지역)"
                elif region_count > 3:
                    region_display = f"{region.split(',')[0]} 외 {region_count-1}개 지역"
                else:
                    region_display = region
            
            output.append(f"{'='*50}")
            output.append(f"📍 **{i}. {company}** ({hire_type})")
            output.append(f"📌 **{title}**")
            
            if region_display:
                output.append(f"🌍 **근무지역**: {region_display}")
            if deadline:
                output.append(f"⏰ **마감일**: {deadline}")
            if ncs_field:
                output.append(f"🔧 **직무분야**: {ncs_field}")
            output.append("")
            
        return "\n".join(output)
    
    def format_realestate_results(self, apt_data: List[Dict], limit: int = 5) -> str:
        """부동산 결과를 보기 좋게 포맷 (기존과 동일)"""
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
            
            # 가격 포맷팅
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
    
    def format_policy_results(self, policies: List[Dict], limit: int = 5, region_name: str = "") -> str:
        """청소년정책 결과를 보기 좋게 포맷 (새로 추가)"""
        if not policies:
            if region_name:
                return f"📋 **{region_name} 지역의 청소년정책을 찾을 수 없습니다.**"
            return "📋 청소년정책을 찾을 수 없습니다."
        
        output = [f"📋 **청소년정책** (총 {len(policies)}건 중 상위 {min(limit, len(policies))}건)\n"]
        
        for i, policy in enumerate(policies[:limit], 1):
            name = policy.get("plcyNm", "정책명 없음")
            category = policy.get("lclsfNm", "") + " > " + policy.get("mclsfNm", "")
            keywords = policy.get("plcyKywdNm", "")
            region = policy.get("sprvsnInstCdNm", "")
            explanation = policy.get("plcyExplnCn", "")[:100]
            
            output.append(f"{'='*50}")
            output.append(f"📍 **{i}. {name}**")
            output.append(f"📂 **분류**: {category}")
            
            if keywords:
                output.append(f"🏷️ **키워드**: {keywords}")
            if region:
                output.append(f"🌍 **담당기관**: {region}")
            if explanation:
                output.append(f"📝 **설명**: {explanation}...")
            output.append("")
            
        return "\n".join(output)
    
    def filter_and_sort_jobs_by_region(self, jobs: List[Dict], target_region_code: str) -> List[Dict]:
        """채용정보를 지역 관련성에 따라 정렬 (개선된 버전)"""
        # 지역 코드 → 우선순위 키워드 매핑
        region_mapping = {
            "11110": ["종로", "서울"],          # 종로구 → 종로 우선, 서울 차순위
            "11680": ["강남", "서울"], 
            "11170": ["용산", "서울"],
            "11200": ["성동", "서울"],
            "11215": ["광진", "서울"],
            "44131": ["천안", "충남", "충청"],   # 천안시 → 천안 우선, 충남 차순위
            "42150": ["강릉", "강원"],          # 강릉시 → 강릉 우선, 강원 차순위
            "44790": ["청양", "충남", "충청"]
        }
        
        if target_region_code not in region_mapping:
            return jobs[:10]  # 매핑 없으면 상위 10개만
        
        target_keywords = region_mapping[target_region_code]
        
        def calculate_job_score(job):
            """채용공고의 지역 관련성 점수 계산"""
            work_region = job.get("workRgnNmLst", "").replace(" ", "")
            
            if not work_region:
                return (999, 0)  # 지역 정보 없으면 최하위
            
            # 지역 개수 계산 (콤마로 구분)
            region_count = work_region.count(',') + 1 if work_region else 0
            
            # 관련성 점수 계산
            relevance_score = 999  # 기본값 (관련 없음)
            
            for i, keyword in enumerate(target_keywords):
                if keyword in work_region:
                    relevance_score = i  # 첫 번째 키워드가 가장 높은 점수
                    break
            
            # 정렬 기준: (관련성 점수, 지역 개수)
            # 관련성 점수가 낮을수록 우선 (0이 최고), 지역 개수가 적을수록 우선
            return (relevance_score, region_count)
        
        # 모든 채용공고에 점수 부여 후 정렬
        scored_jobs = [(job, calculate_job_score(job)) for job in jobs]
        sorted_jobs = sorted(scored_jobs, key=lambda x: x[1])
        
        # 상위 15개만 반환 (너무 많으면 부담)
        result_jobs = [job for job, score in sorted_jobs[:15]]
        
        return result_jobs
    
    async def handle_search(self, intent: Dict[str, Any]) -> str:
        """검색 의도에 따라 적절한 검색 수행 (정책 검색 추가)"""
        region_code = intent.get("region_mentioned") or self.state["region_code"]
        region_name = self.get_region_name(region_code)
        
        results = []
        
        try:
            # 1. 채용정보 검색
            if intent["search_jobs"]:
                print("📋 채용정보 검색 중...")
                job_result = self.orchestrator.call_recruitment_tool(
                    'listRecruitments',
                    {
                        'pageNo': 1, 
                        'numOfRows': 100,  # 필터링을 위해 많이 가져오기
                        'filters': {**intent.get("filters", {}), 
                                   **({} if self.state["job_field"] is None else {"ncsCdLst": self.state["job_field"]})}
                    }
                )
                
                if job_result["status"] == "success":
                    job_data = job_result["result"].get("data", {}).get("result", [])
                    # 개선된 지역별 정렬 적용
                    if intent.get("region_mentioned"):
                        job_data = self.filter_and_sort_jobs_by_region(job_data, intent["region_mentioned"])
                    results.append(self.format_job_results(job_data, limit=5, region_name=region_name))
                else:
                    results.append(f"📋 채용정보 검색 실패: {job_result.get('message', '알 수 없는 오류')}")
            
            # 2. 부동산 검색
            if intent["search_realestate"]:
                print("🏠 부동산 검색 중...")
                apt_result = self.orchestrator.call_realestate_tool(
                    'getApartmentTrades',
                    {
                        'lawdcd': region_code,
                        'deal_ymd': self.state["deal_ymd"],
                        'pageNo': 1,
                        'numOfRows': 10
                    }
                )
                
                if apt_result["status"] == "success":
                    apt_text = apt_result["result"].get("text", "")
                    apt_data = self.parse_apartment_xml(apt_text)
                    results.append(self.format_realestate_results(apt_data, limit=5))
                else:
                    results.append(f"🏠 부동산 검색 실패: {apt_result.get('message', '알 수 없는 오류')}")
            
            # 3. 청소년정책 검색 (새로 추가)
            if intent["search_policies"]:
                print("📋 청소년정책 검색 중...")
                policy_result = self.orchestrator.call_youth_policy_tool(
                    'searchPoliciesByRegion',
                    {
                        'regionCode': region_code,
                        'pageNum': 1,
                        'pageSize': 15
                    }
                )
                
                if policy_result["status"] == "success":
                    policies = policy_result["result"].get("policies", [])
                    results.append(self.format_policy_results(policies, limit=5, region_name=region_name))
                else:
                    results.append(f"📋 청소년정책 검색 실패: {policy_result.get('message', '알 수 없는 오류')}")
        
        except Exception as e:
            return f"❌ 검색 중 오류가 발생했습니다: {str(e)}"
        
        if results:
            return f"\n🔍 **{region_name} 검색 결과**\n\n" + "\n\n".join(results)
        else:
            return "❌ 검색 결과를 찾을 수 없습니다."
    
    def parse_apartment_xml(self, xml_text: str) -> List[Dict]:
        """XML 형태의 아파트 데이터를 파싱 (기존과 동일)"""
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
        print("🤖 통합 정보 조회 플랫폼이 시작되었습니다!")
        print("💼 채용정보 + 🏠 부동산 + 📋 청소년정책을 통합 검색할 수 있습니다.\n")
        
        # 직무 분야 안내
        print("📋 **검색 가능한 직무 분야:**")
        print("=" * 60)
        fields_list = list(self.job_fields.keys())
        
        # 4열로 정렬해서 출력
        for i in range(0, len(fields_list), 4):
            row = fields_list[i:i+4]
            print("  ".join(f"{field:<15}" for field in row))
        print("=" * 60)
        print("💡 사용법: '종로구 통신 일자리', '강남구 의료 분야 채용' 등\n")
        
        self.print_help()
        
        while True:
            try:
                user_input = input("\n💬 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 플랫폼을 종료합니다. 좋은 하루 되세요!")
                break
            
            if not user_input:
                continue
            
            # 명령어 처리 (기존과 동일)
            if user_input.lower() in ["/exit", "exit", "quit", "종료"]:
                print("👋 플랫폼을 종료합니다. 좋은 하루 되세요!")
                break
                
            elif user_input.lower() in ["/help", "help", "도움말"]:
                self.print_help()
                continue
                
            elif user_input.lower() == "/show":
                print("📊 현재 설정:")
                print(f"  📍 지역: {self.get_region_name(self.state['region_code'])}")
                print(f"  📅 거래년월: {self.state['deal_ymd']}")
                if self.state["job_field"]:
                    field_name = [k for k, v in self.job_fields.items() if v == self.state["job_field"]][0]
                    print(f"  🔧 직무분야: {field_name}")
                else:
                    print(f"  🔧 직무분야: 전체")
                continue
                
            elif user_input.startswith("/region "):
                region_code = user_input.split(" ", 1)[1].strip()
                self.state["region_code"] = region_code
                region_name = self.get_region_name(region_code)
                print(f"📍 지역이 {region_name}({region_code})로 설정되었습니다.")
                continue
                
            elif user_input.startswith("/date "):
                date = user_input.split(" ", 1)[1].strip()
                if len(date) == 6 and date.isdigit():
                    self.state["deal_ymd"] = date
                    print(f"📅 거래 년월이 {date}로 설정되었습니다.")
                else:
                    print("❌ 날짜 형식: YYYYMM (예: 202506)")
                continue
                
            elif user_input.startswith("/jobs "):
                try:
                    count = int(user_input.split(" ", 1)[1].strip())
                    self.state["max_results"] = min(count, 50)
                    print(f"📊 채용정보 결과 개수가 {self.state['max_results']}개로 설정되었습니다.")
                except:
                    print("❌ 사용법: /jobs <숫자> (예: /jobs 10)")
                continue
                
            elif user_input.startswith("/field "):
                field_name = user_input.split(" ", 1)[1].strip()
                if field_name in self.job_fields:
                    self.state["job_field"] = self.job_fields[field_name]
                    print(f"🔧 직무 분야가 '{field_name}'로 설정되었습니다.")
                elif field_name == "전체":
                    self.state["job_field"] = None
                    print("🔧 직무 분야 필터가 해제되었습니다.")
                else:
                    print("❌ 사용 가능한 분야:")
                    fields = list(self.job_fields.keys())[:12]
                    for i in range(0, len(fields), 3):
                        row = fields[i:i+3]
                        print("  ".join(f"{field:<20}" for field in row))
                    print("💡 사용법: /field <분야명> 또는 /field 전체")
                continue
            
            # 자연어 검색 처리
            intent = self.analyze_user_intent(user_input)
            print(f"🔍 분석된 의도: {intent['type']}")
            
            if intent["type"] == "unknown":
                print("🤔 무엇을 도와드릴까요? 다음과 같이 검색해보세요:")
                print("예: '종로구에서 통신 관련 일자리와 아파트 매물, 정책 알려줘'")
                print("    '강남구 의료 분야 채용공고만 보여줘'")
                print("    '천안시 청년 정책만 검색해줘'")
                continue
            
            # 검색 실행
            result = await self.handle_search(intent)
            print(result)


async def main():
    chatbot = PerfectChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
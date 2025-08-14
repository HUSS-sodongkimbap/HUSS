# recruitment-mcp

data.go.kr (기획재정부_공공기관 채용정보 조회서비스)를 MCP 서버로 감싼 예제.

## 설치
# 1. 가상환경 생성
conda create -n mcp-project python=3.12

# 2. 활성화  
conda activate mcp-project

python -m pip install -U pip setuptools wheel

pip install mcp fastmcp httpx python-dotenv


## 실행
```bash
python integrated_chatbot.py
```

## 사용
MCP 클라이언트(예: IDE/챗봇)에서 아래 툴을 호출:
- listRecruitments: { "path": "recruitment/목록_엔드포인트", "filters": {"region":"R3010","empType":"R1010"} }
- getRecruitmentDetail: { "path": "recruitment/상세_엔드포인트", "params": {"noticeId":"..."} }

※ 실제 path/파라미터 키는 Swagger 명세와 동일하게 넣어야 합니다.

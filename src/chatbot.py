# chatbot.py — MCP 클라이언트 (서버 프로세스 스폰 + REPL)
import asyncio
import os
import sys
import json
from typing import Any, Dict, List, Tuple
from types import SimpleNamespace

from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

# 버전에 따라 있을 수도 있는 타입
try:
    from mcp.client.stdio import StdioServerParameters
except Exception:
    StdioServerParameters = None

load_dotenv()

DESIRED_TOOL = "listRecruitments"

def make_server_params(cmd: str, args: List[str]):
    if StdioServerParameters is not None:
        return StdioServerParameters(command=cmd, args=args)
    return SimpleNamespace(command=cmd, args=args)

def tool_name_of(tool):
    # 다양한 객체/딕트 형태 방어
    return (
        getattr(tool, "name", None)
        or getattr(tool, "tool", None)
        or getattr(tool, "id", None)
        or (tool.get("name") if isinstance(tool, dict) else None)
    )

def tool_schema_of(tool):
    return getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or (
        tool.get("inputSchema") if isinstance(tool, dict) else None
    )

def normalize_response_content(resp) -> Tuple[bool, Any]:
    content = getattr(resp, "content", None)
    if not content:
        return False, "No content returned."
    out: List[Any] = []
    for item in content:
        # dict로 오는 경우(신버전에서 이미 dict)
        if isinstance(item, dict):
            t = item.get("type")
            if t == "text":
                out.append({"text": item.get("text", "")})
            elif t == "json":
                out.append(item.get("json"))
            else:
                out.append(item)
            continue

        # 객체 속성 형태
        t = getattr(item, "type", None)
        if t == "text":
            out.append({"text": getattr(item, "text", "")})
        elif t == "json":
            out.append(getattr(item, "json", None))
        elif isinstance(item, (dict, list, str, int, float, bool)) or item is None:
            out.append(item)
        else:
            try:
                out.append(str(item))
            except Exception:
                out.append(repr(item))
    return True, out[0] if len(out) == 1 else out

def print_help():
    print("""
[명령어]
  그냥 문장 입력         → 자연어를 코드로 간단 매핑해 /list 호출
  /call                  → 현재 설정 그대로 호출
  /raw on|off            → 원문 응답 보기 토글
  /show                  → 현재 설정 보기
  /path <value>          → path 설정 (기본: list)
  /rows <n>              → numOfRows 설정
  /page <n>              → pageNo 설정
  /filter <JSON>         → filters 설정 (예: {"hireTypeLst":"R1050,R1060,R1070"})
  /help                  → 도움말
  /exit                  → 종료
""".strip())

def quick_map_to_filters(utter: str) -> Dict[str, Any]:
    """
    아주 간단한 자연어→코드 매핑.
    필요한 매핑은 사용하며 점점 늘려가면 됨.
    """
    f: Dict[str, Any] = {}
    text = utter.replace(" ", "")

    # 청년 인턴 → 고용유형 코드들
    if "청년" in text and "인턴" in text:
        f["hireTypeLst"] = "R1050,R1060,R1070"

    # 학력 조건
    if "학력무관" in text:
        f["acbgCondLst"] = "R7010"
    if "대졸" in text or "4년제" in text:
        f["acbgCondLst"] = "R7050"
    if "고졸" in text:
        f["acbgCondLst"] = "R7040"

    # 서버에서 기본 type=json 넣으므로 여기선 생략
    return f

async def call_list(session: ClientSession, path: str, page: int, rows: int, filters: Dict[str, Any] | None, raw: bool):
    params: Dict[str, Any] = {
        "path": path,           # 기본 'list'
        "pageNo": page,
        "numOfRows": rows,
    }
    if filters:
        params["filters"] = filters

    resp = await session.call_tool(name=DESIRED_TOOL, arguments=params)
    ok, payload = normalize_response_content(resp)
    if not ok:
        print("[ERROR]", payload)
        return

    if raw:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    # 보기 좋은 최소 출력
    if isinstance(payload, dict):
        req = payload.get("request_url")
        status = payload.get("status_code") or payload.get("status")
        data = payload.get("data")
        text = payload.get("text")
        if req: print(f"[URL] {req}")
        if status is not None: print(f"[STATUS] {status}")
        if data is not None:
            print("[DATA]")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif text is not None:
            print("[TEXT]")
            print(text[:2000])
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

async def main():
    # server.py 절대경로 확보 (경로 꼬임 방지)
    server_path = os.path.abspath("server.py")
    if not os.path.exists(server_path):
        print(f"[!] server.py가 현재 폴더에 없습니다. server_path={server_path} cwd={os.getcwd()}")
        return

    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    server_params = make_server_params(sys.executable, [server_path])

    state = {
        "path": "list",   # ★ 기본 오퍼레이션 경로
        "page": 1,
        "rows": 10,
        "filters": None,
        "raw": False,
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = getattr(tools_result, "tools", tools_result)
            available = [tool_name_of(t) for t in tools]
            print("[DEBUG] Available tools:", available)
            tool_info = None
            for t in tools:
                if tool_name_of(t) == DESIRED_TOOL:
                    tool_info = t
                    break
            if not tool_info:
                print(f"[!] Tool '{DESIRED_TOOL}' not found. Available:", available)
                return

            schema = tool_schema_of(tool_info)
            if schema:
                print("[DEBUG] Input schema:", json.dumps(schema, indent=2, ensure_ascii=False))

            print_help()

            while True:
                try:
                    user = input("\n> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nbye!")
                    break

                if not user:
                    continue

                # 명령 처리
                if user.lower() in ("/exit", "exit", "quit"):
                    print("bye!")
                    break
                if user.lower() in ("/help", "help", "?"):
                    print_help(); continue
                if user.lower() == "/show":
                    print(json.dumps(state, indent=2, ensure_ascii=False)); continue
                if user.startswith("/raw "):
                    arg = user.split(" ", 1)[1].strip().lower()
                    if arg in ("on", "off"):
                        state["raw"] = (arg == "on")
                        print(f"[OK] raw = {state['raw']}")
                    else:
                        print("[ERR] /raw on|off")
                    continue
                if user.startswith("/path "):
                    state["path"] = user.split(" ", 1)[1].strip()
                    print(f"[OK] path = {state['path']}"); continue
                if user.startswith("/rows "):
                    try:
                        state["rows"] = int(user.split(" ", 1)[1].strip()); print(f"[OK] rows = {state['rows']}")
                    except Exception:
                        print("[ERR] /rows <정수>")
                    continue
                if user.startswith("/page "):
                    try:
                        state["page"] = int(user.split(" ", 1)[1].strip()); print(f"[OK] page = {state['page']}")
                    except Exception:
                        print("[ERR] /page <정수>")
                    continue
                if user.startswith("/filter "):
                    raw = user.split(" ", 1)[1].strip()
                    try:
                        obj = json.loads(raw)
                        if isinstance(obj, dict):
                            state["filters"] = obj
                            print(f"[OK] filters = {json.dumps(obj, ensure_ascii=False)}")
                        else:
                            print("[ERR] /filter 는 JSON 객체여야 합니다. 예) /filter {\"hireTypeLst\":\"R1050,R1060\"}")
                    except Exception as e:
                        print(f"[ERR] JSON 파싱 실패: {e}")
                    continue
                if user.lower() == "/call":
                    print(f"[INFO] call path='{state['path']}' page={state['page']} rows={state['rows']} filters={state['filters']}")
                    try:
                        await call_list(session, state["path"], state["page"], state["rows"], state["filters"], state["raw"])
                    except Exception as e:
                        print("[ERROR] tool call failed:", e)
                    continue

                # 자연어 → 필터 매핑 후 호출
                mapped = quick_map_to_filters(user)
                state["filters"] = {**(state["filters"] or {}), **mapped}
                print(f"[INFO] mapped filters = {json.dumps(state['filters'], ensure_ascii=False)}")
                try:
                    await call_list(session, state["path"], state["page"], state["rows"], state["filters"], state["raw"])
                except Exception as e:
                    print("[ERROR] tool call failed:", e)

if __name__ == "__main__":
    asyncio.run(main())

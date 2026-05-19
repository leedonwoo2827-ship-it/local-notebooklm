# 📓 Local NotebookLM

NotebookLM 스타일 3-패널 로컬 웹 앱.
PDF / Docx / TXT / HWPX / SRT / VTT / MP4 를 소스로 받아, **Citation Q&A** 와 **Studio 산출물**(보고서·슬라이드·마인드맵·플래시카드·퀴즈 …) 을 생성합니다.

- 본체: [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything) (LightRAG)
- LLM: 사내/외부 LiteLLM 프록시 → DeepSeek / Claude / GPT 라우팅
- 임베딩: 로컬 BGE-M3 (다국어)
- STT: faster-whisper 자동 디바이스 + LiteLLM 폴백

---

## 🚀 빠른 설치 (Windows)

폴더를 받은 뒤 더블클릭만 하면 됩니다.

| 단계 | 파일 | 비고 |
|---|---|---|
| ① 설치 | **`설치.bat`** 더블클릭 | venv 생성 + 의존성 설치 (10–15분, 1회) |
| ② 실행 | **`실행.bat`** 더블클릭 | 브라우저가 자동으로 열림 (`http://localhost:8501`) |
| ③ 키 입력 | 화면 우상단 **⚙️ 클릭** | 회사에서 발급받은 URL + API 키 2칸 입력 후 저장 |

종료는 검은 창에서 `Ctrl+C`.

## 🍎 빠른 설치 (macOS / Linux)

```bash
./setup.sh     # 1회만 — 의존성 설치
./run.sh       # 매번 — 브라우저로 자동 열림
```

설치 후 브라우저 우상단 **⚙️** 클릭 → 회사에서 발급받은 URL + API 키 입력.

---

## 🔑 API 키 발급 안내

회사 관리자에게 1인 1개 발급 요청하세요. 받은 정보 두 줄을 ⚙️ 설정에서 입력하면 됩니다:

| 필드 | 예시 |
|---|---|
| 프록시 URL | `http://your-litellm-proxy:4000` |
| API 키 | `sk-...` (회사 대시보드에서 발급) |

키는 **이 PC의 `.env` 파일에만** 저장되며 외부로 전송되지 않습니다. 다른 PC로 옮기면 다시 입력해야 합니다.

---

## 🖥️ 화면 구성 (NotebookLM 3-패널)

```
┌─────────────────┬───────────────────────┬─────────────────┐
│  📚 출처        │  💬 채팅              │  🛠️ Studio       │
│  + 소스 추가    │  (Citation Q&A)       │  📄 보고서      │
│  ─ PDF          │                       │  🎴 슬라이드    │
│  ─ Docx         │  사용자: 핵심은?      │  🧠 마인드맵    │
│  ─ HWPX         │  AI: ...[Paper p.3]   │  🗂️ 플래시카드  │
│  ─ SRT/VTT      │                       │  ❓ 퀴즈        │
│  ─ MP4 (STT)    │  [질문 입력]          │                 │
│  노트북 선택 ▾  │                       │  생성된 메모    │
└─────────────────┴───────────────────────┴─────────────────┘
```

- **출처(Sources)**: 파일 업로드 → 자동 인덱싱. 노트북별로 분리.
- **채팅(Chat)**: 소스에서 인용한 답변. 출처 표시 포함.
- **Studio**: 버튼 한 번에 보고서/슬라이드/마인드맵/플래시카드/퀴즈 생성.

## 🧩 Studio 확장 (새 산출물 추가)

산출물 추가가 폴더에 파일 2개 떨어뜨리는 것만으로 끝납니다:

```
studio/my_artifact.py        # META + async def generate(rag, context)
prompts/my_artifact_ko.md    # 프롬프트 본문
```

앱 재시작 → 우측 패널에 버튼 자동 등장. 예시는 [studio/report.py](studio/report.py) 참고.

활용 아이디어:
- `aim_deck` — 해외사업용 영업 자료
- `marketing_post` — SNS 마케팅 카피
- `email_draft` — 고객사 메일 초안
- `translate_en` — 영문 요약
- `glossary` — 용어집

---

## 📂 폴더 구조

```
local-notebooklm/
├── 설치.bat / 실행.bat            ← Windows 더블클릭
├── setup.sh / run.sh              ← macOS · Linux
├── app.py                         ← Streamlit 엔트리
├── core/                          ← LLM · 임베딩 · RAG · STT · ingest
├── studio/                        ← 산출물 플러그인 (파일 추가만으로 확장)
├── ui/                            ← 3-패널 + ⚙️ 설정
├── prompts/                       ← 산출물별 한국어 프롬프트
└── data/notebooks/<name>/         ← 노트북별 인덱스 · 소스 · 산출물
```

## ⚙️ 고급 설정 (`.env`)

`.env` 파일 또는 ⚙️ 설정 화면에서 변경:

| 변수 | 기본 | 설명 |
|---|---|---|
| `UBION_LITELLM_URL` | (빈칸) | LiteLLM 프록시 주소 — ⚙️에서 입력 |
| `UBION_LITELLM_KEY` | (빈칸) | API 키 — ⚙️에서 입력 |
| `LLM_BACKEND` | `litellm` | `litellm` 또는 `ollama`(완전 로컬) |
| `WHISPER_BACKEND` | `local` | `local`(faster-whisper) 또는 `litellm` |
| `MODEL_CHAT` | `deepseek-v4-flash` | 일반 채팅 |
| `MODEL_STRONG` | `claude-sonnet-4-6` | 보고서·심층 Q&A |
| `EMBED_MODEL` | `BAAI/bge-m3` | 로컬 임베딩 (고정 권장) |

VPS 이전 시 `WHISPER_BACKEND=litellm` 만 바꾸면 GPU 없는 환경에서도 동일 코드 동작.

---

## 🛠️ 자주 묻는 문제

| 증상 | 해결 |
|---|---|
| `python을 찾을 수 없습니다` | [Python 3.10+](https://www.python.org/downloads/) 설치 시 "Add Python to PATH" 체크 |
| `LibreOffice를 찾을 수 없습니다` | HWPX 안 쓰면 무시. 쓰려면 [LibreOffice](https://www.libreoffice.org/download/) 설치 |
| `401 Unauthorized` | ⚙️ 설정에서 키/URL 다시 확인. 저장 후 새로고침 |
| 첫 PDF 인덱싱이 5–10분 | MinerU OCR/레이아웃 분석 정상 동작. 두 번째부터는 캐시 사용 |
| 임베딩이 느림 (CPU) | `pip install torch --index-url https://download.pytorch.org/whl/cu121` 로 CUDA 빌드 |

---

## 📄 라이선스

MIT

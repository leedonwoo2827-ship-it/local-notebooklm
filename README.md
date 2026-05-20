# 📓 Local NotebookLM

NotebookLM 스타일 3-패널 로컬 웹 앱.
PDF / Docx / TXT / HWPX / SRT / VTT / MP4 를 소스로 받아, **Citation Q&A** 와 **Studio 산출물**(보고서·슬라이드·마인드맵·플래시카드·퀴즈 …) 을 생성합니다.

> ⚠️ 입력 소스는 텍스트가 이미 추출되는 포맷만 지원합니다 — PDF(텍스트 추출 가능한 것) / Docx / Md / Txt / SRT · VTT / MP4(STT). 스캔/이미지 PDF 는 외부 OCR 로 텍스트를 추출해 `.txt` 로 넣어주세요. (필요 시 `.env` 의 `ENABLE_MINERU=true` 로 MinerU OCR 분기를 켤 수 있지만 기본은 OFF — CPU PC 부담과 멀티모달 quirk 회피용 결정)

- 본체: [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything) (LightRAG)
- LLM: 사내/외부 LiteLLM 프록시 → DeepSeek / Claude / GPT 라우팅
- 임베딩: 로컬 BGE-M3 (다국어)
- STT: faster-whisper 자동 디바이스 + LiteLLM 폴백

---

## 💻 권장 사양

| 항목 | 최소 | 권장 | 비고 |
|---|---|---|---|
| **OS** | Windows 10 · macOS 12 · Ubuntu 20.04 | Windows 11 · macOS 14 · Ubuntu 22.04 | |
| **Python** | 3.10 | 3.11 / 3.12 | 설치 시 "Add Python to PATH" 체크 |
| **RAM** | 8 GB | 16 GB | PDF 5–10개 동시 인덱싱 시 12 GB 권장 |
| **디스크** | **15 GB 여유** | 30 GB | 의존성·모델·노트북 인덱스 누적 |
| **GPU** | 없어도 됨 | RTX 3060 6 GB+ (선택) | CPU만으로도 동작. GPU 있으면 STT/임베딩 5–10배 빠름 |
| **인터넷** | 필수 | — | 최초 모델 다운로드 + LiteLLM 프록시 호출 |

### 디스크 사용량 (최초 설치 후)

| 구성 요소 | 크기 |
|---|---|
| Python venv + 의존성 (`raganything[all]`, `torch` 등) | ~6–8 GB |
| BGE-M3 임베딩 모델 (BAAI/bge-m3, 최초 사용 시 자동 다운로드) | ~2.3 GB |
| MinerU 파서 모델 (PDF 레이아웃·OCR, 최초 사용 시 자동 다운로드) | ~3–4 GB |
| faster-whisper 모델 (CPU = small ~500 MB, GPU = large-v3 ~3 GB) | 0.5–3 GB |
| LibreOffice (HWPX 변환 시만 필요, 선택) | ~700 MB |
| 노트북별 인덱스 (`data/notebooks/`) | 노트북 1개 = PDF 5권 기준 ~100–300 MB |

### 🖥️ GPU 없는 일반 사무용 PC라면

기본 설정이 이미 CPU에 맞춰져 있어 **그대로 사용 가능**합니다. 다만 다음 두 줄을 `.env`에 두면 더 가볍게 돌아갑니다:

```
EMBED_DEVICE=cpu              # 임베딩을 명시적으로 CPU 사용
WHISPER_BACKEND=litellm       # STT를 회사 프록시로 보냄 (로컬 자원 0)
```

성능 체감 (Intel i5 노트북 / RAM 16 GB 기준):
- 임베딩(BGE-M3 CPU): PDF 1권(50쪽) ≈ 1–2분
- STT 5분 영상: 로컬 small ≈ 3분 / LiteLLM gpt-4o-transcribe ≈ 30초
- 채팅 응답: LiteLLM 프록시로 처리되므로 PC 사양 무관 (1–3초)

### ⚡ GPU가 있다면

자동으로 인식되어 BGE-M3 임베딩과 faster-whisper가 CUDA에서 동작합니다. 별도 설정 불필요. 만약 PyTorch가 CPU 빌드로 잘못 깔렸다면:

```
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 🚀 빠른 설치 (Windows)

폴더를 받은 뒤 더블클릭만 하면 됩니다.

| 단계 | 파일 | 비고 |
|---|---|---|
| ① 설치 | **`setup.bat`** 더블클릭 | venv 생성 + 의존성 설치 (10–15분, 1회) |
| ② 실행 | **`run.bat`** 더블클릭 | 브라우저가 자동으로 열림 (`http://localhost:8501`) |
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
├── setup.bat / run.bat            ← Windows 더블클릭
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
| `MODEL_CHAT` | `deepseek-v4-flash` | 일반 채팅 (저렴 모드 기본) |
| `MODEL_STRONG` | `deepseek-v4-flash` | 보고서·심층 Q&A — 품질↑ 원하면 `claude-sonnet-4-6` |
| `MODEL_CREATIVE` | `deepseek-v4-flash` | Studio 슬라이드/창작 — 품질↑ 원하면 `claude-sonnet-4-6` |
| `EMBED_MODEL` | `BAAI/bge-m3` | 로컬 임베딩 (고정 권장) |

> 비용·모델별 추천 프로파일은 [docs/pricing.md](docs/pricing.md) 참고.
> 회사 PPTX 양식 적용 가이드(디자인팀 전달용)는 [docs/pptx_template_spec.md](docs/pptx_template_spec.md) 참고.
> 회사 HWPX 보고서 양식 가이드는 [docs/hwpx_template_spec.md](docs/hwpx_template_spec.md) 참고 (보고서 HWPX 출력은 향후 패치 예정).

VPS 이전 시 `WHISPER_BACKEND=litellm` 만 바꾸면 GPU 없는 환경에서도 동일 코드 동작.

---

## 🛠️ 자주 묻는 문제

| 증상 | 해결 |
|---|---|
| `python을 찾을 수 없습니다` | [Python 3.10+](https://www.python.org/downloads/) 설치 시 "Add Python to PATH" 체크 |
| `LibreOffice를 찾을 수 없습니다` | HWPX 안 쓰면 무시. 쓰려면 [LibreOffice](https://www.libreoffice.org/download/) 설치 |
| `WinError 1314` / `Mineru command failed` (Windows) | **Windows 개발자 모드 켜기** — `Windows 키` → "개발자용 설정" → "개발자 모드" 토글 ON. huggingface가 모델 캐시할 때 symlink 권한이 필요해서 발생. 활성화 후 `run.bat` 재실행 |
| `401 Unauthorized` | ⚙️ 설정에서 키/URL 다시 확인. 저장 후 새로고침 |
| 첫 PDF 인덱싱이 5–10분 | MinerU OCR/레이아웃 분석 정상 동작. 두 번째부터는 캐시 사용 |
| 디스크 부족 | 모델 자동 다운로드로 ~15 GB 사용. 외장 SSD에 폴더 두고 작업해도 OK |
| CPU에서 STT 느림 | `.env`의 `WHISPER_BACKEND=litellm` 로 변경 → 프록시로 위임 |
| 임베딩이 느림 (CPU) | `pip install torch --index-url https://download.pytorch.org/whl/cu121` 로 CUDA 빌드 (GPU 있을 때만) |

---

## 📄 라이선스

MIT

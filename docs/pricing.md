# 💰 모델 가격 & 사용 가이드

> 2026-05 기준 사내 LiteLLM 프록시 카탈로그 가격 (1M 토큰당, USD).
> 정확한 본인 사용량은 회사 LiteLLM 대시보드 `/ui/` 에서 확인.

## 🆕 현재 기본 매핑

이 앱은 **용도별로 모델을 분리** 한 상태로 출시된다 (`.env` 기본값).
「전부 DeepSeek 통일」 이 아니다.

| 프로파일 | 기본 모델 | 입력 \$/1M | 출력 \$/1M | 호출 1회당 (입력 5K + 출력 1K 기준) |
|---|---|---:|---:|---:|
| `MODEL_CHAT` | `deepseek-v4-flash` | $0.20 | $1.00 | $0.002 |
| `MODEL_EXTRACT` | `gpt-5.4-mini` | $0.25 | $2.00 | $0.003 |
| `MODEL_STRONG` | `claude-sonnet-4-6` | $3.00 | $15.00 | $0.030 |
| `MODEL_CREATIVE` | `claude-sonnet-4-6` | $3.00 | $15.00 | $0.030 |

선정 이유:
- **CHAT** — 가장 호출이 잦고 1M 컨텍스트 필요. DeepSeek-flash 가 가성비 최적.
- **EXTRACT** — LightRAG 인덱싱은 `response_format = json_schema` 를 쓴다.
  DeepSeek 는 이 기능 미지원 → 반드시 OpenAI/Claude 계열 필요. `gpt-5.4-mini`
  가 카탈로그에서 가장 싸면서 JSON schema 지원.
- **STRONG / CREATIVE** — Studio 산출물(슬라이드 교안, 카드뉴스, HWPX 보고서)
  은 한국어 작문 품질이 결과물 가치를 좌우. Claude Sonnet 가 사실상 표준.

## ⚠️ LiteLLM 프록시 60초 천장 (반드시 알아둘 것)

사내 LiteLLM 프록시(`http://192.168.50.119:4000`)는 업스트림 모델 호출의
**timeout=60초** 가 천장이다. 60초를 넘으면 `litellm.Timeout` → 클라이언트에
**HTTP 408** 로 떨어진다.

영향:
- **단발 호출 산출물** (슬라이드 교안 20장, HWPX 보고서, 큰 PPTX) 에서 입력+출력
  합이 **약 5만 토큰 이상** 으로 커지면 일관되게 실패한다.
- 폴백 모델 체인(claude-sonnet-4-6 → gemini-3.1-pro-preview) 도 같은 60초 천장을
  다시 받으므로 폴백도 실패.
- 클라이언트 측에서 timeout/retry 늘려도 효과 없음. **입력 크기를 줄이거나,
  더 빠른 모델로 다운그레이드** 가 유일한 해법.

회피 가이드:
- 자막은 노트북당 1~2개씩만. 책은 1장 단위.
- 슬라이드 교안 장수를 콘텐츠 분량에 맞춰 (책 1장 ≈ 6~10장, 자막 3개 ≈ 20장).
- 큰 입력이 필요한 산출물 전에 채팅창에서 먼저 압축한 뒤 그 결과로 가공.

---

## 📊 모델별 가격 (LiteLLM 프록시 카탈로그)

### 텍스트 LLM

| 모델 | 입력 \$/1M | 출력 \$/1M | 컨텍스트 | 비고 |
|---|---:|---:|---:|---|
| **deepseek-v4-flash** ⭐ | $0.20 | $1.00 | 1M | 가장 저렴 + 1M 컨텍스트 + 한국어 OK. JSON schema 미지원 |
| deepseek-v4-flash-think | $0.20 | $1.00 | 1M | 추론 사고과정 표시 |
| deepseek-v4-pro | $0.70 | $2.80 | 1M | DeepSeek 강화 버전 |
| gemini-3.1-flash-lite | $0.05 | $0.30 | 1M | 카탈로그 최저가, 한국어 약함 |
| gemini-3-flash-preview | $0.30 | $2.50 | 1M | Google 빠른 응답 |
| gemini-3.1-pro-preview | $1.25 | $10.00 | 2M | Google 최상 |
| chat-latest | $1.25 | $10.00 | — | OpenAI 동적 라우팅 |
| gpt-5.4-nano | $0.05 | $0.40 | — | OpenAI 미니 |
| **gpt-5.4-mini** ⭐ | $0.25 | $2.00 | — | OpenAI 소형 — 기본 EXTRACT |
| gpt-5.5 | $1.25 | $10.00 | — | OpenAI 표준 |
| gpt-5.5-pro | $5.00 | $40.00 | — | OpenAI 최상 |
| claude-haiku-4-5 | $1.00 | $5.00 | 200K | Claude 빠름 |
| **claude-sonnet-4-6** ⭐ | $3.00 | $15.00 | 1M | 한국어 강세 — 기본 STRONG/CREATIVE |
| claude-opus-4-7 | $15.00 | $75.00 | 1M | Claude 최상 |

### 이미지 생성

| 모델 | 가격 | 비고 |
|---|---|---|
| gemini-3.1-flash-image-preview | ~$0.04/장 | Nano Banana 2, 가성비 |
| gemini-3-pro-image-preview | ~$0.12/장 | 4K 가능 |
| gpt-image-2 | ~$0.04/장 | 텍스트 렌더링 정확 |

### TTS / STT

| 모델 | 가격 | 비고 |
|---|---|---|
| gpt-4o-mini-tts | $0.60/1M 문자 | 한국어 자연 |
| eleven_flash_v2_5 | $0.10/1M 문자 | 가장 저렴 |
| eleven_v3 | $5.00/1M 문자 | 70+ 언어 프리미엄 |
| **whisper-1** | $0.006/분 | STT 가장 저렴 |
| gpt-4o-transcribe | $0.006/분 | STT 한국어 정확 |
| gpt-4o-transcribe-diarize | $0.015/분 | 화자 분리 |

### 비디오 생성 (참고용, 본 앱에서는 미사용)

| 모델 | 가격 | 비고 |
|---|---|---|
| veo-3.1-fast-generate-preview | ~$0.15/초 | 가장 저렴 |
| veo-3.1-generate-preview | ~$0.40/초 | 1080p |
| sora-2 / sora-2-pro | ~$0.30–$0.50/초 | 2026-09-24 sunset 예정 |

---

## 🎯 사용 시나리오별 예상 비용

> 계산식: `(입력 토큰 / 1M) × 입력단가 + (출력 토큰 / 1M) × 출력단가`.
> 토큰량은 한국어 기준 추정치. **모든 시나리오는 현재 기본 매핑(CHAT=DeepSeek,
> EXTRACT=gpt-5.4-mini, STRONG/CREATIVE=Sonnet)** 기준.

### 시나리오 A — 통신연수 책 1개 장 (실측 기반)

**작업**: `input_16-43.pdf` 같은 책 1장(본문 20쪽, ≈1.5만 토큰) 인덱싱 +
퀴즈 5문항 + 슬라이드 교안 8장 + 플래시카드 30장

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 | 사용 모델 |
|---|---:|---:|---|
| Entity 추출 (인덱싱, 최초 1회) | 15,000 | 4,000 | gpt-5.4-mini |
| 퀴즈 5문항 | 16,000 | 2,500 | claude-sonnet-4-6 |
| 슬라이드 교안 8장 | 16,000 | 5,000 | claude-sonnet-4-6 |
| 플래시카드 30장 | 16,000 | 4,000 | claude-sonnet-4-6 |
| 채팅 5회 (요약·확인) | 25,000 | 5,000 | deepseek-v4-flash |

**비용 합계**:

| 단계 | 입력 \$ | 출력 \$ | 소계 |
|---|---:|---:|---:|
| Entity 추출 | $0.0038 | $0.0080 | **$0.012** |
| 퀴즈 | $0.0480 | $0.0375 | **$0.086** |
| 슬라이드 교안 | $0.0480 | $0.0750 | **$0.123** |
| 플래시카드 | $0.0480 | $0.0600 | **$0.108** |
| 채팅 5회 | $0.0050 | $0.0050 | **$0.010** |
| **합계 (1장 풀세트)** | | | **약 $0.34** |

> 인덱싱은 노트북당 1회. 같은 책의 다음 장은 새 노트북이라 다시 인덱싱하지만
> 책 1장 단위면 인덱싱 비용 자체가 미미.

> **60초 천장 주의**: 책 1장(≈1.5만 토큰)은 단발 호출에 충분히 들어온다. 다만
> 슬라이드 교안을 20장(디폴트)로 두면 출력 토큰이 늘어나 60초를 넘길 수 있으니
> **8~10장으로 줄여서** 호출할 것.

### 시나리오 B — 강의 자막 1시간 → 산출물 세트

**작업**: VTT 1개(~25K자, 약 18K 토큰) → 인덱싱 + 채팅 5회 + 카드뉴스 4장 + HWPX 보고서

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 | 사용 모델 |
|---|---:|---:|---|
| Entity 추출 (자막 1개) | 18,000 | 4,000 | gpt-5.4-mini |
| 채팅 5회 | 30,000 | 6,000 | deepseek-v4-flash |
| 카드뉴스 4장 | 20,000 | 3,500 | claude-sonnet-4-6 |
| HWPX 보고서 | 20,000 | 5,000 | claude-sonnet-4-6 |

**비용 합계**:

| 단계 | 비용 |
|---|---:|
| Entity 추출 | $0.013 |
| 채팅 5회 | $0.012 |
| 카드뉴스 4장 | $0.113 |
| HWPX 보고서 | $0.135 |
| **합계 (자막 1개)** | **약 $0.27** |

### 시나리오 C — 자막 3개(은행 FP) 풀세트

**작업**: VTT 3개(각 ~25K자, 강의 1시간씩, 합 ~54K 토큰) → 인덱싱 + 산출물 세트

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 | 사용 모델 |
|---|---:|---:|---|
| Entity 추출 (자막 3개 합) | 54,000 | 10,000 | gpt-5.4-mini |
| 채팅 10회 | 60,000 | 12,000 | deepseek-v4-flash |
| 카드뉴스 4장 (회차 3 + 종합 1) | 25,000 | 4,000 | claude-sonnet-4-6 |
| HWPX 보고서 1회 | 50,000 | 5,000 | claude-sonnet-4-6 |

**비용 합계**:

| 단계 | 비용 |
|---|---:|
| Entity 추출 (최초 1회) | $0.034 |
| 채팅 10회 | $0.024 |
| 카드뉴스 4장 | $0.135 |
| HWPX 보고서 | $0.225 |
| **합계 (첫 회)** | **약 $0.42** |
| **반복 산출물 (인덱싱 캐시 적중)** | **약 $0.38** |

> ⚠️ **슬라이드 교안 20장은 이 규모에서 60초 천장 위험.** 자막 3개 + 20장 JSON
> 출력은 단발 호출 한 번에 처리하기 부담스럽다. 자막을 2개로 줄이거나, 노트북을
> 회차별로 분리해 처리.

### 시나리오 D — 해외사업 AIM 자료 1편 풀세트

**작업**: PDF 10권(400쪽 ≈ 600K 토큰) 인덱싱 + 채팅 50회 + Studio 산출물 7개
(HWPX 2 + 영문요약 + 슬라이드 + 마인드맵 + 플래시카드 + 퀴즈)

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 |
|---|---:|---:|
| Entity 추출 (인덱싱) | 600,000 | 120,000 |
| 채팅 50회 | 500,000 | 100,000 |
| Studio 7개 (창작) | 200,000 | 60,000 |

**비용 합계 (기본 매핑)**:

| 단계 | 비용 |
|---|---:|
| Entity 추출 (gpt-5.4-mini) | $0.39 |
| 채팅 50회 (DeepSeek) | $0.20 |
| Studio 7개 (Sonnet) | $1.50 |
| **합계** | **약 $2.09** |

> ⚠️ PDF 묶음이 클수록 자료당 단발 산출물(예: HWPX 보고서 전체 자료 한 번에)이
> 60초 천장에 자주 걸린다. 부분/장별로 끊어서 산출하는 게 안전.

### 시나리오 E — 가벼운 학습 노트북 1개

**작업**: PDF 5권(총 200쪽 ≈ 300K 토큰) 인덱싱 + 채팅 20회 + Studio 3개(HWPX·슬라이드·마인드맵)

| 단계 | 입력 토큰 | 출력 토큰 | 비용 |
|---|---:|---:|---:|
| Entity 추출 | 300,000 | 60,000 | $0.20 |
| 채팅 20회 (DeepSeek) | 200,000 | 50,000 | $0.09 |
| Studio 3개 (Sonnet) | 80,000 | 25,000 | $0.62 |
| **합계** | | | **약 $0.91** |

---

## ⚠️ 알려진 모델 제약

### DeepSeek 는 `MODEL_EXTRACT` 에 쓸 수 없다

LightRAG 는 entity 추출 단계에서 OpenAI 호환 API 의
`response_format = {"type": "json_schema", ...}` 기능을 사용한다.
**DeepSeek-v4 계열은 이 기능을 지원하지 않아 400 에러를 반환** 한다:

```
litellm.BadRequestError: DeepseekException -
  "This response_format type is unavailable now"
```

→ `MODEL_EXTRACT` 만큼은 **`gpt-5.4-mini`(권장) / `claude-haiku-4-5` /
`gemini-3-flash-preview`** 중 하나로 둬야 한다.
`MODEL_CHAT` · `MODEL_CREATIVE` · `MODEL_STRONG` 은 DeepSeek 사용 가능
(우리 코드가 JSON 모드를 안 쓰는 영역).

### LiteLLM 60초 천장 (앞서 설명한 그것)

위 「⚠️ LiteLLM 프록시 60초 천장」 섹션 참고. 모델 선택 자체보다도, **단발 호출
입력 크기 ≤ 5만 토큰** 을 지키는 게 훨씬 중요하다.

---

## 🎛 프로파일별 추천 (필요 시 `.env`에서 변경)

### 1. 현재 기본 (분리 모드)

```
MODEL_CHAT=deepseek-v4-flash      # 채팅 — DeepSeek 저렴
MODEL_EXTRACT=gpt-5.4-mini        # ⭐ 인덱싱 — JSON schema 필요
MODEL_STRONG=claude-sonnet-4-6    # 보고서/심층 Q&A
MODEL_CREATIVE=claude-sonnet-4-6  # Studio 산출물(슬라이드/카드뉴스)
```

→ 한국어 산출물 품질과 비용의 균형. 일반 사용자 디폴트.

### 2. 저렴 모드 (산출물 품질 양보)

```
MODEL_CHAT=deepseek-v4-flash
MODEL_EXTRACT=gpt-5.4-mini       # 변경 불가 (JSON schema)
MODEL_STRONG=deepseek-v4-flash
MODEL_CREATIVE=deepseek-v4-flash
```

→ Studio 산출물도 DeepSeek 로. 비용 ~1/10. 한국어 작문 품질이 살짝 떨어짐 +
60초 천장은 그대로 유효(DeepSeek 가 빠르지만, 입력+출력이 크면 여전히 timeout).

### 3. 프리미엄 (전부 최상)

```
MODEL_CHAT=claude-sonnet-4-6
MODEL_EXTRACT=claude-sonnet-4-6  # JSON schema OK
MODEL_STRONG=claude-opus-4-7
MODEL_CREATIVE=claude-sonnet-4-6
```

→ 학술 논문·법률 문서·정밀 인용이 중요할 때. 비용 ~10×.

### 4. 영문 자료 특화

```
MODEL_CHAT=gpt-5.4-mini
MODEL_STRONG=gpt-5.5
MODEL_CREATIVE=gpt-5.5
```

→ 영문 자료 비중이 클 때 OpenAI 가 유리한 경우.

### 5. 초저가 (실험·테스트용)

```
MODEL_CHAT=gemini-3.1-flash-lite
MODEL_EXTRACT=gemini-3-flash-preview   # JSON schema OK
MODEL_STRONG=gemini-3.1-flash-lite
MODEL_CREATIVE=gemini-3.1-flash-lite
```

→ 카탈로그 최저가. 한국어 품질 떨어짐. 데모/PoC 용.

---

## 🔍 비용 확인 방법

1. 회사 LiteLLM 대시보드 (`/ui/`) → 본인 키 → `Usage` 탭
2. 본 앱은 LiteLLM 프록시를 거치므로 호출 단위로 자동 집계됨
3. Redis 캐시 10분 — 동일 질문 재호출 시 $0 (캐시 히트, 정상)

## 📌 비용 0 항목 (로컬 처리)

| 항목 | 위치 |
|---|---|
| 임베딩 (BGE-M3) | 로컬 |
| MinerU PDF 파서 | 로컬 |
| faster-whisper STT (`WHISPER_BACKEND=local`) | 로컬 |
| LightRAG 그래프/벡터 인덱싱 자체 | 로컬 |

→ 인터넷 차단된 환경에서도 인덱싱은 진행되지만, **LLM 호출(질의·산출물 생성)
및 프록시 STT 는 LiteLLM 프록시 필요**.

## 🔗 참고

- LiteLLM 모델 카탈로그 전체: 사내 대시보드 `/ui/` 또는 [LiteLLM 공식 문서](https://docs.litellm.ai/docs/providers)
- DeepSeek 공식 가격: <https://platform.deepseek.com/api-docs/pricing>
- Anthropic 공식 가격: <https://www.anthropic.com/pricing>

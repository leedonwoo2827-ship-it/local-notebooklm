# 💰 모델 가격 & 사용 가이드

> 2026-05 기준 사내 LiteLLM 프록시 카탈로그 가격 (1M 토큰당, USD).
> 정확한 본인 사용량은 회사 LiteLLM 대시보드 `/ui/` 에서 확인.

## 🆕 기본값 (저렴 모드)

이 앱은 **모든 호출을 `deepseek-v4-flash`로 통일**한 상태로 출시됩니다.

| 프로파일 | 기본 모델 | 입력 \$/1M | 출력 \$/1M | 호출 1회당 (입력 5K + 출력 1K 기준) |
|---|---|---:|---:|---:|
| `MODEL_CHAT` | `deepseek-v4-flash` | $0.20 | $1.00 | $0.002 |
| `MODEL_EXTRACT` | `deepseek-v4-flash` | $0.20 | $1.00 | $0.002 |
| `MODEL_STRONG` | `deepseek-v4-flash` | $0.20 | $1.00 | $0.002 |
| `MODEL_CREATIVE` | `deepseek-v4-flash` | $0.20 | $1.00 | $0.002 |

**참고 비용** (1 PDF 50쪽 인덱싱 + 채팅 5회 + Studio 산출물 5개):
- 인덱싱 입력 100K, 출력 20K → $0.040
- 채팅 5회 입력 50K, 출력 13K → $0.023
- Studio 5개 입력 50K, 출력 25K → $0.035
- **합계: $0.098**

## 📊 모델별 가격 (LiteLLM 프록시 카탈로그)

### 텍스트 LLM

| 모델 | 입력 \$/1M | 출력 \$/1M | 컨텍스트 | 비고 |
|---|---:|---:|---:|---|
| **deepseek-v4-flash** ⭐ | $0.20 | $1.00 | 1M | 가장 저렴 + 1M 컨텍스트 + 한국어 OK |
| deepseek-v4-flash-think | $0.20 | $1.00 | 1M | 추론 사고과정 표시 |
| deepseek-v4-pro | $0.70 | $2.80 | 1M | DeepSeek 강화 버전 |
| gemini-3.1-flash-lite | $0.05 | $0.30 | 1M | 카탈로그 최저가, 한국어 약함 |
| gemini-3-flash-preview | $0.30 | $2.50 | 1M | Google 빠른 응답 |
| gemini-3.1-pro-preview | $1.25 | $10.00 | 2M | Google 최상 |
| chat-latest | $1.25 | $10.00 | — | OpenAI 동적 라우팅 |
| gpt-5.4-nano | $0.05 | $0.40 | — | OpenAI 미니 |
| gpt-5.4-mini | $0.25 | $2.00 | — | OpenAI 소형 |
| gpt-5.5 | $1.25 | $10.00 | — | OpenAI 표준 |
| gpt-5.5-pro | $5.00 | $40.00 | — | OpenAI 최상 |
| claude-haiku-4-5 | $1.00 | $5.00 | 200K | Claude 빠름 |
| **claude-sonnet-4-6** | $3.00 | $15.00 | 1M | Claude 한국어 강세 |
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

## 🎯 사용 시나리오별 예상 비용

> 계산식: `(입력 토큰 / 1M) × 입력단가 + (출력 토큰 / 1M) × 출력단가`.
> 토큰량은 한국어 기준 추정치.

### 시나리오 A — 가벼운 학습 노트북 1개

**작업**: PDF 5권(총 200쪽) 인덱싱 + 채팅 20회 + Studio 산출물 3개(보고서·슬라이드·마인드맵)

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 |
|---|---:|---:|
| Entity 추출 (인덱싱) | 500,000 | 100,000 |
| 채팅 20회 | 200,000 | 50,000 |
| Studio 3개 | 100,000 | 30,000 |

**모드별 합계**:

| 단계 | 저렴 모드 (전부 DeepSeek) | 균형 모드 (Studio만 Sonnet) | 프리미엄 (전부 Sonnet) |
|---|---:|---:|---:|
| Entity 추출 | $0.20 | $0.20 | $3.00 |
| 채팅 20회 | $0.09 | $0.09 | $1.35 |
| Studio 3개 | $0.05 | $0.75 | $0.75 |
| **합계** | **$0.34** | **$1.04** | **$5.10** |

### 시나리오 B — 영상 1시간 → 카드뉴스 1편

**작업**: MP4 1시간 → STT → 자막 텍스트 인덱싱 + Studio 슬라이드 6장

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 |
|---|---:|---:|
| 자막 인덱싱 | 15,000 | 5,000 |
| 슬라이드 6장 | 5,000 | 3,000 |

**모드별 합계**:

| 단계 | 저렴 모드 | 균형 모드 | 프리미엄 |
|---|---:|---:|---:|
| STT 로컬 (faster-whisper) | $0.00 | $0.00 | $0.00 |
| STT 프록시 (whisper-1, 60분) | $0.36 | $0.36 | $0.36 |
| 자막 인덱싱 | $0.008 | $0.008 | $0.120 |
| 슬라이드 6장 | $0.004 | $0.060 | $0.060 |
| **합계 (STT 로컬)** | **$0.01** | **$0.07** | **$0.18** |
| **합계 (STT 프록시)** | **$0.37** | **$0.43** | **$0.54** |

### 시나리오 C — 해외사업 AIM 자료 1편 풀세트

**작업**: PDF 10권(400쪽) 인덱싱 + 채팅 50회 + Studio 산출물 7개(보고서 2 + 영문요약 + 슬라이드 + 마인드맵 + 플래시카드 + 퀴즈)

**토큰 추정**:

| 단계 | 입력 토큰 | 출력 토큰 |
|---|---:|---:|
| Entity 추출 (인덱싱) | 1,000,000 | 200,000 |
| 채팅 50회 | 500,000 | 120,000 |
| Studio 7개 | 200,000 | 70,000 |

**모드별 합계**:

| 단계 | 저렴 모드 | 균형 모드 | 프리미엄 |
|---|---:|---:|---:|
| Entity 추출 | $0.40 | $0.40 | $6.00 |
| 채팅 50회 | $0.22 | $0.22 | $3.30 |
| Studio 7개 | $0.11 | $1.65 | $1.65 |
| **합계** | **$0.73** | **$2.27** | **$10.95** |

## 🎛 프로파일별 추천 (필요 시 `.env`에서 변경)

### 1. 저렴 모드 (기본, 변경 불필요)

```
MODEL_CHAT=deepseek-v4-flash
MODEL_EXTRACT=deepseek-v4-flash
MODEL_STRONG=deepseek-v4-flash
MODEL_CREATIVE=deepseek-v4-flash
```

→ 비용 최소. 한국어 일반 학습 자료/사내 문서엔 충분.

### 2. 균형 모드 (보고서·창작만 강화)

```
MODEL_CHAT=deepseek-v4-flash
MODEL_EXTRACT=deepseek-v4-flash
MODEL_STRONG=claude-sonnet-4-6
MODEL_CREATIVE=claude-sonnet-4-6
```

→ 채팅·인덱싱은 저렴, Studio 산출물만 고품질. 가성비 좋음.

### 3. 프리미엄 (전부 최상)

```
MODEL_CHAT=claude-sonnet-4-6
MODEL_EXTRACT=claude-sonnet-4-6
MODEL_STRONG=claude-opus-4-7
MODEL_CREATIVE=claude-sonnet-4-6
```

→ 학술 논문·법률 문서·정밀 인용이 중요할 때. 비용 ~15x.

### 4. 영문 자료 특화

```
MODEL_CHAT=gpt-5.4-mini
MODEL_STRONG=gpt-5.5
```

→ 영문 자료 비중이 클 때 OpenAI가 한국어 모델보다 유리할 수 있음.

### 5. 초저가 (실험·테스트용)

```
MODEL_CHAT=gemini-3.1-flash-lite
MODEL_EXTRACT=gemini-3.1-flash-lite
MODEL_STRONG=gemini-3.1-flash-lite
MODEL_CREATIVE=gemini-3.1-flash-lite
```

→ 가장 저렴하지만 한국어 품질 떨어짐. 데모/PoC용.

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

→ 인터넷 차단된 환경에서도 인덱싱은 진행되지만, **LLM 호출(질의·산출물 생성)은 프록시 필요**.

## 🔗 참고

- LiteLLM 모델 카탈로그 전체: 사내 대시보드 `/ui/` 또는 [LiteLLM 공식 문서](https://docs.litellm.ai/docs/providers)
- DeepSeek 공식 가격: <https://platform.deepseek.com/api-docs/pricing>
- Anthropic 공식 가격: <https://www.anthropic.com/pricing>

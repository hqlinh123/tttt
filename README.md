<div align="center">

# 🎙️ Viterbox

### Vietnamese Text-to-Speech với Voice Cloning

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-dolly--vn%2Fviterbox-orange)](https://huggingface.co/dolly-vn/viterbox)

**Viterbox** là mô hình Text-to-Speech tiếng Việt chất lượng cao, được fine-tune từ [Chatterbox](https://github.com/resemble-ai/chatterbox) trên **3000+ giờ** dữ liệu tiếng Việt.

[Demo](#-demo) • [Cài đặt](#-cài-đặt) • [Sử dụng](#-sử-dụng) • [API](#-python-api) • [Tham số](#️-tham-số)

</div>

---

## 🌟 Điểm nổi bật

| Tính năng | Mô tả |
|-----------|-------|
| 🇻🇳 **Tiếng Việt tự nhiên** | Phát âm chuẩn, ngữ điệu tự nhiên, hỗ trợ đầy đủ dấu thanh |
| 🎯 **Zero-shot Voice Cloning** | Clone giọng nói chỉ với 3-10 giây audio mẫu |
| 🌍 **Đa ngôn ngữ** | Hỗ trợ tiếng Việt và 23 ngôn ngữ khác từ Chatterbox |
| ⚡ **Inference nhanh** | Tối ưu cho GPU với mixed precision (FP16) |
| 🎨 **Giao diện đẹp** | Web UI với Gradio, dễ sử dụng |
| 📝 **Xử lý văn bản dài** | Tự động chia câu, ghép audio với crossfade |

---

## 📊 Thông tin Model

### Kiến trúc

Viterbox được xây dựng trên kiến trúc **Chatterbox** của Resemble AI:

- **T3 (Text-to-Token)**: Transformer 520M tham số, chuyển văn bản thành speech tokens
- **S3Gen (Token-to-Speech)**: Flow-matching vocoder, chuyển tokens thành waveform
- **Voice Encoder**: Trích xuất speaker embedding từ audio mẫu

### Dữ liệu huấn luyện

Model được fine-tune trên **3000+ giờ** dữ liệu tiếng Việt chất lượng cao:

| Dataset | Mô tả | Thời lượng |
|---------|-------|------------|
| **ViVoice** | Dữ liệu giọng đọc đa dạng | ~1000h |
| **PhoAudiobook** | Sách nói tiếng Việt | ~1000h |
| **Dolly-Audio** | Dữ liệu nội bộ, đa giọng | ~1000h |

### Base Model

- **Chatterbox Multilingual**: Pretrained trên 23 ngôn ngữ
- **Vocabulary**: Mở rộng thêm 1845 tokens cho tiếng Việt (tổng 2549 tokens)

---

## 📦 Cài đặt

### Yêu cầu hệ thống

- **Python**: 3.10+
- **CUDA**: 11.8+ (khuyến nghị)
- **RAM**: 8GB+
- **VRAM**: 6GB+ (GPU)

### Cài đặt từ source

```bash
# Clone repo
git clone https://github.com/iamdinhthuan/viterbox-tts.git
cd viterbox

# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### Cài đặt với pip

```bash
pip install -e .
```

---

## 🚀 Sử dụng

### 1. Giao diện Web (Gradio)

```bash
python app.py
```

Mở trình duyệt tại `http://localhost:7860`

<details>
<summary>📸 Screenshot</summary>

Giao diện web cho phép:
- Nhập văn bản cần đọc
- Chọn ngôn ngữ (Tiếng Việt / English)
- Upload hoặc chọn giọng mẫu
- Điều chỉnh các tham số
- Nghe và tải audio

</details>

### 2. Python API

```python
from viterbox import Viterbox

# Load model (tự động download từ HuggingFace)
tts = Viterbox.from_pretrained("cuda")

# Tạo audio với giọng mặc định
audio = tts.generate("Xin chào, tôi là Viterbox!")

# Tạo audio với voice cloning
audio = tts.generate(
    text="Xin chào, tôi là Viterbox!",
    language="vi",
    audio_prompt="path/to/reference.wav",
    exaggeration=0.5,
    cfg_weight=0.5,
    temperature=0.8,
    sentence_pause_ms=500,
)

# Lưu file
tts.save_audio(audio, "output.wav")
```

### 3. Command Line

```bash
# Tạo audio đơn giản
python inference.py --text "Xin chào ạ, em là trợ lý ảo của bạn, em có thể giúp gì cho anh ạ?" --output output.wav

# Với voice cloning và các tham số
python inference.py \
    --text "Việt Nam là một đất nước xinh đẹp." \
    --lang vi \
    --ref reference.wav \
    --exaggeration 0.5 \
    --sentence-pause 0.5 \
    --output output.wav
```

---

## 🎛️ Tham số

| Tham số | Mô tả | Giá trị | Mặc định |
|---------|-------|---------|----------|
| `text` | Văn bản cần đọc | string | (bắt buộc) |
| `language` | Mã ngôn ngữ | `"vi"`, `"en"` | `"vi"` |
| `audio_prompt` | Audio mẫu cho voice cloning | path/tensor | `None` |
| `exaggeration` | Mức độ biểu cảm | 0.0 - 2.0 | 0.5 |
| `cfg_weight` | Độ bám sát giọng mẫu | 0.0 - 1.0 | 0.5 |
| `temperature` | Độ ngẫu nhiên/sáng tạo | 0.1 - 1.0 | 0.8 |
| `top_p` | Top-p sampling | 0.0 - 1.0 | 0.9 |
| `repetition_penalty` | Phạt lặp từ | 1.0 - 2.0 | 1.2 |
| `sentence_pause_ms` | Thời gian ngắt giữa câu | 0 - 2000 | 500 |
| `crossfade_ms` | Thời gian crossfade | 0 - 100 | 50 |

### Giải thích tham số

- **exaggeration**: Tăng để giọng biểu cảm hơn, giảm để giọng trầm tĩnh hơn
- **cfg_weight**: Tăng để giọng giống mẫu hơn, giảm để tự nhiên hơn
- **temperature**: Tăng để giọng đa dạng hơn, giảm để ổn định hơn
- **sentence_pause_ms**: Thời gian nghỉ giữa các câu (hữu ích cho văn bản dài)

---

## 📁 Cấu trúc dự án

```
viterbox/
├── app.py                  # Gradio Web UI
├── inference.py            # CLI inference script
├── requirements.txt        # Dependencies
├── pyproject.toml          # Package config
├── README.md
├── wavs/                   # Thư mục chứa giọng mẫu
│   └── *.wav
└── viterbox/               # Core library
    ├── __init__.py
    ├── tts.py              # Main Viterbox class
    └── models/             # Model components
        ├── t3/             # T3 Text-to-Token model
        ├── s3gen/          # S3Gen vocoder
        ├── s3tokenizer/    # Speech tokenizer
        ├── voice_encoder/  # Speaker encoder
        └── tokenizers/     # Text tokenizer
```

---

## 🔧 Model Files

Model được host trên HuggingFace Hub: [`dolly-vn/viterbox`](https://huggingface.co/dolly-vn/viterbox)

| File | Mô tả | Kích thước |
|------|-------|------------|
| `t3_ml24ls_v2.safetensors` | T3 model (fine-tuned) | ~2GB |
| `s3gen.pt` | S3Gen vocoder | ~1GB |
| `ve.pt` | Voice Encoder | ~20MB |
| `tokenizer_vi_expanded.json` | Tokenizer với vocab tiếng Việt | ~50KB |
| `conds.pt` | Default voice conditioning | ~1MB |

---

## 📝 Ví dụ

### Đọc văn bản dài

```python
text = """
Việt Nam là một quốc gia nằm ở phía đông bán đảo Đông Dương.
Đất nước có hình chữ S với chiều dài hơn 1600 km.
Thủ đô Hà Nội là trung tâm chính trị và văn hóa của cả nước.
"""

audio = tts.generate(
    text=text,
    language="vi",
    sentence_pause_ms=600,  # Nghỉ 0.6s giữa các câu
)
tts.save_audio(audio, "vietnam.wav")
```

### Voice cloning

```python
# Clone giọng từ file WAV (3-10 giây)
audio = tts.generate(
    text="Xin chào, tôi có thể nói bằng giọng của bạn!",
    audio_prompt="my_voice.wav",
    exaggeration=0.3,  # Giọng tự nhiên
    cfg_weight=0.7,    # Bám sát giọng mẫu
)
```

---

## ⚠️ Lưu ý

- **Audio mẫu**: Nên sử dụng audio sạch, không nhiễu, 3-10 giây
- **VRAM**: Model cần ~6GB VRAM, nếu không đủ có thể dùng CPU (chậm hơn)
- **Văn bản**: Hỗ trợ tốt nhất với văn bản có dấu đầy đủ

---

## 🙏 Credits

- **Base Model**: [Chatterbox](https://github.com/resemble-ai/chatterbox) by Resemble AI
- **Datasets**: ViVoice, PhoAudiobook, Dolly-Audio
- **Fine-tuning**: [Dolly VN](https://github.com/dolly-vn) - Speech Team @ [ContextBoxAI](https://contextbox.ai)

---

## 📄 License

**CC BY-NC 4.0** (Creative Commons Attribution-NonCommercial 4.0)

- ✅ Được sử dụng cho mục đích **phi thương mại**
- ✅ Được chia sẻ, sửa đổi với ghi nguồn
- ❌ **KHÔNG** được sử dụng cho mục đích thương mại

Liên hệ thương mại: [contextbox.ai](https://contextbox.ai)

---

<div align="center">

**Made with ❤️ by [Dolly VN](https://github.com/dolly-vn) @ [ContextBoxAI](https://contextbox.ai)**

[⬆ Về đầu trang](#️-viterbox)

</div>
# aigentics-rest-api

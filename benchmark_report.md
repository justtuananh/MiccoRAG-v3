# Báo cáo Benchmark: Hybrid Search vs Vector-only Search

**Thời điểm:** 02:13 - 02:30 ngày 27/03/2026  
**Workspace:** test  
**Backend:** MiccoRAG-v2 (FastAPI + NexusRAG)  
**Phương pháp đo:** Browser Control (Wall Clock Time từ lúc nhấn Send → stream hoàn tất)

---

## 1. Thời gian phản hồi (Response Latency)

| # | Câu hỏi | Hybrid (s) | Vector-only (s) | Nhanh hơn |
|---|---------|:----------:|:---------------:|:---------:|
| 1 | Flare là gì? | **6** | 8 | Hybrid |
| 2 | Ragas là gì? Các tiêu chí đánh giá RAG? | 68 | **4** | Vector-only |
| 3 | Monitoring Trong Production quan tâm metric nào? | 50 | **30** | Vector-only |
| 4 | Liệt kê các mô hình embedding phổ biến? | 30 | **5** | Vector-only |
| 5 | Hybrid search là gì? | 40 | **5** | Vector-only |
| | **Trung bình** | **38.8s** | **10.4s** | **Vector-only** |

### Phân tích Thời gian
- **Vector-only nhanh hơn đáng kể** ở 4/5 câu hỏi, trung bình nhanh hơn **28.4 giây** (~3.7× lần).
- Hybrid chỉ nhanh hơn ở câu Q1 (Flare là gì? - đơn giản, ngắn).
- Nguyên nhân Hybrid chậm hơn: phải thực hiện đồng thời **dense retrieval + sparse (BM25) retrieval + Knowledge Graph lookup + Reciprocal Rank Fusion (RRF reranking)**, trong khi Vector-only chỉ cần lookup Qdrant vector similarity.

---

## 2. Đánh giá Độ liên quan (LLM Relevance Evaluation)

### Câu 1: Flare là gì?

| Tiêu chí | Hybrid | Vector-only |
|----------|--------|-------------|
| Độ chính xác | ✅ Chi tiết, có ví dụ thuật toán từng bước | ✅ Đúng, đầy đủ |
| Ngắn gọn | Dài hơn, nhiều chi tiết | Tương đương |
| Thông tin mở rộng | Có (mô tả thuật toán FLARE đầy đủ) | Có (mức cơ bản) |
| **Winner** | **Hybrid** | - |

> **Nhận xét:** Hybrid trả lời chi tiết hơn, bao gồm cả 4 bước của thuật toán. Vector-only đúng nhưng ít chi tiết hơn.

### Câu 2: Ragas là gì? Các tiêu chí đánh giá RAG?

| Tiêu chí | Hybrid | Vector-only |
|----------|--------|-------------|
| Độ chính xác | ✅ 5 tiêu chí: Faithfulness, Answer Relevance, Context Relevance, Context Recall, Answer Similarity | ✅ Đúng |
| Ngắn gọn | Vừa phải | Ngắn hơn |
| Thông tin mở rộng | Có | Cơ bản |
| **Winner** | **Hybrid** | - |

> **Nhận xét:** Cả 2 đều chính xác. Hybrid liệt kê đầy đủ 5 metrics. Vector-only đề cập Context Precision/Recall nhưng bỏ qua Answer Similarity.

### Câu 3: Monitoring Trong Production quan tâm metric nào?

| Tiêu chí | Hybrid | Vector-only |
|----------|--------|-------------|
| Độ chính xác | ✅ 3 nhóm: System, RAG Quality, Cost | ✅ Tương tự |
| Ngắn gọn | Có cấu trúc rõ ràng | Có cấu trúc |
| Thông tin mở rộng | P50/P95/P99, token usage | Tương đương |
| **Winner** | **TIE** | **TIE** |

> **Nhận xét:** Cả 2 đều trả lời rất tốt, nội dung tương đương nhau.

### Câu 4: Liệt kê các mô hình embedding phổ biến?

| Tiêu chí | Hybrid | Vector-only |
|----------|--------|-------------|
| Độ chính xác | ✅ Đầy đủ: Classical, Transformer, Commercial, Open-source | ⚠️ Thiếu chi tiết (chỉ nhắc GloVe, FastText, BERT, MTEB) |
| Ngắn gọn | Dài hơn nhưng có cấu trúc | Ngắn hơn |
| Thông tin mở rộng | OpenAI, Cohere, Google, BGE, E5, Instructor, Jina | MTEB benchmark |
| **Winner** | **Hybrid** | - |

> **Nhận xét:** Hybrid đầy đủ hơn nhiều, liệt kê BGE, E5, Instructor, Jina, OpenAI text-embedding-3-small/large. Vector-only thiếu các mô hình quan trọng.

### Câu 5: Hybrid search là gì?

| Tiêu chí | Hybrid | Vector-only |
|----------|--------|-------------|
| Độ chính xác | ✅ Định nghĩa + RRF + ưu điểm từng phương pháp | ✅ Giống nội dung |
| Ngắn gọn | Vừa phải | Ngắn gọn hơn |
| Thông tin mở rộng | Ứng dụng RAG, vì sao retrieval quan trọng | Tương đương |
| **Winner** | **TIE** | **TIE** |

> **Nhận xét:** Cả 2 đều đúng và đầy đủ.

---

## 3. Bảng Tổng hợp Kết quả

| Tiêu chí | Hybrid | Vector-only |
|----------|:------:|:-----------:|
| Thời gian TB | 38.8s | **10.4s** ✅ |
| Độ liên quan Wins | **3/5** ✅ | 0/5 |
| Hoà | 2/5 | 2/5 |
| Điểm tổng thể | **Chất lượng cao hơn** | **Nhanh hơn 3.7×** |

---

## 4. Kết luận & Khuyến nghị

### 🏆 Về Thời gian phản hồi: **Vector-only thắng**
- Trung bình **10.4 giây** so với **38.8 giây** của Hybrid — nhanh hơn **3.7 lần**.
- Phù hợp cho các use case cần phản hồi tức thì, câu hỏi đơn giản.

### 🎯 Về Độ liên quan: **Hybrid thắng (3-0-2)**
- Hybrid cho câu trả lời **đầy đủ, chi tiết và phong phú hơn** ở 3/5 câu hỏi.
- Đặc biệt vượt trội ở câu hỏi yêu cầu liệt kê nhiều items (embedding models) và giải thích thuật toán.
- Hai câu hoà cho thấy Vector-only cũng đủ tốt với câu hỏi rõ nghĩa.

### 📌 Đề xuất cải thiện
1. **Dùng Vector-only cho câu hỏi ngắn** (< 20 từ, câu hỏi đơn khái niệm) → tiết kiệm ~30s.
2. **Dùng Hybrid cho câu hỏi phức tạp** (yêu cầu liệt kê, so sánh, đánh giá nhiều chiều) → kết quả tốt hơn.
3. **Tối ưu pipeline Hybrid:** Cân nhắc giảm số chunks retrieved trong KG pass để cải thiện latency.
4. **Async prefetch:** Chạy sparse + dense retrieval song song thay vì tuần tự sẽ cải thiện đáng kể tốc độ Hybrid.

---

## 5. Bằng chứng kiểm tra

![Vector-only Search - Kết quả cuối](file:///C:/Users/tuana/.gemini/antigravity/brain/2f69a4c2-a13c-4053-8132-f8d8428f9b0b/benchmark_vector_only_final_1774553401713.png)

![Hybrid Search - Recording](file:///C:/Users/tuana/.gemini/antigravity/brain/2f69a4c2-a13c-4053-8132-f8d8428f9b0b/benchmark_hybrid_search_1774552726527.webp)

![Vector-only Search - Recording](file:///C:/Users/tuana/.gemini/antigravity/brain/2f69a4c2-a13c-4053-8132-f8d8428f9b0b/benchmark_vector_only_search_1774553122872.webp)

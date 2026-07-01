#!/bin/bash
# harness_smoke.sh — shim tương thích. Nội dung thật đã chuyển vào harness/smoke.sh
# (component 'smoke' của hệ harness). Giữ file này để không phá vỡ tài liệu/tham chiếu cũ.
# Chạy trực tiếp:  bash harness_smoke.sh   |   Hoặc:  bash harness/run.sh smoke
exec bash "$(cd "$(dirname "$0")" && pwd)/harness/smoke.sh" "$@"

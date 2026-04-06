#!/bin/bash
# =============================================================
# Fix: Mismatch giữa approval_status và status trong processing tab
# Cách chạy: bash fix_status_mismatch.sh
# =============================================================

CONTAINER="nexusrag-postgres"
DB="nexusrag"
USER="postgres"

echo "=== [1] Kiểm tra docs bị kẹt PENDING + approved ==="
sudo docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c \
  "SELECT id, original_filename, status, approval_status FROM documents WHERE approval_status = 'approved' AND status = 'PENDING' ORDER BY id;"

echo ""
echo "=== [2] Chạy fix: đổi sang FAILED ==="
sudo docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c \
  "UPDATE documents SET status = 'FAILED', error_message = 'Processing stalled (server restart). Please re-upload.', updated_at = NOW() WHERE approval_status = 'approved' AND status = 'PENDING';"

echo ""
echo "=== [3] Kiểm tra docs rejected còn bị mismatch ==="
sudo docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c \
  "SELECT id, original_filename, status, approval_status FROM documents WHERE approval_status = 'rejected' AND status NOT IN ('REJECTED', 'FAILED');"

echo ""
echo "=== [4] Tổng quan sau fix ==="
sudo docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c \
  "SELECT status, approval_status, COUNT(*) as total FROM documents GROUP BY status, approval_status ORDER BY approval_status, status;"

echo ""
echo "=== Hoàn tất! Khởi động lại backend để áp dụng code fix ==="
echo "  tmux send-keys -t micco_be C-c Enter && cd /home/kms/MiccoRAG-v3/micco-backend && bash run_bk.sh"

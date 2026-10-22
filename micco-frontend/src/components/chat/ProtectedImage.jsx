import { useEffect, useState } from 'react';
import { ragDocumentsApi } from '../../utils/api';

export default function ProtectedImage({ image }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!image?.document_id || !image?.image_id) return;
    let active = true;
    let objectUrl = '';
    ragDocumentsApi.imageFile(image.document_id, image.image_id)
      .then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        if (!blob.type.startsWith('image/')) throw new Error('Định dạng ảnh không hợp lệ');
        objectUrl = URL.createObjectURL(blob);
        if (active) setUrl(objectUrl);
        else URL.revokeObjectURL(objectUrl);
      })
      .catch(() => { if (active) setError(true); });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [image?.document_id, image?.image_id]);

  if (error) return <span className="text-xs text-gray-400">Không thể tải ảnh nguồn.</span>;
  if (!url) return <span className="text-xs text-gray-400">Đang tải ảnh nguồn...</span>;
  return <img src={url} alt={image.caption || `Ảnh trang ${image.page_no || ''}`} className="max-w-full max-h-72 rounded-lg object-contain" />;
}

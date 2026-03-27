import { useRef } from 'react';
import { Upload } from 'lucide-react';

export default function UploadZone({ isDragging, onDragEnter, onDragLeave, onDragOver, onDrop, onFilesSelected }) {
    const fileInput = useRef(null);

    const handleClick = () => fileInput.current?.click();
    const handleFileInput = (e) => {
        onFilesSelected(e.target.files);
        e.target.value = '';
    };

    return (
        <div
            onDragEnter={onDragEnter}
            onDragLeave={onDragLeave}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onClick={handleClick}
            className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${isDragging ? 'border-primary-600 bg-primary-600/5' : 'border-gray-200 dark:border-gray-700 hover:border-primary-600/50'}`}
        >
            <div className="w-12 h-12 rounded-2xl bg-primary-600/10 flex items-center justify-center mx-auto mb-3">
                <Upload className={`w-6 h-6 transition-colors ${isDragging ? 'text-primary-600' : 'text-gray-400'}`} />
            </div>
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                {isDragging ? 'Thả tệp vào đây' : 'Kéo thả tệp hoặc nhấp để chọn'}
            </p>
            <p className="text-xs text-gray-400">PDF, DOCX, XLSX, PPTX, PNG, JPG, MD, ZIP — Tối đa 50MB</p>
            <input ref={fileInput} type="file" multiple className="hidden" onChange={handleFileInput} />
        </div>
    );
}

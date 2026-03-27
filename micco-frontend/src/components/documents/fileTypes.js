import {
    FileText, FileSpreadsheet, FileImage, File, FileArchive
} from 'lucide-react';

export const fileTypeIconMap = {
    PDF: FileText,
    DOCX: FileText,
    XLSX: FileSpreadsheet,
    PPTX: FileText,
    PNG: FileImage,
    JPG: FileImage,
    MP4: File,
    MD: File,
    ZIP: FileArchive,
};

export const fileTypeColors = {
    PDF:  'text-red-500',
    DOCX: 'text-blue-500',
    XLSX: 'text-green-500',
    PPTX: 'text-orange-500',
    PNG:  'text-purple-500',
    JPG:  'text-purple-500',
    MP4:  'text-pink-500',
    MD:   'text-gray-500',
    ZIP:  'text-yellow-600',
};

export const fileTypeBgColors = {
    PDF:  'bg-red-50 dark:bg-red-500/10',
    DOCX: 'bg-blue-50 dark:bg-blue-500/10',
    XLSX: 'bg-green-50 dark:bg-green-500/10',
    PPTX: 'bg-orange-50 dark:bg-orange-500/10',
    PNG:  'bg-purple-50 dark:bg-purple-500/10',
    JPG:  'bg-purple-50 dark:bg-purple-500/10',
    MP4:  'bg-pink-50 dark:bg-pink-500/10',
    MD:   'bg-gray-50 dark:bg-gray-500/10',
    ZIP:  'bg-yellow-50 dark:bg-yellow-500/10',
};

export const thumbnailBg = {
    PDF:  'from-amber-50 to-amber-100 border-amber-200',
    DOCX: 'from-blue-50 to-blue-100 border-blue-200',
    XLSX: 'from-green-50 to-green-100 border-green-200',
    PPTX: 'from-orange-50 to-orange-100 border-orange-200',
    PNG:  'from-purple-50 to-purple-100 border-purple-200',
    JPG:  'from-rose-50 to-rose-100 border-rose-200',
    MP4:  'from-pink-50 to-pink-100 border-pink-200',
    MD:   'from-slate-50 to-slate-100 border-slate-200',
    ZIP:  'from-teal-50 to-teal-100 border-teal-200',
};

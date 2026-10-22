// src/components/chat/ChatMessage.jsx
import { Bot, User, FileText, ExternalLink } from 'lucide-react';
import KnowledgeGraphPanel from './KnowledgeGraphPanel';
import { escapeHtml, sanitizeHtml } from '../../utils/sanitizeHtml';

// Nhận diện câu từ chối "không tìm thấy thông tin" của model một cách linh hoạt.
// Backend hiện có 2 chuỗi từ chối khác nhau (bất nhất, nên thống nhất ở lần sau):
//   1. Chuỗi dài trong chat_prompt.py:190 (không dùng trong luồng chat agentic thực tế) —
//      model không lặp lại nguyên văn mỗi lần, nên so khớp bằng vài cụm từ đặc trưng
//      (chữ thường) và yêu cầu khớp từ 2 cụm trở lên để tránh nhận nhầm câu trả lời bình thường.
//   2. Chuỗi thực tế đang phát ra trong luồng chat agentic: "Tài liệu không chứa thông tin..."
//      (chat_agent.py, rag.py) — nhận diện bằng cụm đặc trưng "tài liệu không chứa thông tin".
// File này là bản dead code (component thực tế đang dùng là src/pages/ChatAssistant.jsx),
// sửa đồng bộ để tránh lệch logic nếu sau này được dùng lại.
function isFallbackMessage(content) {
    if (!content) return false;
    const normalized = content.toLowerCase();
    const markers = [
        'không tìm thấy thông tin',
        'tài liệu hiện có',
        'kiểm tra lại từ khóa',
        'cung cấp thêm hồ sơ',
    ];
    const matchCount = markers.reduce((count, marker) => count + (normalized.includes(marker) ? 1 : 0), 0);
    return matchCount >= 2 || normalized.includes('tài liệu không chứa thông tin');
}

export default function ChatMessage({ msg }) {
    const isFallback = isFallbackMessage(msg.content);

    return (
        <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center ${msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gradient-to-br from-secondary-500 to-accent-500 text-white'
                    }`}>
                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div>
                    <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                        <div className="text-sm leading-relaxed whitespace-pre-line" dangerouslySetInnerHTML={{
                            __html: sanitizeHtml(escapeHtml(msg.content || '')
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br/>'))
                        }} />
                    </div>
                    {!isFallback && msg.sources && msg.sources.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            {msg.sources.map((source, i) => (
                                <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-medium bg-accent-500/10 text-accent-600 dark:bg-accent-500/20 dark:text-accent-400 cursor-pointer hover:bg-accent-500/20 transition-colors">
                                    <FileText className="w-3 h-3" />
                                    {source}
                                    <ExternalLink className="w-2.5 h-2.5" />
                                </span>
                            ))}
                        </div>
                    )}
                    {import.meta.env.DEV && msg.graph_data && (
                        <KnowledgeGraphPanel data={msg.graph_data} />
                    )}
                </div>
            </div>
        </div>
    );
}

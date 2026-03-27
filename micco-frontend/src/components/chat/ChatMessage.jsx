// src/components/chat/ChatMessage.jsx
import { Bot, User, FileText, ExternalLink } from 'lucide-react';
import KnowledgeGraphPanel from './KnowledgeGraphPanel';

export default function ChatMessage({ msg }) {
    const isFallback = msg.content?.includes("Dựa trên các tài liệu hiện có trong hệ thống, tôi không tìm thấy thông tin cụ thể về câu hỏi của bạn");

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
                            __html: msg.content
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br/>')
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

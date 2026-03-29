import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    Send, Bot, User, Loader2, X, Brain,
    ChevronDown, Trash2, FileText, ExternalLink,
    AlertCircle, Sparkles, RefreshCw, Database,
    Search, Cpu, CheckCircle2, ChevronRight,
    Settings, RotateCcw, Save, LayoutPanelLeft,
    Copy, Check
} from 'lucide-react';
import { workspacesApi, ragChatApi, ragDocumentsApi, readSSEStream } from '../utils/api';
import { useAuth } from '../context/AuthContext';

// ─── Default system prompt (mirror of backend DEFAULT_SYSTEM_PROMPT) ──────────
const DEFAULT_PROMPT = `Bạn là trợ lý AI chuyên nghiệp và hỗ trợ giải đáp các câu hỏi dựa trên tài liệu được cung cấp.

Mục tiêu chính:
- Trả lời CHÍNH XÁC, NGẮN GỌN và TRỰC TIẾP vào trọng tâm câu hỏi.
- Phân tích thông tin từ tài liệu được cung cấp, tuyệt đối không tự bịa thông tin.

Yêu cầu format:
- Viết thành các ĐOẠN VĂN có cấu trúc mạch lạc (như phong cách báo chí/văn xuôi).
- Ưu tiên sử dụng đoạn văn thay vì gạch đầu dòng (bullet points) trừ khi liệt kê quá 5 mục.
- Bắt buộc phải trích dẫn nguồn khi trích xuất dữ liệu từ context (Ví dụ: [doc:1], [doc:2]).

Bắt buộc:
1. Thông tin trả lời phải có trong phần "Tài liệu Context".
2. Nếu "Tài liệu Context" KHÔNG chứa bất cứ thông tin liên quan nào hỗ trợ trả lời, không cố gắng tạo ra câu trả lời. BẠN PHẢI TRẢ LỜI CHÍNH XÁC NGUYÊN VĂN CÂU DƯỚI ĐÂY, KHÔNG THÊM BỚT TỪ NÀO:
   "Dựa trên các tài liệu hiện có trong hệ thống, tôi không tìm thấy thông tin cụ thể về câu hỏi của bạn. Để đảm bảo tính chính xác, vui lòng kiểm tra lại từ khóa hoặc cung cấp thêm hồ sơ liên quan để tôi có thể hỗ trợ tốt hơn"
3. Tôn trọng ngôn ngữ của người dùng (nếu người dùng hỏi Tiếng Việt, hãy trả lời bằng Tiếng Việt).`;
// ─── System Prompt Editor Panel ───────────────────────────────────────────────
function SystemPromptPanel({ workspace, onClose, onSaved }) {
    const [draft, setDraft] = useState(workspace?.system_prompt || DEFAULT_PROMPT);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState('');

    const handleSave = async () => {
        if (!workspace) return;
        setSaving(true);
        setError('');
        try {
            const res = await workspacesApi.update(workspace.id, { system_prompt: draft.trim() || null });
            if (res.ok) {
                const updated = await res.json();
                setSaved(true);
                onSaved?.(updated);
                setTimeout(() => setSaved(false), 2000);
            } else {
                const body = await res.json().catch(() => ({}));
                setError(body.detail || `HTTP ${res.status}`);
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleReset = () => {
        setDraft(DEFAULT_PROMPT);
        setSaved(false);
        setError('');
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-end">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
            {/* Panel */}
            <div className="relative flex flex-col w-full max-w-xl bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-800 animate-slide-in-right">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                    <div>
                        <h2 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <Settings className="w-4 h-4 text-violet-500" />
                            System Prompt
                        </h2>
                        <p className="text-xs text-gray-400 mt-0.5">Workspace: <strong>{workspace?.name}</strong></p>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Info */}
                <div className="px-5 py-3 bg-violet-50 dark:bg-violet-500/10 border-b border-violet-100 dark:border-violet-500/20">
                    <p className="text-xs text-violet-700 dark:text-violet-300 leading-relaxed">
                        Prompt này định hướng cách AI trả lời câu hỏi trong workspace này. Để trống để dùng prompt mặc định của hệ thống.
                    </p>
                </div>

                {/* Editor */}
                <div className="flex-1 p-5 overflow-hidden flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Nội dung prompt</label>
                        <span className="text-xs text-gray-400">{draft.length} ký tự</span>
                    </div>
                    <textarea
                        value={draft}
                        onChange={e => { setDraft(e.target.value); setSaved(false); }}
                        className="flex-1 w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-xs font-mono text-gray-800 dark:text-gray-200 leading-relaxed resize-none outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-400 dark:focus:border-violet-500 transition-all"
                        placeholder="Nhập system prompt..."
                        style={{ minHeight: '320px' }}
                    />
                    {error && (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-xs text-red-600 dark:text-red-400">
                            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between gap-3 px-5 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                        <RotateCcw className="w-3.5 h-3.5" /> Đặt lại mặc định
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                            saved
                                ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30'
                                : 'bg-violet-600 hover:bg-violet-700 text-white shadow-sm'
                        } disabled:opacity-50`}
                    >
                        {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : saved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                        {saving ? 'Đang lưu...' : saved ? 'Đã lưu!' : 'Lưu prompt'}
                    </button>
                </div>
            </div>
        </div>
    );
}

function renderMarkdown(text, sources = []) {
    if (!text) return '';
    
    let mathBlocks = [];
    let html = text;

    // 1. Extract and render Math (Block and Inline)
    const hasKatex = typeof window !== 'undefined' && window.katex;

    // Block math: $$ ... $$
    html = html.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        if (!hasKatex) return match;
        try {
            const rendered = window.katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
            const id = `__MATH_BLOCK_${mathBlocks.length}__`;
            mathBlocks.push({ id, html: `<div class="katex-display-wrapper my-4 overflow-x-auto">${rendered}</div>` });
            return id;
        } catch (e) { return match; }
    });

    // Inline math: $ ... $
    html = html.replace(/\$([^\s\$][^\$]*?[^\s\$])\$/g, (match, formula) => {
        if (!hasKatex) return match;
        try {
            const rendered = window.katex.renderToString(formula, { displayMode: false, throwOnError: false });
            const id = `__MATH_INLINE_${mathBlocks.length}__`;
            mathBlocks.push({ id, html: `<span class="katex-inline">${rendered}</span>` });
            return id;
        } catch (e) { return match; }
    });

    // 2. Table handling (Basic Markdown table)
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = '';
    let processedLines = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        // Check if line looks like a table row (has at least one | and isn't just a separator)
        if (line.includes('|')) {
            if (!inTable) {
                inTable = true;
                tableHtml = '<div class="table-container my-3 overflow-x-auto border border-gray-100 dark:border-gray-800 rounded-lg shadow-sm"><table class="min-w-full text-xs text-left text-gray-700 dark:text-gray-300 border-collapse">';
            }
            
            // Refined cell splitting: remove empty first/last elements if they were caused by leading/trailing pipes
            let cells = line.split('|').map(c => c.trim());
            if (cells[0] === '') cells.shift();
            if (cells[cells.length - 1] === '') cells.pop();
            
            // Skip separator row if it exists
            if (line.includes('---') || line.match(/^[|\s:-]+$/)) {
                continue;
            }

            const isHeader = !tableHtml.includes('<tbody>');
            if (isHeader && !tableHtml.includes('<thead>')) {
                tableHtml += '<thead><tr class="bg-gray-50/80 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">';
                cells.forEach(c => tableHtml += `<th class="px-4 py-2 font-bold text-gray-900 dark:text-white">${c}</th>`);
                tableHtml += '</tr></thead><tbody>';
            } else {
                tableHtml += '<tr class="border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">';
                cells.forEach(c => tableHtml += `<td class="px-4 py-2">${c}</td>`);
                tableHtml += '</tr>';
            }
        } else {
            if (inTable) {
                tableHtml += '</tbody></table></div>';
                processedLines.push(tableHtml);
                inTable = false;
                tableHtml = '';
            }
            processedLines.push(lines[i]);
        }
    }
    if (inTable) {
        tableHtml += '</tbody></table></div>';
        processedLines.push(tableHtml);
    }
    html = processedLines.join('\n');

    // 3. Standard Markdown formatting
    html = html
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-[10px] font-mono text-pink-600 dark:text-pink-400">$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre class="my-2 p-3 rounded-xl bg-gray-100 dark:bg-gray-800 text-[10px] font-mono overflow-x-auto border border-gray-200 dark:border-gray-700"><code>$1</code></pre>')
        .replace(/^#{3}\s+(.+)$/gm, (match, p1) => `<h3 id="h3-${p1}" class="font-black text-xs mt-3 mb-1 text-gray-900 dark:text-white uppercase tracking-wider">${p1}</h3>`)
        .replace(/^#{2}\s+(.+)$/gm, (match, p1) => `<h2 id="h2-${p1}" class="font-black text-sm mt-4 mb-1.5 text-gray-900 dark:text-white uppercase tracking-wider">${p1}</h2>`)
        .replace(/^#{1}\s+(.+)$/gm, (match, p1) => `<h1 id="h1-${p1}" class="font-black text-base mt-5 mb-2 text-gray-900 dark:text-white uppercase tracking-wider">${p1}</h1>`)
        .replace(/^[\-\*]\s+(.+)$/gm, '<li class="ml-4 list-disc text-gray-700 dark:text-gray-300">$1</li>')
        .replace(/(<li.*<\/li>)/gs, '<ul class="my-1.5 space-y-0.5">$1</ul>');

    // 4. Newline to Paragraphs
    let paragraphs = html.split(/\n\n+/);
    html = paragraphs.map(p => {
        if (p.startsWith('<') && (p.includes('<h') || p.includes('<pre') || p.includes('<ul') || p.includes('<div') || p.includes('<table'))) {
            return p;
        }
        return `<p class="mb-1 last:mb-0">${p.replace(/\n/g, '<br/>')}</p>`;
    }).join('\n');

    // 5. Inline citations replacement
    if (sources && sources.length > 0) {
        html = html.replace(/\[([a-zA-Z0-9_\-\.:\?]+)\]/g, (match, p1) => {
            const src = sources.find(s => s.index === p1 || s.formatted === p1 || s.source_file === p1 || `doc:${s.document_id}` === p1);
            if (src) {
                return `<button type="button" class="citation inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 text-[10px] font-bold rounded bg-emerald-100/80 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-500/40 transition-colors cursor-pointer align-baseline ring-1 ring-emerald-200 dark:ring-emerald-500/30" data-source-id="${src.document_id}" data-index="${src.index || ''}" title="Nguồn: ${src.source_file || src.formatted || src.document_id}">[${p1}]</button>`;
            }
            return match;
        });
    }

    // 6. Restore math placeholders
    mathBlocks.forEach(block => {
        html = html.replace(block.id, block.html);
    });

    return `<div class="markdown-content">${html}</div>`;
}



function renderPreviewMarkdown(text, highlightText) {
    let html = renderMarkdown(text);
    if (highlightText) {
        // Create a safe snippet for regex matching (first 40-50 chars of the actual text content)
        const cleanSnippet = highlightText.replace(/\n/g, ' ').trim();
        const snippet = cleanSnippet.substring(0, 50).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (snippet.length > 10) {
            const regex = new RegExp(`(${snippet}[^<]*)`, 'i');
            html = html.replace(regex, `<mark id="highlight-target" class="bg-emerald-200/60 dark:bg-emerald-500/40 text-inherit rounded-sm py-0.5">$1</mark>`);
        }
    }
    return html;
}

// ─── Reasoning Steps ──────────────────────────────────────────────────────────
const STEP_CONFIG = {
    analyzing: {
        label: 'Đang phân tích câu hỏi...',
        icon: Brain,
        color: 'text-violet-500',
        bg: 'bg-violet-50 dark:bg-violet-500/10',
    },
    retrieving: {
        label: 'Đang truy vấn cơ sở kiến thức...',
        icon: Search,
        color: 'text-blue-500',
        bg: 'bg-blue-50 dark:bg-blue-500/10',
    },
    generating: {
        label: 'Đang tạo câu trả lời...',
        icon: Cpu,
        color: 'text-emerald-500',
        bg: 'bg-emerald-50 dark:bg-emerald-500/10',
    },
    done: {
        label: 'Hoàn thành',
        icon: CheckCircle2,
        color: 'text-gray-400',
        bg: 'bg-gray-50 dark:bg-gray-800/50',
    },
};

function ReasoningSteps({ steps, currentStep, detail }) {
    if (!steps.length && !currentStep) return null;
    const allSteps = ['analyzing', 'retrieving', 'generating'];
    const completedSteps = allSteps.slice(0, allSteps.indexOf(currentStep));

    return (
        <div className="flex flex-col gap-1.5 mb-2">
            {/* Completed steps — greyed out */}
            {completedSteps.map(s => {
                const cfg = STEP_CONFIG[s];
                const Icon = cfg.icon;
                return (
                    <div key={s} className="flex items-center gap-2 text-xs text-gray-400">
                        <CheckCircle2 className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
                        <span className="line-through opacity-60">{cfg.label}</span>
                    </div>
                );
            })}

            {/* Current active step */}
            {currentStep && STEP_CONFIG[currentStep] && (() => {
                const cfg = STEP_CONFIG[currentStep];
                const Icon = cfg.icon;
                return (
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-xl ${cfg.bg} border border-current/10`}>
                        <Icon className={`w-4 h-4 ${cfg.color} animate-pulse flex-shrink-0`} />
                        <div className="flex-1 min-w-0">
                            <p className={`text-xs font-semibold ${cfg.color}`}>{cfg.label}</p>
                            {detail && <p className="text-xs text-gray-400 truncate mt-0.5">{detail}</p>}
                        </div>
                        <div className="flex gap-0.5 ml-2">
                            {[0, 1, 2].map(i => (
                                <div
                                    key={i}
                                    className={`w-1.5 h-1.5 rounded-full ${cfg.color.replace('text-', 'bg-')} opacity-75`}
                                    style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
                                />
                            ))}
                        </div>
                    </div>
                );
            })()}
        </div>
    );
}

// ─── Thinking Block ───────────────────────────────────────────────────────────
function ThinkingBlock({ text }) {
    const [expanded, setExpanded] = useState(false);
    if (!text) return null;
    return (
        <div className="mb-2">
            <button
                onClick={() => setExpanded(v => !v)}
                className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-violet-500 transition-colors"
            >
                <Brain className="w-3.5 h-3.5" />
                <span>Quá trình suy nghĩ</span>
                <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? 'rotate-90' : ''}`} />
            </button>
            {expanded && (
                <div className="mt-1.5 px-3 py-2 rounded-xl bg-violet-50 dark:bg-violet-500/10 border border-violet-200 dark:border-violet-500/30 text-xs text-violet-700 dark:text-violet-300 font-mono leading-relaxed max-h-40 overflow-y-auto">
                    {text}
                </div>
            )}
        </div>
    );
}

// ─── Chat Message ─────────────────────────────────────────────────────────────
function ChatMessage({ msg, onSourceClick }) {
    const isUser = msg.role === 'user';
    const isFallback = msg.content?.includes("Dựa trên các tài liệu hiện có trong hệ thống, tôi không tìm thấy thông tin cụ thể về câu hỏi của bạn");
    const isStreaming = msg.streaming;
    const sources = msg.sources || [];
    const relatedEntities = msg.related_entities || [];
    const reasoningStep = msg.reasoningStep;
    const reasoningDetail = msg.reasoningDetail;
    const thinking = msg.thinking;
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        if (!msg.content) return;
        navigator.clipboard.writeText(msg.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={`flex gap-3 group/msg ${isUser ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                isUser ? 'bg-primary-600' : 'bg-gradient-to-br from-violet-500 to-purple-600'
            }`}>
                {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
            </div>

            <div className={`max-w-[82%] space-y-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>

                {/* Reasoning steps (AI only, while streaming) */}
                {!isUser && isStreaming && (
                    <ReasoningSteps
                        steps={[]}
                        currentStep={reasoningStep}
                        detail={reasoningDetail}
                    />
                )}

                {/* Thinking block */}
                {!isUser && thinking && <ThinkingBlock text={thinking} />}

                {/* Bubble */}
                {(msg.content || !isStreaming) && (
                    <div className="flex flex-col gap-1 w-full relative">
                        <div className={`rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                            isUser
                                ? 'bg-primary-600 text-white rounded-tr-sm'
                                : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-sm shadow-sm'
                        }`}>
                            {isUser ? (
                                <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                            ) : (
                                <div className="flex items-start gap-1.5">
                                    <div 
                                        onClick={(e) => {
                                            const btn = e.target.closest('button.citation');
                                            if (btn && onSourceClick) {
                                                const docId = btn.getAttribute('data-source-id');
                                                const idx = btn.getAttribute('data-index');
                                                const src = sources.find(s => String(s.document_id) === docId && s.index === idx) || sources.find(s => String(s.document_id) === docId);
                                                if (src) onSourceClick(src);
                                            }
                                        }}
                                        dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content, msg.sources) || '' }} 
                                    />
                                    {isStreaming && msg.content && (
                                        <span className="inline-block w-1 h-4 bg-primary-500 dark:bg-secondary-400 animate-pulse rounded-full ml-1 flex-shrink-0 mt-0.5" />
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Actions — Visible on hover */}
                        {!isUser && !isStreaming && msg.content && (
                            <div className="flex items-center gap-1 opacity-0 group-hover/msg:opacity-100 transition-opacity absolute top-0 -right-8">
                                <button
                                    onClick={handleCopy}
                                    className={`p-1.5 rounded-lg border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:shadow-sm transition-all ${copied ? 'text-emerald-500 border-emerald-100' : ''}`}
                                    title="Copy"
                                >
                                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Sources Collapsible */}
                {!isUser && sources.length > 0 && !isStreaming && !isFallback && (
                    <div className="w-full mt-1.5">
                        <details className="group border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-800/50 overflow-hidden shadow-sm">
                            <summary className="flex items-center justify-between px-3 py-2 cursor-pointer bg-emerald-50/50 dark:bg-gray-800 hover:bg-emerald-50 dark:hover:bg-gray-750 transition-colors select-none">
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                    <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-400">
                                        Tìm thấy {sources.length} nguồn
                                    </span>
                                </div>
                                <ChevronDown className="w-4 h-4 text-gray-400 group-open:rotate-180 transition-transform" />
                            </summary>
                            <div className="p-2 space-y-1 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800">
                                {sources.map((src, i) => (
                                    <button 
                                        key={i} 
                                        onClick={() => onSourceClick && onSourceClick(src)} 
                                        className="w-full text-left text-xs px-3 py-2.5 rounded-lg bg-gray-50 dark:bg-gray-800/80 border border-gray-100 dark:border-gray-700/50 text-gray-700 dark:text-gray-300 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200 dark:hover:bg-emerald-500/10 dark:hover:text-emerald-400 dark:hover:border-emerald-500/30 transition-colors flex items-start gap-2.5"
                                    >
                                        <FileText className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 opacity-60 text-emerald-600 dark:text-emerald-500" />
                                        <div className="flex flex-col min-w-0">
                                            <span className="font-medium line-clamp-1">
                                                {typeof src === 'string' ? src : (src.source_file || src.formatted || `[${src.index}] Tài liệu ${src.document_id}`)}
                                            </span>
                                            {typeof src !== 'string' && src.heading_path && src.heading_path.length > 0 && (
                                                <span className="text-[10px] text-gray-400 dark:text-gray-500 truncate mt-0.5" title={src.heading_path.join(' > ')}>
                                                    ↳ {src.heading_path.join(' > ')}
                                                </span>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </details>
                    </div>
                )}

                {/* Related entities */}
                {!isUser && relatedEntities.length > 0 && !isStreaming && !isFallback && (
                    <div className="flex flex-wrap gap-1.5">
                        {relatedEntities.slice(0, 6).map((e, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-400">
                                {typeof e === 'string' ? e : e.name || JSON.stringify(e)}
                            </span>
                        ))}
                    </div>
                )}

                {/* Timestamp */}
                {msg.created_at && (
                    <p className="text-xs text-gray-400 px-1">
                        {new Date(msg.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                )}
            </div>
        </div>
    );
}

    // ─── Main Component ───────────────────────────────────────────────────────────
export default function ChatAssistant() {
    // Workspaces
    const [workspaces, setWorkspaces] = useState([]);
    const [selectedWs, setSelectedWs] = useState(null);
    const [wsLoading, setWsLoading] = useState(true);
    const [showWsDropdown, setShowWsDropdown] = useState(false);
    const [showPromptPanel, setShowPromptPanel] = useState(false);
    const [previewDoc, setPreviewDoc] = useState(null);

    const { user } = useAuth();
    const isAdmin = user?.role === 'Admin';

    // Chat
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [sending, setSending] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);

    // Options
    const [mode, setMode] = useState('hybrid');
    const [clearConfirm, setClearConfirm] = useState(false);

    // Suggested questions
    const [suggestedQuestions, setSuggestedQuestions] = useState([
        'Phân tích rủi ro & cơ hội?', 
        'Chiến lược hành động cốt lõi', 
        'Đánh giá hiệu quả hệ thống', 
        'Tối ưu hóa quy trình hiện tại'
    ]);
    const [suggestionsLoading, setSuggestionsLoading] = useState(false);


    const scrollContainerRef = useRef(null);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // ─── Load workspaces ──────────────────────────────────────────────────────
    useEffect(() => {
        (async () => {
            setWsLoading(true);
            try {
                const res = await workspacesApi.list();
                if (res.ok) {
                    const data = await res.json();
                    setWorkspaces(data);
                    if (data.length > 0) setSelectedWs(data[0]);
                }
            } catch { /* connection error */ } finally {
                setWsLoading(false);
            }
        })();
    }, []);

    // ─── Load history when workspace changes ──────────────────────────────────
    useEffect(() => {
        if (!selectedWs) { 
            setMessages([]); 
            return; 
        }
        loadHistory(selectedWs.id);
        loadSuggestedQuestions(selectedWs.id);
        
        // Non-admins forced to use workspace default search mode
        if (!isAdmin && selectedWs.search_mode) {
            setMode(selectedWs.search_mode);
        }
    }, [selectedWs?.id, isAdmin]);

    const loadSuggestedQuestions = async (wsId) => {
        setSuggestionsLoading(true);
        try {
            const res = await workspacesApi.getSuggestedQuestions(wsId);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    setSuggestedQuestions(data);
                }
            }
        } catch { /* use default */ } finally {
            setSuggestionsLoading(false);
        }
    };


    const loadHistory = async (wsId) => {
        setHistoryLoading(true);
        setMessages([]);
        try {
            const res = await ragChatApi.history(wsId);
            if (res.ok) {
                const data = await res.json();
                const mapped = (data.messages || []).map(m => ({
                    id: m.message_id || m.id,
                    role: m.role,
                    content: m.content,
                    sources: m.sources || [],
                    related_entities: m.related_entities || [],
                    thinking: m.thinking || null,
                    created_at: m.created_at,
                }));
                setMessages(mapped);
            }
        } catch { /* silent */ } finally {
            setHistoryLoading(false);
        }
    };

    // ─── Auto-scroll ──────────────────────────────────────────────────────────
    const scrollToBottom = () => {
        if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // ─── Send message (streaming SSE) ─────────────────────────────────────────
    const handleSend = useCallback(async () => {
        const text = input.trim();
        if (!text || !selectedWs || sending) return;

        setInput('');
        setSending(true);

        // Optimistic user message
        const userMsg = { id: `u-${Date.now()}`, role: 'user', content: text };
        setMessages(prev => [...prev, userMsg]);

        // Placeholder AI message (streaming) — starts with analyzing step
        const aiId = `a-${Date.now()}`;
        setMessages(prev => [...prev, {
            id: aiId,
            role: 'assistant',
            content: '',
            streaming: true,
            reasoningStep: 'analyzing',
            reasoningDetail: '',
            thinking: '',
        }]);

        let accContent = '';
        let accThinking = '';
        let finalSources = [];
        let finalEntities = [];

        const updateMsg = (patch) => {
            setMessages(prev => prev.map(m => m.id === aiId ? { ...m, ...patch } : m));
        };

        try {
            const res = await ragChatApi.streamChat(selectedWs.id, text, { mode });

            await readSSEStream(res, {
                onChunk: (chunk) => {
                    const { event, type } = chunk;
                    const evtType = event || type;

                    if (evtType === 'status') {
                        // {step: "analyzing"|"retrieving"|"generating", detail: str}
                        updateMsg({
                            reasoningStep: chunk.step || chunk.data?.step,
                            reasoningDetail: chunk.detail || chunk.data?.detail || '',
                        });
                    } else if (evtType === 'thinking') {
                        // {text: str}
                        accThinking += chunk.text || chunk.data?.text || '';
                        updateMsg({ thinking: accThinking });
                    } else if (evtType === 'token') {
                        // {text: str}
                        accContent += chunk.text || chunk.data?.text || '';
                        updateMsg({ content: accContent });
                    } else if (evtType === 'token_rollback') {
                        // Speculative tokens cancelled — clear content
                        accContent = '';
                        updateMsg({ content: '' });
                    } else if (evtType === 'sources') {
                        finalSources = chunk.sources || chunk.data?.sources || [];
                    } else if (evtType === 'images') {
                        // image_refs — ignore for now
                    } else if (evtType === 'complete') {
                        const d = chunk.data || chunk;
                        if (d.answer) accContent = d.answer;
                        finalSources = d.sources || finalSources;
                        finalEntities = d.related_entities || [];
                        if (d.thinking) accThinking = d.thinking;
                        updateMsg({
                            content: accContent,
                            thinking: accThinking || null,
                            sources: finalSources,
                            related_entities: finalEntities,
                        });
                    } else if (evtType === 'error') {
                        const errMsg = chunk.message || chunk.data?.message || 'Lỗi không xác định';
                        updateMsg({ content: `⚠️ ${errMsg}` });
                    } else if (chunk.raw) {
                        accContent += chunk.raw;
                        updateMsg({ content: accContent });
                    }
                },
                onDone: () => {
                    setMessages(prev => prev.map(m => m.id === aiId
                        ? {
                            ...m,
                            streaming: false,
                            reasoningStep: null,
                            sources: finalSources,
                            related_entities: finalEntities,
                            thinking: accThinking || null,
                            created_at: new Date().toISOString(),
                          }
                        : m
                    ));
                    setSending(false);
                },
                onError: (err) => {
                    console.error('Stream error:', err);
                    setMessages(prev => prev.map(m => m.id === aiId
                        ? { ...m, streaming: false, reasoningStep: null, content: accContent || '⚠️ Có lỗi xảy ra. Vui lòng thử lại.', sources: [] }
                        : m
                    ));
                    setSending(false);
                },
            });
        } catch (err) {
            // Fallback: non-streaming
            try {
                const res = await ragChatApi.chat(selectedWs.id, text, { mode });
                if (res.ok) {
                    const data = await res.json();
                    const answerContent = data.answer || data.content || data.message || JSON.stringify(data);
                    setMessages(prev => prev.map(m => m.id === aiId
                        ? { ...m, streaming: false, reasoningStep: null, content: answerContent, sources: data.sources || [], related_entities: data.related_entities || [], created_at: new Date().toISOString() }
                        : m
                    ));
                } else {
                    throw new Error(`HTTP ${res.status}`);
                }
            } catch (fallbackErr) {
                setMessages(prev => prev.map(m => m.id === aiId
                    ? { ...m, streaming: false, reasoningStep: null, content: '⚠️ Không thể kết nối tới MiccoRAG-v2 server. Kiểm tra VITE_RAGV2_BASE_URL trong .env.' }
                    : m
                ));
            }
            setSending(false);
        }
    }, [input, selectedWs, sending, mode]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    // ─── Clear history ────────────────────────────────────────────────────────
    const handleClear = async () => {
        if (!selectedWs) return;
        try {
            await ragChatApi.clearHistory(selectedWs.id);
            setMessages([]);
        } catch { /* silent */ }
        setClearConfirm(false);
    };

    // ─── Document Preview ─────────────────────────────────────────────────────
    const handleSourceClick = async (src) => {
        if (!src || typeof src === 'string' || !src.document_id) return;
        
        const docName = src.source_file || src.formatted || `Document ${src.document_id}`;
        
        // Always update TargetText to scroll/highlight again if clicking a different chunk in same doc
        setPreviewDoc(prev => ({
            id: src.document_id,
            name: docName,
            loading: prev?.id !== src.document_id, // skip loading if same doc
            content: prev?.id === src.document_id ? prev.content : '',
            targetText: src.content
        }));

        if (previewDoc && previewDoc.id === src.document_id) return;

        try {
            const res = await ragDocumentsApi.markdown(src.document_id);
            if (res.ok) {
                const textData = await res.text();
                setPreviewDoc(prev => (prev?.id === src.document_id ? {
                    ...prev,
                    loading: false,
                    content: textData || 'Tài liệu rỗng.'
                } : prev));
            } else {
                setPreviewDoc(prev => (prev?.id === src.document_id ? {
                    ...prev,
                    loading: false,
                    content: `⚠️ Không thể tải nội dung (HTTP ${res.status}).`
                } : prev));
            }
        } catch (e) {
            setPreviewDoc(prev => (prev?.id === src.document_id ? {
                ...prev,
                loading: false,
                content: `⚠️ Lỗi mạng: ${e.message}`
            } : prev));
        }
    };

    // Auto-scroll to highlighted text when preview doc loads
    useEffect(() => {
        if (previewDoc && !previewDoc.loading && previewDoc.targetText) {
            setTimeout(() => {
                const target = document.getElementById('highlight-target');
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 150);
        }
    }, [previewDoc?.content, previewDoc?.loading, previewDoc?.targetText]);

    // Parse TOC from markdown
    const previewToc = useMemo(() => {
        if (!previewDoc || !previewDoc.content) return [];
        const lines = previewDoc.content.split('\n');
        const headers = [];
        lines.forEach(line => {
            const match = line.match(/^(#{1,3})\s+(.+)$/);
            if (match) {
                headers.push({ level: match[1].length, text: match[2], id: `h${match[1].length}-${match[2]}` });
            }
        });
        return headers;
    }, [previewDoc?.content]);

    // ─── Render ───────────────────────────────────────────────────────────────
    return (
        <div className="flex flex-col lg:flex-row h-full bg-white dark:bg-gray-900 overflow-hidden relative p-2 lg:p-3 gap-3">
            
            {/* ─── Left Pane (Chat Zone) ─── */}
            <div className={`flex flex-col h-full bg-gray-50 dark:bg-gray-950 transition-all duration-300 ease-in-out ${
                previewDoc ? 'w-full lg:w-1/2 lg:border-r border-gray-200 dark:border-gray-800' : 'w-full'
            } ${previewDoc ? 'hidden lg:flex' : 'flex'}`}>

                {/* ─── Header ─── */}
                <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between flex-shrink-0 rounded-t-2xl">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md flex-shrink-0">
                        <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-base font-bold text-gray-900 dark:text-white">Micco AI Chat</h1>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Workspace Selector */}
                    <div className="relative">
                        <button
                            onClick={() => setShowWsDropdown(v => !v)}
                            className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors max-w-[150px]"
                        >
                            <Database className="w-3 h-3 text-gray-400 flex-shrink-0" />
                            <span className="truncate">{wsLoading ? '...' : (selectedWs?.name || 'Chọn')}</span>
                            <ChevronDown className="w-3 h-3 text-gray-400 flex-shrink-0" />
                        </button>
                        {showWsDropdown && (
                            <div className="absolute top-full right-0 mt-1 w-52 bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-800 z-50 overflow-hidden">
                                {workspaces.length === 0 ? (
                                    <p className="text-xs text-gray-400 px-3 py-2">Chưa có workspace — tạo trong trang Tài liệu</p>
                                ) : workspaces.map(ws => (
                                    <button
                                        key={ws.id}
                                        onClick={() => { setSelectedWs(ws); setShowWsDropdown(false); }}
                                        className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm transition-colors ${
                                            selectedWs?.id === ws.id
                                                ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-secondary-400'
                                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                                        }`}
                                    >
                                        <Database className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                                        <span className="flex-1 truncate text-left">{ws.name}</span>
                                        <span className="text-xs opacity-50">{ws.document_count}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Mode selector - Admin only */}
                    {isAdmin && (
                        <select
                            value={mode}
                            onChange={e => setMode(e.target.value)}
                            className="text-xs px-2 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 outline-none"
                        >
                            <option value="hybrid">Hybrid</option>
                            <option value="vector_only">Vector only</option>
                            <option value="graph_only">Graph only</option>
                        </select>
                    )}

                    {/* System Prompt Settings - Admin only */}
                    {selectedWs && isAdmin && (
                        <button
                            onClick={() => setShowPromptPanel(true)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-violet-600 hover:bg-violet-50 dark:hover:text-violet-400 dark:hover:bg-violet-500/10 transition-colors"
                            title="Chỉnh sửa System Prompt"
                        >
                            <Settings className="w-4 h-4" />
                        </button>
                    )}

                    {/* Clear */}
                    {messages.length > 0 && !clearConfirm && (
                        <button
                            onClick={() => setClearConfirm(true)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                            title="Xóa lịch sử"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    )}
                    {clearConfirm && (
                        <div className="flex items-center gap-2 text-xs bg-red-50 dark:bg-red-500/10 px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-800">
                            <span className="text-red-600 dark:text-red-400 font-medium">Xóa lịch sử?</span>
                            <button onClick={handleClear} className="text-red-600 dark:text-red-400 font-bold hover:underline">Có</button>
                            <button onClick={() => setClearConfirm(false)} className="text-gray-500 hover:underline">Không</button>
                        </div>
                    )}
                </div>
            </div>

            {/* ─── Messages Area ─── */}
            <div 
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-950 scroll-smooth relative custom-scrollbar"
            >
                <div className="max-w-4xl mx-auto w-full flex flex-col p-4 lg:p-6 pb-20">
                    {/* No workspace */}
                    {!wsLoading && workspaces.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20 gap-3 text-center animate-fade-in-up">
                            <Database className="w-10 h-10 text-gray-200 dark:text-gray-700" />
                            <p className="text-xs font-bold text-gray-500 dark:text-gray-400">Chưa có workspace nào</p>
                        </div>
                    )}

                    {/* History loading */}
                    {historyLoading && (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
                        </div>
                    )}

                    {/* Welcome / Initial Chat Landing */}
                    {!historyLoading && messages.length === 0 && selectedWs && (
                        <div className="flex flex-col items-center justify-center py-12 text-center animate-fade-in-up">
                            <div className="w-16 h-16 rounded-3xl bg-primary-600 flex items-center justify-center shadow-xl shadow-primary-600/20 mb-6 group hover:scale-110 transition-transform duration-500">
                                <Brain className="w-8 h-8 text-white group-hover:rotate-12 transition-transform" />
                            </div>
                            <h3 className="text-lg font-black text-gray-900 dark:text-white mb-1">
                                Chat với "{selectedWs.name}"
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-8 max-w-sm mx-auto">
                                {selectedWs.document_count > 0
                                    ? `${selectedWs.indexed_count || 0}/${selectedWs.document_count} tài liệu đã xử lý — sẵn sàng`
                                    : 'Tải lên tài liệu để bắt đầu'}
                            </p>
                            {/* Suggestion chips */}
                            <div className="flex flex-wrap justify-center gap-2 max-w-md">
                                {suggestionsLoading ? (
                                    <div className="flex items-center gap-2 text-[10px] text-gray-400">
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                        Đang tạo gợi ý...
                                    </div>
                                ) : suggestedQuestions.map((q, i) => (
                                    <button
                                        key={q}
                                        onClick={() => setInput(q)}
                                        className="px-4 py-2 rounded-full border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-[11px] font-bold text-gray-600 dark:text-gray-400 hover:border-primary-400 hover:text-primary-600 dark:hover:border-primary-500 dark:hover:text-primary-400 hover:shadow-md transition-all animate-fade-in-up"
                                        style={{ animationDelay: `${i * 0.1}s` }}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>

                        </div>
                    )}

                    {/* Messages List */}
                    <div className="space-y-4">
                        {messages.map(msg => (
                            <div key={msg.id} className="animate-fade-in-up">
                                <ChatMessage msg={msg} onSourceClick={handleSourceClick} />
                            </div>
                        ))}
                    </div>

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* ─── Input Area (Footer) ─── */}
            {selectedWs && (
                <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200 dark:border-gray-800 p-3 lg:p-4 flex-shrink-0 rounded-b-2xl">
                    <div className="max-w-4xl mx-auto w-full">
                        <div className="flex items-center justify-between mb-2 px-1">
                            {!historyLoading && messages.length > 0 && (
                                <button
                                    onClick={() => loadHistory(selectedWs.id)}
                                    className="flex items-center gap-1 text-[10px] uppercase font-bold text-gray-400 hover:text-primary-600 transition-colors"
                                >
                                    <RefreshCw className="w-2.5 h-2.5" /> Làm mới
                                </button>
                            )}
                            <span className="text-[10px] uppercase font-bold text-gray-400 ml-auto">
                                Enter để gửi · Shift+Enter xuống dòng
                            </span>
                        </div>
                        
                        <div className="flex items-end gap-2 relative group">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={`Hỏi về tài liệu trong "${selectedWs.name}"...`}
                                disabled={sending}
                                rows={1}
                                style={{ resize: 'none', minHeight: '42px', maxHeight: '100px' }}
                                className="flex-1 w-full px-4 py-2.5 pr-12 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 text-sm text-gray-800 dark:text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all disabled:opacity-60 shadow-sm"
                                onInput={e => {
                                    e.target.style.height = '42px';
                                    e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
                                }}
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || sending}
                                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0 shadow-sm ${
                                    input.trim() && !sending 
                                        ? 'bg-primary-600 text-white hover:bg-primary-700 active:scale-95' 
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                                }`}
                            >
                                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            
            </div> {/* End Left Pane */}

            {/* ─── Right Pane (Preview Doc) ─── */}
            {previewDoc && (
                <div className="w-full lg:w-1/2 h-full flex flex-col bg-white dark:bg-gray-900 animate-slide-in-right z-10 lg:z-auto absolute lg:relative inset-0 lg:inset-auto">
                    {/* Header */}
                    <div className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800 px-5 py-3.5 flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center gap-2 overflow-hidden">
                            <LayoutPanelLeft className="w-4 h-4 text-primary-500 flex-shrink-0" />
                            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
                                {previewDoc.name}
                            </h3>
                        </div>
                        <button 
                            onClick={() => setPreviewDoc(null)} 
                            className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition flex-shrink-0"
                            title="Đóng bản xem trước"
                        >
                            <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </button>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 flex overflow-hidden">
                        
                        {/* TOC Sidebar */}
                        <div className="w-48 xl:w-56 flex-shrink-0 bg-gray-50/30 dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 overflow-y-auto p-4 hidden md:block">
                            <h4 className="text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3">Mục lục</h4>
                            {previewToc.length === 0 && !previewDoc.loading && (
                                <p className="text-xs text-gray-400 italic">Không có mục lục.</p>
                            )}
                            <ul className="space-y-1.5">
                                {previewToc.map((h, i) => (
                                    <li key={i} style={{ paddingLeft: `${(h.level - 1) * 8}px` }}>
                                        <button 
                                            onClick={() => document.getElementById(h.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                                            className="text-left w-full text-xs text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 line-clamp-2 transition-colors focus:outline-none"
                                        >
                                            {h.text}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Document Content */}
                        <div className="flex-1 overflow-y-auto p-5 xl:p-8 text-sm leading-relaxed text-gray-800 dark:text-gray-300 scroll-smooth">
                            {previewDoc.loading ? (
                                <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-400">
                                    <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
                                    <span>Đang tải nội dung tài liệu...</span>
                                </div>
                            ) : previewDoc.content ? (
                                <div 
                                    className="prose dark:prose-invert prose-sm max-w-none"
                                    dangerouslySetInnerHTML={{ __html: renderPreviewMarkdown(previewDoc.content, previewDoc.targetText) }} 
                                />
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-400">
                                    <FileText className="w-8 h-8 opacity-20" />
                                    <span className="italic">Không có nội dung.</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Close dropdown overlay */}
            {showWsDropdown && (
                <div className="fixed inset-0 z-40" onClick={() => setShowWsDropdown(false)} />
            )}

            {/* System Prompt Editor Panel */}
            {showPromptPanel && selectedWs && (
                <SystemPromptPanel
                    workspace={selectedWs}
                    onClose={() => setShowPromptPanel(false)}
                    onSaved={(updatedWs) => {
                        // Update workspace list to reflect new prompt
                        setWorkspaces(prev => prev.map(w => w.id === updatedWs.id ? updatedWs : w));
                        setSelectedWs(updatedWs);
                    }}
                />
            )}
        </div>
    );
}

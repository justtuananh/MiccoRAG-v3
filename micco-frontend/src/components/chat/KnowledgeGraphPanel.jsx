// web/src/components/chat/KnowledgeGraphPanel.jsx
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

const TYPE_COLORS = {
    Supplier:  'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    Contract:  'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    Invoice:   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    Material:  'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
    Country:   'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
    Origin:    'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
};
const DEFAULT_COLOR = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';

/**
 * Dev-only Knowledge Graph panel rendered below an AI chat message.
 * data shape: { nodes: [{id, label, type}], edges: [{from, to, relation}] }
 *
 * Gated externally by `import.meta.env.DEV && msg.graph_data` in ChatMessage.jsx.
 * Note: Vite tree-shakes the entire module from production builds because the
 * only call site is behind `import.meta.env.DEV` (a build-time constant).
 * Use dynamic import only if you need to verify this with bundle analysis.
 */
export default function KnowledgeGraphPanel({ data }) {
    const [open, setOpen] = useState(false);

    return (
        <div className="mt-2 border border-indigo-200 dark:border-indigo-800 rounded-lg overflow-hidden text-xs">
            <button
                onClick={() => setOpen(!open)}
                aria-expanded={open}
                className="w-full flex items-center gap-1.5 px-3 py-2 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors"
            >
                {open
                    ? <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
                    : <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
                }
                🔗 Đồ thị tri thức
                <span className="ml-auto text-indigo-400 dark:text-indigo-500 font-normal">
                    {data.nodes.length} nodes · {data.edges.length} edges
                </span>
            </button>

            {open && (
                <div className="px-3 py-2.5 space-y-3 bg-white dark:bg-gray-900">
                    {/* Nodes */}
                    <div>
                        <p className="text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide text-[10px] font-semibold">
                            Thực thể
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                            {data.nodes.map((node) => (
                                <span
                                    key={node.id}
                                    title={node.type}
                                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[node.type] ?? DEFAULT_COLOR}`}
                                >
                                    {node.label}
                                    <span className="opacity-60 text-[10px]">{node.type}</span>
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Edges */}
                    {data.edges.length > 0 && (
                        <div>
                            <p className="text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide text-[10px] font-semibold">
                                Quan hệ
                            </p>
                            <ul className="space-y-0.5 text-gray-600 dark:text-gray-400 font-mono">
                                {data.edges.map((edge, i) => (
                                    <li key={i}>
                                        <span className="text-indigo-500 dark:text-indigo-400">{edge.from}</span>
                                        {' → '}
                                        <span className="text-amber-500 dark:text-amber-400">{edge.relation}</span>
                                        {' → '}
                                        <span className="text-indigo-500 dark:text-indigo-400">{edge.to}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

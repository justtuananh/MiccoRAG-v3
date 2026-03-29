// GraphKnowledge.jsx - Knowledge Graph visualization (renamed from Knowledge.jsx)
// This file contains the original Knowledge graph visualization
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import {
    BookOpen, Database, ChevronDown, AlertTriangle,
    Link as LinkIcon, Hash, Search, Loader2, Maximize2, ZoomIn, ZoomOut
} from 'lucide-react';
import { workspacesApi, ragGraphApi } from '../utils/api';

const ENTITY_COLORS = {
    Person: '#3b82f6',       // Blue
    Organization: '#22c55e', // Green
    Location: '#eab308',     // Yellow
    Event: '#f97316',        // Orange
    Concept: '#a855f7',      // Purple
    Date: '#ef4444',         // Red
    Technology: '#ec4899',   // Pink
    Method: '#06b6d4',       // Cyan
    Dataset: '#8b5cf6',      // Violet
    Product: '#14b8a6',      // Teal
    Article: '#f43f5e',      // Rose
    Industry: '#84cc16',     // Lime
    Unknown: '#9ca3af'       // Gray
};

export default function GraphKnowledge() {
    const [workspaces, setWorkspaces] = useState([]);
    const [selectedWs, setSelectedWs] = useState(null);
    const [showWsDropdown, setShowWsDropdown] = useState(false);

    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [windowSize, setWindowSize] = useState({ width: 800, height: 600 });
    const containerRef = useRef(null);
    const fgRef = useRef();

    // ─── Theme Observer ─────────────────────────────────────────────────────
    const [isDarkMode, setIsDarkMode] = useState(() => document.documentElement.classList.contains('dark'));

    useEffect(() => {
        const observer = new MutationObserver(() => {
            setIsDarkMode(document.documentElement.classList.contains('dark'));
        });
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    // ─── Fetch Workspaces ──────────────────────────────────────────────────
    useEffect(() => {
        workspacesApi.list()
            .then(res => res.ok ? res.json() : [])
            .then(data => {
                setWorkspaces(data);
                if (data.length > 0) {
                    setSelectedWs(data[0]);
                }
            })
            .catch(() => {});
    }, []);

    // ─── Responsive Graph Container ─────────────────────────────────────────
    useEffect(() => {
        const updateSize = () => {
            if (containerRef.current) {
                setWindowSize({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };
        updateSize();
        window.addEventListener('resize', updateSize);
        return () => window.removeEventListener('resize', updateSize);
    }, []);

    // ─── Fetch Graph Data ───────────────────────────────────────────────────
    useEffect(() => {
        if (!selectedWs) return;

        let isMounted = true;
        setLoading(true);
        setError(null);
        setGraphData({ nodes: [], links: [] });

        ragGraphApi.getGraph(selectedWs.id)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (!isMounted) return;

                const nodes = (data.nodes || []).map(entry => ({
                    id: entry.id,
                    name: entry.label,
                    type: entry.entity_type || 'Unknown',
                    val: entry.degree ? Math.max(1, Math.min(entry.degree / 2, 20)) : 1,
                    rawDegree: entry.degree || 0,
                    color: ENTITY_COLORS[entry.entity_type] || ENTITY_COLORS.Unknown
                }));

                const links = (data.edges || []).map(edge => ({
                    source: edge.source,
                    target: edge.target,
                    name: edge.label,
                    weight: edge.weight || 1
                }));

                const nodeIds = new Set(nodes.map(n => n.id));
                const validLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));

                const graph = { nodes, links: validLinks };

                setGraphData(graph);

                setTimeout(() => {
                    if (fgRef.current && isMounted) {
                         fgRef.current.zoomToFit(400, 50);
                    }
                }, 500);

            })
            .catch(err => {
                if (!isMounted) return;
                setError("Không thể lấy sơ đồ tri thức. " + err.message);
            })
            .finally(() => {
                if (isMounted) setLoading(false);
            });

        return () => { isMounted = false; };
    }, [selectedWs]);

    // ─── Calculate Legends & Stats ──────────────────────────────────────────
    const stats = useMemo(() => {
        const typeCount = {};
        const sortedEntities = [...graphData.nodes].sort((a, b) => b.rawDegree - a.rawDegree).slice(0, 10);

        graphData.nodes.forEach(n => {
            typeCount[n.type] = (typeCount[n.type] || 0) + 1;
        });

        const legendItems = Object.entries(typeCount)
            .sort((a, b) => b[1] - a[1])
            .map(([type, count]) => ({
                type,
                count,
                color: ENTITY_COLORS[type] || ENTITY_COLORS.Unknown
            }));

        return { legendItems, topEntities: sortedEntities, totalNodes: graphData.nodes.length, totalLinks: graphData.links.length };
    }, [graphData]);

    // ─── Tweak Physics ──────────────────────────────────────────────────────
    useEffect(() => {
        if (fgRef.current && graphData.nodes.length > 0) {
            fgRef.current.d3Force('charge').strength(-40);
            fgRef.current.d3Force('link').distance(15);
        }
    }, [graphData]);

    // ─── Graph Interaction ──────────────────────────────────────────────────
    const [highlightNodes, setHighlightNodes] = useState(new Set());
    const [highlightLinks, setHighlightLinks] = useState(new Set());
    const [hoverNode, setHoverNode] = useState(null);

    const handleNodeHover = useCallback(node => {
        setHighlightNodes(new Set());
        setHighlightLinks(new Set());

        if (node) {
            const hNodes = new Set();
            const hLinks = new Set();
            hNodes.add(node);

            graphData.links.forEach(link => {
                if (link.source.id === node.id || link.target.id === node.id) {
                    hLinks.add(link);
                    hNodes.add(link.source);
                    hNodes.add(link.target);
                }
            });

            setHighlightNodes(hNodes);
            setHighlightLinks(hLinks);
        }

        setHoverNode(node || null);
    }, [graphData]);

    const handleNodeClick = useCallback(node => {
        if (fgRef.current && node) {
            fgRef.current.centerAt(node.x, node.y, 1000);
            fgRef.current.zoom(4, 1000);
        }
    }, []);

    // Paint node
    const paintNode = useCallback((node, ctx, globalScale) => {
        const isHighlighted = highlightNodes.has(node);
        const radius = Math.sqrt(node.val) * 4;

        if (hoverNode === node) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.color;
            ctx.globalAlpha = 0.3;
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
        ctx.fillStyle = highlightNodes.size > 0 && !isHighlighted ? 'rgba(150,150,150,0.1)' : node.color;
        ctx.fill();

        if (highlightNodes.size === 0 || isHighlighted) {
            ctx.strokeStyle = isDarkMode ? '#111827' : '#ffffff';
            ctx.lineWidth = 1 / globalScale;
            ctx.stroke();
        }

        if (globalScale > 1.5 || isHighlighted) {
            const label = node.name;
            const fontSize = isHighlighted ? 12/globalScale : 11/globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            if (highlightNodes.size > 0 && !isHighlighted) {
                ctx.fillStyle = isDarkMode ? 'rgba(150,150,150,0.3)' : 'rgba(156, 163, 175, 0.4)';
            } else {
                ctx.fillStyle = isDarkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(17, 24, 39, 0.85)';
            }

            ctx.fillText(label, node.x, node.y + radius + (8 / globalScale));
        }
    }, [hoverNode, highlightNodes, isDarkMode]);

    // Paint Link
    const paintLink = useCallback((link, ctx, globalScale) => {
        const isHighlighted = highlightLinks.has(link);

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);

        if (isHighlighted) {
            ctx.strokeStyle = isDarkMode ? 'rgba(156, 163, 175, 0.8)' : 'rgba(75, 85, 99, 0.8)';
        } else {
            ctx.strokeStyle = isDarkMode ? 'rgba(55, 65, 81, 0.4)' : 'rgba(209, 213, 219, 0.7)';
        }

        ctx.lineWidth = isHighlighted ? 2 / globalScale : 1 / globalScale;
        ctx.stroke();
    }, [highlightLinks, isDarkMode]);


    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 overflow-hidden relative p-2 lg:p-3 gap-3">

            {/* Top Bar */}
            <div className="bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-2 flex items-center justify-between shrink-0 shadow-sm">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-sm">
                        <BookOpen className="w-4 h-4 text-white" />
                    </div>
                    <h1 className="text-sm font-bold text-gray-900 dark:text-white tracking-wide">Đồ thị tri thức</h1>
                </div>

                <div className="flex items-center gap-3">
                    {/* Workspace Selector */}
                    <div className="relative">
                        <button
                            onClick={() => setShowWsDropdown(v => !v)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors min-w-[180px] shadow-sm"
                        >
                            <Database className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                            <span className="truncate flex-1 text-left font-medium">{selectedWs?.name || 'Chọn Workspace'}</span>
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                        </button>
                        {showWsDropdown && (
                            <div className="absolute top-full right-0 mt-1 w-60 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-800 z-50 overflow-hidden">
                                {workspaces.length === 0 ? (
                                    <p className="text-xs text-gray-500 px-4 py-3">Chưa có workspace</p>
                                ) : workspaces.map(ws => (
                                    <button
                                        key={ws.id}
                                        onClick={() => { setSelectedWs(ws); setShowWsDropdown(false); }}
                                        className={`w-full flex items-center gap-3 px-3 py-2.5 text-xs transition-colors ${
                                            selectedWs?.id === ws.id
                                                ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
                                        }`}
                                    >
                                        <Database className={`w-3.5 h-3.5 flex-shrink-0 ${selectedWs?.id === ws.id ? 'text-primary-500 opacity-100' : 'opacity-60'}`} />
                                        <span className="flex-1 truncate text-left">{ws.name}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Graph Area */}
            <div className="flex-1 relative flex bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden shadow-sm" ref={containerRef}>
                {loading ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm z-20">
                        <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-3" />
                        <p className="text-gray-600 dark:text-gray-400 font-medium text-sm">Đang trích xuất đồ thị tri thức...</p>
                    </div>
                ) : error ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
                        <div className="w-14 h-14 rounded-2xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center mb-3">
                            <AlertTriangle className="w-6 h-6 text-red-500" />
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 max-w-md text-center text-sm">{error}</p>
                    </div>
                ) : graphData.nodes.length === 0 ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
                        <Database className="w-10 h-10 text-gray-300 dark:text-gray-700 mb-3" />
                        <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Chưa có dữ liệu đồ thị tri thức cho workspace này.</p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Vui lòng upload tài liệu và xử lý RAG.</p>
                    </div>
                ) : (
                    <>
                        {/* Main Graph Component */}
                        <ForceGraph2D
                            ref={fgRef}
                            width={windowSize.width}
                            height={windowSize.height}
                            graphData={graphData}
                            nodeLabel={node => `<div class="bg-white/95 dark:bg-gray-900/95 text-gray-900 dark:text-white px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 shadow-xl backdrop-blur-md font-sans text-xs">
                                <div class="font-bold mb-0.5">${node.name}</div>
                                <div class="flex items-center gap-1.5 opacity-80 text-[10px] text-gray-500 dark:text-gray-400">
                                    <div class="w-1.5 h-1.5 rounded-full" style="background-color: ${node.color}"></div>
                                    <span class="uppercase font-semibold tracking-wider">${node.type}</span>
                                </div>
                            </div>`}
                            nodeColor={node => node.color}
                            nodeCanvasObject={paintNode}
                            linkCanvasObject={paintLink}
                            linkColor={() => isDarkMode ? 'rgba(55, 65, 81, 0.4)' : 'rgba(209, 213, 219, 0.7)'}
                            linkWidth={1}
                            linkDirectionalParticles={1}
                            linkDirectionalParticleWidth={1.5}
                            linkDirectionalParticleSpeed={0.005}
                            linkCurvature={0.2}
                            onNodeHover={handleNodeHover}
                            onNodeClick={handleNodeClick}
                            d3AlphaDecay={0.05}
                            d3VelocityDecay={0.4}
                            cooldownTicks={100}
                        />

                        {/* Instruction Overlay */}
                        <div className="absolute top-3 left-3 z-10 pointer-events-none">
                            <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-3 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm pointer-events-auto">
                                <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-1.5 flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
                                    <BookOpen className="w-3.5 h-3.5 text-primary-500" />
                                    Hướng dẫn
                                </h3>
                                <div className="space-y-1 text-[10px] text-gray-500 dark:text-gray-400">
                                    <p className="flex items-center gap-1.5"><span>🖱️</span> Lăn chuột để Zoom</p>
                                    <p className="flex items-center gap-1.5"><span>👆</span> Click & Kéo nền để di chuyển</p>
                                    <p className="flex items-center gap-1.5"><span>🎯</span> Click vào Node để Focus</p>
                                    <p className="flex items-center gap-1.5"><span>✨</span> Hover vào Node để xem chi tiết</p>
                                </div>
                            </div>
                        </div>

                        {/* Controls Overlay */}
                        <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
                            <button onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 1.2, 400)} className="w-8 h-8 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-700 transition-colors shadow-sm focus:outline-none">
                                <ZoomIn className="w-4 h-4" />
                            </button>
                            <button onClick={() => fgRef.current?.zoom(fgRef.current.zoom() / 1.2, 400)} className="w-8 h-8 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-700 transition-colors shadow-sm focus:outline-none">
                                <ZoomOut className="w-4 h-4" />
                            </button>
                            <button onClick={() => fgRef.current?.zoomToFit(400, 50)} className="w-8 h-8 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 flex items-center justify-center text-gray-500 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-700 transition-colors shadow-sm mt-1 focus:outline-none" title="Vừa toàn bộ màn hình">
                                <Maximize2 className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Interactive Legend (Bottom Left) */}
                        <div className="absolute bottom-4 left-4 flex flex-wrap gap-2 z-10 max-w-2xl pointer-events-none">
                            {stats.legendItems.slice(0, 8).map(item => (
                                <div key={item.type} className="flex items-center gap-1.5 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm px-2.5 py-1 rounded-md border border-gray-200 dark:border-gray-800 pointer-events-auto shadow-sm">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400">{item.type}</span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Bottom Panels (Stats & Top Entities) - Only show if data exists */}
            {!loading && graphData.nodes.length > 0 && (
                <div className="h-52 shrink-0 flex gap-2 lg:gap-3 z-10">

                    {/* Type Distribution Panel */}
                    <div className="flex-1 min-w-[300px] border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 rounded-xl p-4 flex flex-col shadow-sm">
                        <div className="flex items-center justify-between mb-3 border-b border-gray-200 dark:border-gray-800 pb-2">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                                <Hash className="w-3.5 h-3.5 text-primary-500" />
                                Thành phần Đồ thị
                            </h3>
                            <span className="text-[10px] font-bold text-gray-500 dark:text-gray-500 uppercase tracking-wider">{stats.totalNodes} Thực thể · {stats.totalLinks} Liên kết</span>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-wrap gap-2 content-start pr-1">
                             {stats.legendItems.map(item => (
                                 <div key={item.type} className="flex items-center gap-2 w-[calc(50%-0.5rem)] mb-1 bg-white dark:bg-gray-900 px-2 py-1.5 rounded-lg border border-gray-100 dark:border-gray-800">
                                     <div className="w-2 h-2 rounded-full shadow-inner" style={{ backgroundColor: item.color }} />
                                     <span className="textxs font-medium text-gray-600 dark:text-gray-400 capitalize truncate flex-1" title={item.type}>{item.type}</span>
                                     <span className="text-xs font-bold text-gray-900 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-center">{item.count}</span>
                                 </div>
                             ))}
                        </div>
                    </div>

                    {/* Top Entities Panel */}
                    <div className="flex-1 min-w-[300px] border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 rounded-xl p-4 flex flex-col shadow-sm">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300 flex items-center gap-1.5 mb-3 border-b border-gray-200 dark:border-gray-800 pb-2">
                            <LinkIcon className="w-3.5 h-3.5 text-emerald-500" />
                            Thực thể Trọng tâm
                        </h3>

                        <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1.5 pr-2">
                            {stats.topEntities.map((entity, i) => (
                                <div key={entity.id} className="flex items-center justify-between group bg-white dark:bg-gray-900 px-3 py-1.5 rounded-lg border border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 transition-colors">
                                    <div className="flex items-center gap-2.5 overflow-hidden">
                                        <span className="text-[10px] font-black text-gray-400 dark:text-gray-600 w-3">{i + 1}</span>
                                        <span className="text-xs text-gray-800 dark:text-gray-200 font-medium truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors cursor-default" title={entity.name}>
                                            {entity.name}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                                        <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-500">{entity.type}</span>
                                        <span className="text-xs font-mono bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded font-bold w-6 text-center">{entity.rawDegree}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
}

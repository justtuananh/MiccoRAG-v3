# Hướng dẫn Hiển thị Knowledge Graph trong Frontend

## 1. Các công nghệ/thư viện phổ biến nhất

Khi xây dựng giao diện hiển thị Knowledge Graph trong các ứng dụng Frontend hiện đại (như React, Vue), dưới đây là các thư viện được sử dụng rộng rãi nhất:

1. **react-force-graph (Đề xuất hàng đầu)**
   - **Đặc điểm:** Tối ưu cực tốt, render bằng HTML Canvas (2D) hoặc WebGL (3D), hỗ trợ cả VR/AR.
   - **Ưu điểm:** Dễ tích hợp với React, hiệu năng mượt mà kể cả với đồ thị hàng ngàn node.
2. **Cytoscape.js (`react-cytoscapejs`)**
   - **Đặc điểm:** Thư viện cực kì mạnh mẽ cho phân tích mạng lưới và thuật toán hệ đồ thị.
   - **Ưu điểm:** Style giống CSS, nhiều tính năng chuyên sâu.
3. **D3.js (`d3-force`)**
   - **Đặc điểm:** Tiêu chuẩn vàng của Data Visualization.
   - **Ưu điểm:** Tùy biến mọi chi tiết từ đường nét tới animation, nhưng học rất khó khi ghép với React.
4. **AntV G6 (Alibaba)**
   - **Đặc điểm:** Framework rất mạnh phục vụ vẽ Graph/Flow.
   - **Ưu điểm:** Tương tác mặc định rất tốt, giao diện gốc đẹp.
5. **Sigma.js**
   - **Đặc điểm:** Chuyên trị các đồ thị cực kì lớn (hàng triệu nodes/edges) thông qua WebGL.

---

## 2. Hướng dẫn xây dựng thực tế với `react-force-graph-2d`

Vì dự án của bạn đang dùng **Vite + React**, `react-force-graph` là sự lựa chọn tối ưu nhất và cân bằng giữa hiệu suất lẫn độ dễ tùy chỉnh.

### Bước 1: Cài đặt thư viện

Bạn cần mở terminal ở thư mục `frontend` và chạy lệnh:

```bash
npm install react-force-graph-2d
```

### Bước 2: Chuẩn bị định dạng dữ liệu (Data Structure)

Dữ liệu đồ thị luôn cần hai mảng chính: `nodes` (các đỉnh) và `links` (các cạnh nối). Bạn cần đảm bảo API trả về hoặc format data dưới dạng sau:

```json
{
  "nodes": [
    { "id": "User_1", "name": "Nguyễn Văn A", "group": "person" },
    { "id": "Doc_1", "name": "Báo cáo Q1", "group": "document" },
    { "id": "Topic_1", "name": "Tài chính", "group": "concept" }
  ],
  "links": [
    { "source": "User_1", "target": "Doc_1", "label": "Tạo bởi" },
    { "source": "Doc_1", "target": "Topic_1", "label": "Thuộc chủ đề" }
  ]
}
```

### Bước 3: Tạo Component hiển thị

Tạo file `KnowledgeGraph.jsx` (hoặc `KnowledgeGraph.tsx` tùy bạn dùng JS hay TS) với nội dung mẫu bao gồm **chỉnh màu theo group**, **hiệu ứng hover làm sáng node liên quan**, và **focus camera khi click**:

```tsx
import React, { useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

// 1. Dữ liệu giả lập
const mockData = {
  nodes: [
    { id: '1', name: 'Công ty A', group: 'company' },
    { id: '2', name: 'Nhân viên B', group: 'person' },
    { id: '3', name: 'Dự án C', group: 'project' }
  ],
  links: [
    { source: '1', target: '2', label: 'WORK_FOR' },
    { source: '2', target: '3', label: 'PARTICIPATE_IN' },
    { source: '1', target: '3', label: 'OWN' }
  ]
};

export default function KnowledgeGraph() {
  const fgRef = useRef();
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());

  // 2. Action: Focus camera vào node khi click (Zoom & Center)
  const handleNodeClick = useCallback((node) => {
    // Di chuyển tới node, zoom 4x, animation diễn ra trong 1000ms
    fgRef.current.centerAt(node.x, node.y, 1000);
    fgRef.current.zoom(4, 1000);
  }, []);

  // 3. Action: Hover chuột làm nổi bật đường đi và node liên quan
  const handleNodeHover = (node) => {
    highlightNodes.clear();
    highlightLinks.clear();
    
    if (node) {
      highlightNodes.add(node);
      mockData.links.forEach((link: any) => {
        if (link.source.id === node.id || link.target.id === node.id) {
          highlightLinks.add(link);
          highlightNodes.add(link.source);
          highlightNodes.add(link.target);
        }
      });
    }

    setHighlightNodes(new Set(highlightNodes));
    setHighlightLinks(new Set(highlightLinks));
  };

  // 4. Utils: Xác định màu sắc Node dựa trên Group
  const getNodeColor = (node) => {
    // Nếu đang hover 1 node khác và node này không liên quan -> làm mờ
    if (highlightNodes.size > 0 && !highlightNodes.has(node)) return 'rgba(150,150,150,0.1)'; 
    
    switch(node.group) {
        case 'company': return '#ff7675';
        case 'person': return '#74b9ff';
        case 'project': return '#55efc4';
        default: return '#dfe6e9';
    }
  };

  return (
    <div style={{ width: '100%', height: '100vh', background: '#1e1e1e', position: 'relative' }}>
      <ForceGraph2D
        ref={fgRef}
        graphData={mockData}
        
        // Cấu hình node
        nodeLabel="name"
        nodeColor={getNodeColor as any}
        nodeRelSize={6}
        
        // Cấu hình link (cạnh / mối quan hệ)
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        linkColor={(link: any) => highlightLinks.has(link) ? '#ffeb3b' : 'rgba(255,255,255,0.2)'}
        linkWidth={(link: any) => highlightLinks.has(link) ? 3 : 1}
        
        // Bắt sự kiện
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover as any}

        // 5. Tùy chỉnh nâng cao: Tự vẽ text hiển thị đính kèm ngay trên node bằng Canvas
        nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
          const label = node.name;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;

          // Vẽ hình tròn cho node
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fillStyle = getNodeColor(node);
          ctx.fill();

          // Chỉ hiển thị chữ nếu zoom cận cảnh để giao diện không bị rối chữ
          if (globalScale > 1.5) {
             ctx.textAlign = 'center';
             ctx.textBaseline = 'middle';
             ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
             ctx.fillText(label, node.x, node.y + 8);
          }
        }}
      />
      
      {/* 6. Lớp overlay hiển thị thông tin hướng dẫn */}
      <div style={{ position: 'absolute', top: 20, left: 20, color: 'white', background: 'rgba(0,0,0,0.6)', padding: '15px', borderRadius: '8px' }}>
        <h3>Knowledge Graph</h3>
        <p>🖱️ Lăn chuột để Zoom</p>
        <p>🖱️ Click & Kéo nền để di chuyển (Pan)</p>
        <p>🖱️ Click vào một Node để Focus</p>
      </div>
    </div>
  );
}
```

## 3. Quá trình tích hợp (Integration)
Ở môi trường thực tế như trong folder `frontend` để nhận dữ liệu từ hệ thống RAG:
1. Bạn import component này vào trang hiển thị / hoặc thẻ Tab `Knowledge Graph` ở Sidebar.
2. Dùng `useEffect` kết hợp `fetch` gọi API để kéo dữ liệu từ Graph Database (ex: Neo4j) với endpoint như `/api/v1/rag/graph/{id}`.
3. Map dữ liệu nhận được thành 2 mảng `nodes` và `links`, sau đó gắn vào state `graphData={your_fetched_data}`.
4. Nếu lượng Node quá lớn và màn hình 2D bị chậm, đổi `<ForceGraph2D />` thành `<ForceGraph3D />` với cùng API truyền vào để tận dụng độ mượt của WebGL.

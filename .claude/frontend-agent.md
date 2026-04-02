# Frontend Developer Agent - Instructions

## Role
Bạn là **Frontend Developer Agent** chịu trách nhiệm phát triển và bảo trì frontend code trong project MiccoRAG-v3.

## Working Directory
```
/home/kms/MiccoRAG-v3/micco-frontend
```

## Core Responsibilities

### 1. UI/UX Development
- React components với functional components + hooks
- Responsive design (mobile-first approach)
- Modern CSS với Tailwind CSS
- Animations và transitions mượt mà

### 2. API Integration
- Gọi API qua Next.js route handlers (không gọi trực tiếp từ browser)
- Streaming response với ReadableStream/EventSource
- Error handling với retry logic
- Loading states và skeletons

### 3. State Management
- React Context cho global state
- TanStack Query cho server state
- Local state với useState/useReducer

### 4. Component Library
- shadcn/ui components
- Custom components theo design system
- Reusable utility functions

## Collaboration Protocol

### Khi nhận task từ User:
1. **Analyze**: Đọc kỹ yêu cầu, xác định frontend components cần thay đổi
2. **Plan**: Liệt kê components cần modify/create
3. **Coordinate**: Nếu cần backend API changes, thông báo cho backend-dev agent
4. **Implement**: Code theo React best practices
5. **Test**: Manual testing + check console errors
6. **Report**: Báo cáo tiến độ

### Khi backend-dev cần frontend support:
1. Đợi API contract/documentation
2. Implement API call layer
3. Update UI components
4. Notify backend-dev khi testing xong

## Component Structure
```
src/
├── components/
│   ├── admin/
│   ├── chat/
│   ├── dashboard/
│   ├── documents/
│   ├── document-view/
│   ├── landing/
│   └── shared/
├── pages/
│   ├── Admin.jsx
│   ├── Dashboard.jsx
│   ├── Login.jsx
│   └── Landing.jsx
├── context/
├── hooks/
├── services/    # API calls
└── utils/
```

## API Integration Pattern
```javascript
// API service example
export const chatService = {
  sendMessage: async (message, conversationId) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    return response.json();
  },

  streamMessage: async (message, onChunk) => {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, stream: true }),
    });
    // Handle streaming response
  }
};
```

## Tech Stack
- Vite + React 18
- React Router
- TanStack Query
- Tailwind CSS
- shadcn/ui
- React Dropzone (file upload)
- Recharts (charts)

## Commands
```bash
# Run frontend dev
cd /home/kms/MiccoRAG-v3/micco-frontend && npm run dev

# Build for production
cd /home/kms/MiccoRAG-v3/micco-frontend && npm run build

# Lint check
cd /home/kms/MiccoRAG-v3/micco-frontend && npm run lint

# Type check
cd /home/kms/MiccoRAG-v3/micco-frontend && npm run type-check
```

## UI Guidelines

### Chat Interface
- Hiển thị streaming response
- Show sources/documents khi có
- Loading skeleton khi fetch
- Error boundary cho error handling

### File Upload
- Drag & drop với react-dropzone
- Accept: PDF, DOCX, TXT
- Max file size: 50MB
- Progress bar khi upload
- Preview sau khi upload thành công

### Responsive Breakpoints
```css
/* Mobile first */
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
```

## Quality Standards
- ESLint rules passed
- No console errors
- Responsive trên mọi breakpoint
- Loading states cho mọi async operation
- Toast notifications cho errors

## Communication
- Log all API calls
- Report UI bugs immediately
- Coordinate với backend-dev về API changes

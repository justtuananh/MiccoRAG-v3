# Frontend Rules (Next.js)

## Stack
- Next.js 14+ App Router
- TypeScript strict mode
- Tailwind CSS
- shadcn/ui components
- Tanstack Query cho data fetching

## Chat UI
- Streaming: dùng EventSource hoặc fetch với ReadableStream
- Message format: {role: "user"|"assistant", content: string, sources?: Source[]}
- Luôn show loading skeleton khi đang fetch

## API Calls
- Mọi call qua /api/ Next.js route handlers (không call FastAPI trực tiếp từ browser)
- Error boundary cho mọi page
- Toast notification cho errors

## File Upload
- Drag & drop với react-dropzone
- Chỉ accept: PDF, DOCX, TXT
- Show progress bar khi upload
- Max 50MB client-side validation

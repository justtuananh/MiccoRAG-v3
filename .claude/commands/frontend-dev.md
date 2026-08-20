---
description: Phát triển frontend code trong micco-frontend
---

## Frontend Development Workflow

### Working Directory
```
/home/kms/micco/micco-frontend
```

### Development Steps

1. **Understand Requirements**
   - Đọc yêu cầu từ user
   - Check existing component structure
   - Identify components cần modify/create

2. **Component Development**
   ```
   1. Create/update component
   2. Add TypeScript types
   3. Add error handling
   4. Add loading states
   5. Test manually
   ```

3. **Code Standards**
   - Functional components + hooks
   - TypeScript strict mode
   - Tailwind CSS classes
   - camelCase naming

4. **File Structure**
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
   ├── context/
   ├── hooks/
   ├── services/
   └── utils/
   ```

### Common Tasks

#### Create new component
```jsx
// src/components/new-component/NewComponent.jsx
import { useState } from 'react';

export function NewComponent({ prop1, onAction }) {
  const [loading, setLoading] = useState(false);

  const handleAction = async () => {
    setLoading(true);
    try {
      await onAction();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="...">
      {/* Component content */}
    </div>
  );
}
```

#### Add API integration
```javascript
// src/services/api.js
export const apiService = {
  async callEndpoint(data) {
    const response = await fetch('/api/v1/endpoint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('API Error');
    }

    return response.json();
  },

  async streamEndpoint(data, onChunk) {
    // Streaming implementation
  }
};
```

### Commands
```bash
# Run dev server
cd /home/kms/micco/micco-frontend && npm run dev

# Build
cd /home/kms/micco/micco-frontend && npm run build

# Lint
cd /home/kms/micco/micco-frontend && npm run lint

# Type check
cd /home/kms/micco/micco-frontend && npm run type-check
```

### Testing
```bash
# Unit tests
cd /home/kms/micco/micco-frontend && npm run test

# With coverage
cd /home/kms/micco/micco-frontend && npm run test:coverage

# E2E tests
cd /home/kms/micco/micco-frontend && npm run test:e2e
```

### UI Guidelines

#### Loading States
```jsx
{loading ? (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded"></div>
  </div>
) : (
  <Content />
)}
```

#### Error Handling
```jsx
{error && (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
    {error}
  </div>
)}
```

### Checklist trước khi complete task
- [ ] Component follows design system
- [ ] TypeScript types defined
- [ ] Error handling in place
- [ ] Loading states shown
- [ ] Responsive on all breakpoints
- [ ] No console errors
- [ ] API integration working
- [ ] ESLint passed

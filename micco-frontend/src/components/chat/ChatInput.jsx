// src/components/chat/ChatInput.jsx
import { Send } from 'lucide-react';

export default function ChatInput({ input, loading, onInputChange, onSubmit, onPromptClick, showPrompts, prompts }) {
    return (
        <>
            {/* Example Prompts */}
            {showPrompts && (
                <div className="px-6 pb-3">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">Hãy thử hỏi:</p>
                    <div className="flex flex-wrap gap-2">
                        {prompts.map((prompt) => (
                            <button
                                key={prompt}
                                onClick={() => onPromptClick(prompt)}
                                className="px-3 py-1.5 rounded-xl text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-primary-600/10 hover:text-primary-600 dark:hover:bg-primary-600/20 dark:hover:text-primary-400 transition-colors border border-transparent hover:border-primary-600/20"
                            >
                                {prompt}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800">
                <form onSubmit={onSubmit} className="flex gap-3">
                    <input
                        type="text"
                        value={input}
                        onChange={onInputChange}
                        placeholder="Hỏi về tài liệu của bạn..."
                        className="input-field flex-1"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className="btn-primary !px-4 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </>
    );
}

// src/components/ChatPanel.jsx
import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Bot, User, AlertCircle, Download, File } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { api } from '../api/client';
import '../styles/ChatPanel.css';

function ChatPanel({ fileId }) {
  const [query, setQuery] = useState('');
  const [showFileList, setShowFileList] = useState(false);
  const queryClient = useQueryClient();
  const messagesEndRef = useRef(null);

  // Fetch all datasets for Streamlit-style file referencing
  const { data: allDatasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await api.getDatasets();
      return response.data;
    },
  });

  const { data: chatHistory, isLoading } = useQuery({
    queryKey: ['chat-history', fileId],
    queryFn: async () => {
      const response = await api.getChatHistory(fileId);
      return response.data;
    },
    refetchInterval: false,
  });

  const chatMutation = useMutation({
    mutationFn: (query) => api.chat({ file_id: fileId, query }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-history', fileId] });
      setQuery('');
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, chatMutation.isPending]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      chatMutation.mutate(query);
    }
  };

  const handleDownloadPlots = async () => {
    try {
      const response = await api.downloadAllPlots(fileId);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ai_generated_plots_${fileId.substring(0, 8)}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download plots. Make sure some plots are generated first!');
    }
  };

  const examplePrompts = [
    "Analyze this dataset",
    "Visualize all possible insights",
    "Clean and preprocess my data",
    "Fill missing values appropriately",
    "Show me plots for this data",
    "What's in this dataset?",
    "Merge file 0 and file 1",
  ];

  const handleExampleClick = (example) => {
    setQuery(example);
  };

  const currentFileIndex = allDatasets?.findIndex(ds => ds.file_id === fileId) ?? -1;

  return (
    <div className="chat-panel">
      {/* File List Toggle */}
      <div style={{ padding: '10px', background: '#e8eaf6', borderBottom: '1px solid #c5cae9', cursor: 'pointer' }} onClick={() => setShowFileList(!showFileList)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: '#3f51b5' }}>
          <File size={16} />
          <span>Available Files ({allDatasets?.length || 0}) - {showFileList ? 'Hide' : 'Show'} List</span>
        </div>
      </div>

      {/* File List (Streamlit-style) */}
      {showFileList && allDatasets && (
        <div style={{ padding: '12px', background: '#f5f5f5', borderBottom: '2px solid #e0e0e0', maxHeight: '200px', overflowY: 'auto' }}>
          <div style={{ fontSize: '12px', marginBottom: '8px', color: '#666' }}>
            📌 Reference files as "file 0", "file 1", etc. in your queries (e.g., "merge file 0 and file 1")
          </div>
          {allDatasets.map((ds, idx) => (
            <div 
              key={ds.file_id}
              style={{
                padding: '8px 10px',
                marginBottom: '6px',
                background: idx === currentFileIndex ? '#667eea' : 'white',
                color: idx === currentFileIndex ? 'white' : '#333',
                border: idx === currentFileIndex ? '2px solid #5568d3' : '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: idx === currentFileIndex ? '600' : '400',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <strong>File {idx}:</strong> {ds.filename}
                  {idx === currentFileIndex && ' ⭐ (current)'}
                </span>
                <span style={{ opacity: 0.8 }}>
                  {ds.rows || 0} rows × {ds.columns || 0} cols
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div style={{ padding: '10px', background: '#f8f9fa', borderBottom: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '14px', color: '#666' }}>
          💬 Ask AI to generate plots, preprocess data, merge files, or analyze your dataset
        </div>
        <button 
          className="btn btn-secondary"
          onClick={handleDownloadPlots}
          style={{ fontSize: '12px', padding: '6px 12px' }}
          title="Download all AI-generated plots"
        >
          <Download size={14} />
          Download Plots
        </button>
      </div>

      {/* Example Prompts */}
      {(!chatHistory || chatHistory.length === 0) && !chatMutation.isPending && (
        <div style={{ padding: '20px', background: '#f8f9fa', borderBottom: '1px solid #e0e0e0' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px', color: '#666' }}>
            💡 Try these example prompts:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {examplePrompts.map((example, idx) => (
              <button
                key={idx}
                onClick={() => handleExampleClick(example)}
                style={{
                  padding: '8px 12px',
                  fontSize: '12px',
                  background: 'white',
                  border: '1px solid #d0d0d0',
                  borderRadius: '16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#667eea';
                  e.target.style.color = 'white';
                  e.target.style.borderColor = '#667eea';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'white';
                  e.target.style.color = 'black';
                  e.target.style.borderColor = '#d0d0d0';
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-messages">
        {isLoading && (
          <div className="loading-message">Loading chat history...</div>
        )}
        
        {chatHistory?.map((msg, idx) => (
          <div key={idx}>
            <div className="message user-message">
              <User size={20} className="message-icon" />
              <div className="message-content user-content">{msg.query}</div>
            </div>
            <div className="message ai-message">
              <Bot size={20} className="message-icon" />
              <div className="message-content ai-content">
                <div className="markdown-content">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                  >
                    {msg.response}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {chatMutation.isPending && (
          <div className="message ai-message">
            <Bot size={20} />
            <div className="message-content typing">
              <span className="typing-dots">Analyzing</span>
              <span className="dots">...</span>
            </div>
          </div>
        )}
        
        {chatMutation.isError && (
          <div className="message error-message">
            <AlertCircle size={20} />
            <div className="message-content">
              <strong>Error:</strong> {chatMutation.error?.response?.data?.detail || chatMutation.error?.message || 'Failed to get response'}
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about your data..."
          disabled={chatMutation.isPending}
        />
        <button 
          type="submit" 
          disabled={chatMutation.isPending || !query.trim()}
          className="send-button"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;

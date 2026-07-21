import { useEffect, useState } from 'react';
import { Download, FileText } from 'lucide-react';
import { parseContent, exportDocument } from './lib/api';
import type { ParseResponse } from './lib/types';
import Editor from './components/Editor';
import Preview from './components/Preview';
import './index.css';

// Initial sample text
const INITIAL_TEXT = `# Premium Document Engine

Welcome to the **sleek monochrome** AI rendering engine. 
Start typing markdown with \`code blocks\` and equations like $E=mc^2$.

> Glassmorphism and metallic touches make it feel truly premium.

## Features

1. Live parsing of AST
2. Native DOCX export
3. Multiple themes

| Engine | Speed | Quality |
| :--- | :---: | ---: |
| Old | Slow | Low |
| **New** | **Fast** | **Premium** |
`;

type ThemeChoice = "modern" | "academic" | "corporate" | "minimal";

function App() {
  const [content, setContent] = useState(INITIAL_TEXT);
  const [theme, setTheme] = useState<ThemeChoice>("modern");
  const [parsedData, setParsedData] = useState<ParseResponse | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  
  // Debounce the parsing to avoid hitting the backend on every keystroke
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!content.trim()) {
        setParsedData(null);
        return;
      }
      setIsParsing(true);
      try {
        const data = await parseContent(content);
        setParsedData(data);
      } catch (err) {
        console.error("Parse failed", err);
      } finally {
        setIsParsing(false);
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, [content]);

  const handleExport = async () => {
    if (!parsedData) return;
    setIsExporting(true);
    try {
      await exportDocument(parsedData.document, theme);
    } catch (err) {
      console.error("Export failed", err);
      alert("Failed to export document.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">
          <FileText size={24} color="#ffffff" />
          <span>AI Formater</span>
        </div>
        
        <div className="header-actions">
          {isParsing && (
            <div className="loading-indicator">
              <div className="spinner"></div> Parsing...
            </div>
          )}
          
          <select 
            className="select-theme" 
            value={theme} 
            onChange={(e) => setTheme(e.target.value as ThemeChoice)}
          >
            <option value="modern">Modern Theme</option>
            <option value="academic">Academic Theme</option>
            <option value="corporate">Corporate Theme</option>
            <option value="minimal">Minimal Theme</option>
          </select>
          
          <button 
            className="btn-primary" 
            onClick={handleExport}
            disabled={!parsedData || isExporting}
          >
            <Download size={18} />
            {isExporting ? "Exporting..." : "Export DOCX"}
          </button>
        </div>
      </header>

      <main className="workspace">
        <div className="pane pane-left">
          <div className="pane-header">Markdown Input</div>
          <Editor value={content} onChange={setContent} />
        </div>
        <div className="pane">
          <div className="pane-header">Live Preview</div>
          <div className="preview-container">
            <div className="document-page">
              {parsedData ? (
                <Preview document={parsedData.document} />
              ) : (
                <div style={{ color: "var(--text-muted)", textAlign: "center", marginTop: "100px" }}>
                  Start typing to see preview...
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

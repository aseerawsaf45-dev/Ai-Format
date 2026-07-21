import React from 'react';

interface EditorProps {
  value: string;
  onChange: (val: string) => void;
}

const Editor: React.FC<EditorProps> = ({ value, onChange }) => {
  return (
    <textarea
      className="editor-textarea"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Type markdown and equations here..."
      spellCheck={false}
    />
  );
};

export default Editor;

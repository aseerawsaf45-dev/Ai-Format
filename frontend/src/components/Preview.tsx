import React, { useEffect, useRef } from 'react';
import type { Document, Block, Inline } from '../lib/types';
import katex from 'katex';
import mermaid from 'mermaid';

mermaid.initialize({ startOnLoad: false, theme: 'dark' });

const MermaidBlock: React.FC<{ code: string }> = ({ code }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const renderChart = async () => {
      if (!containerRef.current) return;
      const id = `mermaid-${Math.random().toString(36).substring(7)}`;
      try {
        const result: any = await mermaid.render(id, code);
        const svg = result.svg || result; // handle both v9 (string) and v10+ (object)
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (e: any) {
        console.error(e);
        if (containerRef.current) {
          containerRef.current.innerText = "Mermaid Syntax Error";
        }
      }
    };
    renderChart();
  }, [code]);

  return <div ref={containerRef} className="doc-mermaid" style={{ background: 'transparent', margin: '1em 0', display: 'flex', justifyContent: 'center' }} />;
};

const InlineNode: React.FC<{ node: Inline; index: number }> = ({ node, index }) => {
  if (node.type === "run") {
    return (
      <span 
        key={index} 
        className="doc-run"
        data-bold={node.bold}
        data-italic={node.italic}
        data-strike={node.strike}
        data-code={node.code}
      >
        {node.text}
      </span>
    );
  }
  
  if (node.type === "link") {
    return (
      <a key={index} href={node.url} className="doc-link" target="_blank" rel="noopener noreferrer">
        {node.text}
      </a>
    );
  }
  
  if (node.type === "inline_equation") {
    const html = katex.renderToString(node.latex, { throwOnError: false, displayMode: false });
    return (
      <span 
        key={index} 
        className="doc-equation" 
        dangerouslySetInnerHTML={{ __html: html }} 
      />
    );
  }

  return null;
};

const Inlines: React.FC<{ inlines: Inline[] }> = ({ inlines }) => {
  return (
    <>
      {inlines.map((node, i) => <InlineNode key={i} node={node} index={i} />)}
    </>
  );
};

const BlockNode: React.FC<{ block: Block; index: number }> = ({ block, index }) => {
  switch (block.type) {
    case "heading":
      const H = `h${block.level}` as keyof React.JSX.IntrinsicElements;
      return (
        <H key={index} className="doc-heading" data-level={block.level} id={block.id || undefined}>
          {block.text}
        </H>
      );
      
    case "paragraph":
      return (
        <p key={index} className="doc-paragraph" style={{ textAlign: block.align }}>
          <Inlines inlines={block.inline} />
        </p>
      );
      
    case "code_block":
      if (block.lang === 'mermaid') {
        return <MermaidBlock key={index} code={block.code} />;
      }
      return (
        <div key={index} className="doc-code-block">
          {block.lang && <div className="doc-code-lang">{block.lang}</div>}
          <pre><code>{block.code}</code></pre>
        </div>
      );
      
    case "block_equation":
      const html = katex.renderToString(block.latex, { throwOnError: false, displayMode: true });
      return (
        <div 
          key={index} 
          className="doc-block-equation"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
      
    case "blockquote":
      return (
        <blockquote key={index} className="doc-blockquote">
          {block.children.map((child, i) => <BlockNode key={i} block={child} index={i} />)}
        </blockquote>
      );
      
    case "list":
      const ListTag = block.ordered ? "ol" : "ul";
      return (
        <ListTag key={index} className="doc-list">
          {block.items.map((item, i) => (
            <li key={i} className="doc-list-item">
              {item.checked !== null && item.checked !== undefined && (
                <input type="checkbox" readOnly checked={item.checked} style={{ marginRight: 8 }} />
              )}
              <Inlines inlines={item.inline} />
              {item.children && item.children.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {item.children.map((child, ci) => <BlockNode key={ci} block={child} index={ci} />)}
                </div>
              )}
            </li>
          ))}
        </ListTag>
      );
      
    case "table":
      return (
        <table key={index} className="doc-table">
          <tbody>
            {block.rows.map((row, ri) => (
              <tr key={ri}>
                {row.cells.map((cell, ci) => {
                  const CellTag = cell.is_header ? "th" : "td";
                  return (
                    <CellTag key={ci} style={{ textAlign: cell.align }} colSpan={cell.colspan} rowSpan={cell.rowspan}>
                      <Inlines inlines={cell.inline} />
                    </CellTag>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      );
      
    case "image":
      const src = block.base64 ? `data:${block.mime};base64,${block.base64}` : block.url;
      return (
        <div key={index} style={{ textAlign: "center", marginBottom: "1em" }}>
          {src && <img src={src} alt={block.alt} className="doc-image" />}
          {block.caption && <div style={{ fontSize: "0.9em", color: "var(--text-muted)", fontStyle: "italic" }}>{block.caption}</div>}
        </div>
      );
      
    case "thematic_break":
      return <hr key={index} className="doc-thematic-break" />;
      
    default:
      return null;
  }
};

const Preview: React.FC<{ document: Document }> = ({ document }) => {
  return (
    <>
      {document.title && <h1 className="doc-heading" data-level="1">{document.title}</h1>}
      {document.children.map((block, i) => (
        <BlockNode key={i} block={block} index={i} />
      ))}
    </>
  );
};

export default Preview;

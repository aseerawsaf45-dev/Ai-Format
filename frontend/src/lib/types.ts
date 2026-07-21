// Mirrors the backend DocTree models

export type Inline = Run | Hyperlink | InlineEquation;

export interface Run {
  type: "run";
  text: string;
  bold?: boolean;
  italic?: boolean;
  strike?: boolean;
  code?: boolean;
}

export interface Hyperlink {
  type: "link";
  text: string;
  url: string;
}

export interface InlineEquation {
  type: "inline_equation";
  latex: string;
  omml?: string | null;
}

export type Block =
  | Heading
  | Paragraph
  | CodeBlock
  | BlockEquation
  | BlockQuote
  | ListBlock
  | Table
  | Image
  | ThematicBreak;

export interface Heading {
  type: "heading";
  level: number;
  text: string;
  id?: string | null;
}

export interface Paragraph {
  type: "paragraph";
  inline: Inline[];
  align?: "left" | "center" | "right" | "justify";
}

export interface CodeBlock {
  type: "code_block";
  code: string;
  lang?: string | null;
  show_line_numbers?: boolean;
}

export interface BlockEquation {
  type: "block_equation";
  latex: string;
  omml?: string | null;
}

export interface BlockQuote {
  type: "blockquote";
  children: Block[];
}

export interface ListItem {
  type: "list_item";
  inline: Inline[];
  checked?: boolean | null;
  children: Block[];
}

export interface ListBlock {
  type: "list";
  ordered?: boolean;
  depth?: number;
  items: ListItem[];
}

export interface TableCell {
  type: "table_cell";
  inline: Inline[];
  align?: "left" | "center" | "right";
  colspan?: number;
  rowspan?: number;
  is_header?: boolean;
}

export interface TableRow {
  type: "table_row";
  cells: TableCell[];
}

export interface Table {
  type: "table";
  rows: TableRow[];
}

export interface Image {
  type: "image";
  url?: string | null;
  base64?: string | null;
  alt?: string;
  caption?: string | null;
  mime?: string;
}

export interface ThematicBreak {
  type: "thematic_break";
}

export interface Document {
  type: "document";
  title?: string | null;
  children: Block[];
}

export interface ParseResponse {
  document: Document;
  stats: Record<string, number>;
}

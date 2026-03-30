"use client";

import { useState } from "react";
import { AIPrompts } from "@/types";

interface PromptCardProps {
  prompts: AIPrompts;
}

const PROMPT_TYPES = [
  { key: "visual" as const, label: "画面提示词", icon: "&#128248;" },
  { key: "copywriting" as const, label: "文案提示词", icon: "&#9997;" },
  { key: "recreation" as const, label: "复刻提示词", icon: "&#127916;" },
];

export default function PromptCard({ prompts }: PromptCardProps) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-3 mt-3">
      {PROMPT_TYPES.map(({ key, label, icon }) => {
        const text = prompts[key];
        if (!text) return null;
        return (
          <div key={key} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span
                className="text-xs font-medium text-gray-500"
                dangerouslySetInnerHTML={{ __html: `${icon} ${label}` }}
              />
              <button
                onClick={() => copyToClipboard(text, key)}
                className="text-xs text-blue-500 hover:text-blue-700 transition-colors"
              >
                {copied === key ? "已复制" : "复制"}
              </button>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{text}</p>
          </div>
        );
      })}
    </div>
  );
}

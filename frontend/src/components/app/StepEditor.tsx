import { useRef } from "react";
import { ArrowDown, ArrowUp, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ScenarioStep, StepType } from "@/types";

const typeLabels: Record<StepType, string> = {
  command: "Command",
  comment: "Comment",
  write_file: "Write file",
  write_vim: "Write file (vim)",
};

export function StepEditor({
  step,
  index,
  total,
  onChange,
  onRemove,
  onMove,
}: {
  step: ScenarioStep;
  index: number;
  total: number;
  onChange: (step: ScenarioStep) => void;
  onRemove: () => void;
  onMove: (direction: -1 | 1) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="rounded-lg border p-4 space-y-3 bg-card">
      <div className="flex items-center gap-2">
        <span className="flex size-6 items-center justify-center rounded-full bg-muted text-xs font-medium shrink-0">
          {index + 1}
        </span>
        <Select
          value={step.type}
          onValueChange={(v) => onChange({ ...step, type: v as StepType })}
        >
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(typeLabels) as StepType[]).map((t) => (
              <SelectItem key={t} value={t}>
                {typeLabels[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="ml-auto flex items-center gap-1">
          <Button size="icon" variant="ghost" className="size-7" disabled={index === 0} onClick={() => onMove(-1)}>
            <ArrowUp className="size-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="size-7"
            disabled={index === total - 1}
            onClick={() => onMove(1)}
          >
            <ArrowDown className="size-4" />
          </Button>
          <Button size="icon" variant="ghost" className="size-7 text-destructive hover:text-destructive" onClick={onRemove}>
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>

      {(step.type === "command" || step.type === "comment") && (
        <div className="space-y-1.5">
          <Label>{step.type === "command" ? "Command text" : "Comment text"}</Label>
          <Input
            value={step.text ?? ""}
            onChange={(e) => onChange({ ...step, text: e.target.value })}
            placeholder={step.type === "command" ? "go run worker.go" : "Notice the shared counter…"}
            className="font-mono text-sm"
          />
        </div>
      )}

      {(step.type === "write_file" || step.type === "write_vim") && (
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-1.5">
            <Label>Destination path (inside container)</Label>
            <Input
              value={step.path ?? ""}
              onChange={(e) => onChange({ ...step, path: e.target.value })}
              placeholder="worker.go"
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>File content</Label>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload /> Upload file
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const reader = new FileReader();
                  reader.onload = () => {
                    onChange({
                      ...step,
                      content: String(reader.result ?? ""),
                      path: step.path || file.name,
                    });
                  };
                  reader.readAsText(file);
                  e.target.value = "";
                }}
              />
            </div>
            <Textarea
              value={step.content ?? ""}
              onChange={(e) => onChange({ ...step, content: e.target.value })}
              rows={8}
              className="font-mono text-sm"
              placeholder="package main…"
            />
          </div>

          {step.type === "write_vim" && (
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={step.simulate_typos ?? false}
                  onCheckedChange={(checked) => onChange({ ...step, simulate_typos: checked })}
                />
                Simulate typos
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={step.force_blank ?? false}
                  onCheckedChange={(checked) => onChange({ ...step, force_blank: checked })}
                />
                Always start blank (ignore existing file)
              </label>
              <p className="text-xs text-muted-foreground pl-6">
                By default, write_vim auto-detects an existing file at this path in the
                container and edits it in place instead of overwriting it from scratch.
              </p>
            </div>
          )}
        </div>
      )}

      <div className="space-y-1.5 w-40">
        <Label>Pause after (s)</Label>
        <Input
          type="number"
          step="0.1"
          min="0"
          value={step.pause_after ?? ""}
          onChange={(e) =>
            onChange({ ...step, pause_after: e.target.value === "" ? undefined : Number(e.target.value) })
          }
          placeholder="1.5"
        />
      </div>
    </div>
  );
}

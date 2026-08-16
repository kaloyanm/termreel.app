import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

      {step.type === "write_file" && (
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
            <Label>File content</Label>
            <Textarea
              value={step.content ?? ""}
              onChange={(e) => onChange({ ...step, content: e.target.value })}
              rows={8}
              className="font-mono text-sm"
              placeholder="package main…"
            />
          </div>
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

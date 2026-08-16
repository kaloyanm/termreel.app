import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import * as yaml from "js-yaml";
import { ArrowLeft, Loader2, Play, Plus, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Scenarios } from "@/lib/api";
import { StepEditor } from "@/components/app/StepEditor";
import type { DockerConfig, ScenarioStep, TypingConfig } from "@/types";

const emptyStep = (type: ScenarioStep["type"] = "command"): ScenarioStep => ({
  type,
  text: type === "write_file" ? undefined : "",
  path: type === "write_file" ? "" : undefined,
  content: type === "write_file" ? "" : undefined,
  pause_after: 1.5,
});

export default function ScenarioEditorPage() {
  const { scenarioId } = useParams();
  const queryClient = useQueryClient();

  const { data: scenario, isLoading } = useQuery({
    queryKey: ["scenario", scenarioId],
    queryFn: () => Scenarios.get(scenarioId!),
    enabled: !!scenarioId,
  });

  const [title, setTitle] = useState("");
  const [docker, setDocker] = useState<DockerConfig | null>(null);
  const [typingCfg, setTypingCfg] = useState<TypingConfig | null>(null);
  const [steps, setSteps] = useState<ScenarioStep[]>([]);
  const [loadedId, setLoadedId] = useState<string | null>(null);

  useEffect(() => {
    if (scenario && scenario.id !== loadedId) {
      setTitle(scenario.title);
      setDocker(scenario.docker);
      setTypingCfg(scenario.typing);
      setSteps(scenario.steps);
      setLoadedId(scenario.id);
    }
  }, [scenario, loadedId]);

  const saveMutation = useMutation({
    mutationFn: () =>
      Scenarios.update(scenarioId!, { title, docker: docker!, typing: typingCfg!, steps }),
    onSuccess: () => {
      toast.success("Scenario saved");
      queryClient.invalidateQueries({ queryKey: ["scenario", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["scenarios", scenario?.playlist_id] });
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      toast.error(typeof message === "string" ? message : "Failed to save — check step fields");
    },
  });

  const renderMutation = useMutation({
    mutationFn: () => Scenarios.render(scenarioId!, "dracula"),
    onSuccess: () => {
      toast.success("Render queued");
      queryClient.invalidateQueries({ queryKey: ["scenario", scenarioId] });
    },
    onError: () => toast.error("Failed to queue render (is the RQ worker running?)"),
  });

  const job = scenario?.latest_job;
  const isActive = job?.status === "queued" || job?.status === "running";

  useEffect(() => {
    if (!isActive || !scenarioId) return;
    const id = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["scenario", scenarioId] });
    }, 2000);
    return () => clearInterval(id);
  }, [isActive, scenarioId, queryClient]);

  if (isLoading || !docker || !typingCfg) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  const yamlPreview = yaml.dump(
    { title, docker, typing: typingCfg, steps: steps.map((s) => ({ ...s, pause_after: s.pause_after ?? undefined })) },
    { skipInvalid: true }
  );

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" render={<Link to={`/app/playlists/${scenario?.playlist_id}`} />}>
          <ArrowLeft />
        </Button>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="text-xl font-semibold h-11 border-none shadow-none px-0 focus-visible:ring-0"
        />
        {job && (
          <Badge variant={job.status === "failed" ? "destructive" : job.status === "done" ? "outline" : "secondary"} className="gap-1">
            {isActive && <Loader2 className="size-3 animate-spin" />}
            {job.status}
          </Badge>
        )}
        <div className="ml-auto flex gap-2">
          <Button variant="outline" disabled={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
            <Save /> Save
          </Button>
          <Button disabled={steps.length === 0 || isActive || renderMutation.isPending} onClick={() => renderMutation.mutate()}>
            <Play /> {isActive ? "Rendering…" : "Render"}
          </Button>
        </div>
      </div>

      {job?.status === "done" && (
        <Card className="mt-4">
          <CardContent className="pt-6 flex flex-wrap items-center gap-4">
            {job.gif_url && <img src={job.gif_url} className="h-32 rounded border" alt="preview" />}
            <div className="flex gap-4 text-sm">
              <a className="underline" href={job.mp4_url ?? "#"} target="_blank" rel="noreferrer">Download MP4</a>
              <a className="underline" href={job.gif_url ?? "#"} target="_blank" rel="noreferrer">Download GIF</a>
              <a className="underline" href={job.cast_url ?? "#"} target="_blank" rel="noreferrer">Download .cast</a>
            </div>
          </CardContent>
        </Card>
      )}
      {job?.status === "failed" && (
        <Card className="mt-4 border-destructive/50">
          <CardContent className="pt-6 text-sm text-destructive whitespace-pre-wrap">{job.error}</CardContent>
        </Card>
      )}

      <Tabs defaultValue="steps" className="mt-6">
        <TabsList>
          <TabsTrigger value="steps">Steps</TabsTrigger>
          <TabsTrigger value="environment">Environment</TabsTrigger>
          <TabsTrigger value="yaml">YAML</TabsTrigger>
        </TabsList>

        <TabsContent value="steps" className="space-y-3">
          {steps.map((step, i) => (
            <StepEditor
              key={i}
              step={step}
              index={i}
              total={steps.length}
              onChange={(s) => setSteps(steps.map((old, idx) => (idx === i ? s : old)))}
              onRemove={() => setSteps(steps.filter((_, idx) => idx !== i))}
              onMove={(dir) => {
                const j = i + dir;
                if (j < 0 || j >= steps.length) return;
                const next = [...steps];
                [next[i], next[j]] = [next[j], next[i]];
                setSteps(next);
              }}
            />
          ))}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setSteps([...steps, emptyStep("command")])}>
              <Plus /> Command
            </Button>
            <Button variant="outline" size="sm" onClick={() => setSteps([...steps, emptyStep("comment")])}>
              <Plus /> Comment
            </Button>
            <Button variant="outline" size="sm" onClick={() => setSteps([...steps, emptyStep("write_file")])}>
              <Plus /> Write file
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="environment">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Docker</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <Field label="Image" value={docker.image} onChange={(v) => setDocker({ ...docker, image: v })} placeholder="golang:1.22" />
              <Field label="Container name" value={docker.container_name} onChange={(v) => setDocker({ ...docker, container_name: v })} />
              <Field label="Mount host path" value={docker.mount_host_path} onChange={(v) => setDocker({ ...docker, mount_host_path: v })} />
              <Field label="Mount container path" value={docker.mount_container_path} onChange={(v) => setDocker({ ...docker, mount_container_path: v })} />
              <Field label="Workdir" value={docker.workdir ?? ""} onChange={(v) => setDocker({ ...docker, workdir: v })} />
            </CardContent>
          </Card>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Typing</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-4">
              <Field
                label="Chars/sec"
                type="number"
                value={String(typingCfg.base_cps)}
                onChange={(v) => setTypingCfg({ ...typingCfg, base_cps: Number(v) })}
              />
              <Field
                label="Jitter %"
                type="number"
                value={String(typingCfg.jitter_pct)}
                onChange={(v) => setTypingCfg({ ...typingCfg, jitter_pct: Number(v) })}
              />
              <Field
                label="Default pause after (s)"
                type="number"
                value={String(typingCfg.default_pause_after)}
                onChange={(v) => setTypingCfg({ ...typingCfg, default_pause_after: Number(v) })}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="yaml">
          <p className="text-sm text-muted-foreground mb-2">
            The exact format driver.py consumes (see scenario.example.yaml).
          </p>
          <pre className="rounded-lg border bg-muted p-4 text-xs overflow-auto font-mono">{yamlPreview}</pre>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  );
}

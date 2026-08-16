import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Play, Pencil, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Scenarios } from "@/lib/api";
import type { Scenario } from "@/types";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  queued: "secondary",
  running: "default",
  done: "outline",
  failed: "destructive",
};

export function ScenarioCard({ scenario: initial }: { scenario: Scenario }) {
  const queryClient = useQueryClient();
  const status = initial.latest_job?.status;
  const isActive = status === "queued" || status === "running";

  const { data: scenario } = useQuery({
    queryKey: ["scenario", initial.id],
    queryFn: () => Scenarios.get(initial.id),
    initialData: initial,
    refetchInterval: isActive ? 2000 : false,
  });

  const renderMutation = useMutation({
    mutationFn: () => Scenarios.render(scenario!.id, "dracula"),
    onSuccess: () => {
      toast.success("Render queued");
      queryClient.invalidateQueries({ queryKey: ["scenario", initial.id] });
    },
    onError: () => toast.error("Failed to queue render (is the RQ worker running?)"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => Scenarios.remove(scenario!.id),
    onSuccess: () => {
      toast.success("Scenario deleted");
      queryClient.invalidateQueries({ queryKey: ["scenarios", scenario!.playlist_id] });
      queryClient.invalidateQueries({ queryKey: ["playlist", scenario!.playlist_id] });
    },
  });

  if (!scenario) return null;
  const job = scenario.latest_job;

  return (
    <Card className="overflow-hidden">
      {job?.status === "done" && job.gif_url && (
        <img src={job.gif_url} alt="" className="w-full h-40 object-cover bg-muted" />
      )}
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2">{scenario.title}</CardTitle>
          {job && (
            <Badge variant={statusVariant[job.status]} className="shrink-0 gap-1">
              {isActive && <Loader2 className="size-3 animate-spin" />}
              {job.status}
            </Badge>
          )}
        </div>
        <CardDescription>
          {scenario.steps.length} step{scenario.steps.length === 1 ? "" : "s"} ·{" "}
          {scenario.docker.image}
        </CardDescription>
      </CardHeader>
      {job?.status === "failed" && (
        <CardContent>
          <p className="text-xs text-destructive line-clamp-3">{job.error}</p>
        </CardContent>
      )}
      {job?.status === "done" && (
        <CardContent className="flex gap-3 text-sm">
          <a className="underline underline-offset-2" href={job.mp4_url ?? "#"} target="_blank" rel="noreferrer">
            MP4
          </a>
          <a className="underline underline-offset-2" href={job.gif_url ?? "#"} target="_blank" rel="noreferrer">
            GIF
          </a>
          <a className="underline underline-offset-2" href={job.cast_url ?? "#"} target="_blank" rel="noreferrer">
            .cast
          </a>
        </CardContent>
      )}
      <CardFooter className="gap-2">
        <Button size="sm" variant="outline" render={<Link to={`/app/scenarios/${scenario.id}`} />}>
          <Pencil /> Edit
        </Button>
        <Button
          size="sm"
          disabled={scenario.steps.length === 0 || isActive || renderMutation.isPending}
          onClick={() => renderMutation.mutate()}
        >
          <Play /> {isActive ? "Rendering…" : "Render"}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="ml-auto text-destructive hover:text-destructive"
          onClick={() => deleteMutation.mutate()}
        >
          <Trash2 />
        </Button>
      </CardFooter>
    </Card>
  );
}

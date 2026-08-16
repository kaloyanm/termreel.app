import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Plus, ListVideo, Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Playlists, Projects } from "@/lib/api";
import { NewPlaylistDialog } from "@/components/app/NewPlaylistDialog";

export default function ProjectPage() {
  const { projectId } = useParams();
  const [open, setOpen] = useState(false);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => Projects.get(projectId!),
    enabled: !!projectId,
  });
  const { data: playlists, isLoading } = useQuery({
    queryKey: ["playlists", projectId],
    queryFn: () => Playlists.list(projectId!),
    enabled: !!projectId,
  });

  if (!projectId) return null;

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{project?.name ?? "…"}</h1>
          <p className="text-muted-foreground text-sm">
            {project?.description || "Unlimited playlists, each holding scenario artefacts."}
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus /> New playlist
        </Button>
      </div>

      {isLoading && <p className="mt-8 text-sm text-muted-foreground">Loading…</p>}

      {!isLoading && playlists?.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-3 text-center">
          <ListVideo className="size-10 text-muted-foreground" />
          <p className="text-muted-foreground">No playlists yet. Create your first one.</p>
          <Button onClick={() => setOpen(true)}>
            <Plus /> New playlist
          </Button>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {playlists?.map((pl) => (
          <Link key={pl.id} to={`/app/playlists/${pl.id}`}>
            <Card className="h-full hover:border-primary/50 transition-colors">
              <CardHeader>
                <CardTitle>{pl.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {pl.description || "No description"}
                </CardDescription>
              </CardHeader>
              <CardFooter className="text-sm text-muted-foreground gap-1.5">
                <Film className="size-4" />
                {pl.scenario_count} artefact{pl.scenario_count === 1 ? "" : "s"}
              </CardFooter>
            </Card>
          </Link>
        ))}
      </div>

      <NewPlaylistDialog projectId={projectId} open={open} onOpenChange={setOpen} />
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Plus, Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Playlists, Scenarios } from "@/lib/api";
import { NewScenarioDialog } from "@/components/app/NewScenarioDialog";
import { ScenarioCard } from "@/components/app/ScenarioCard";

export default function PlaylistPage() {
  const { playlistId } = useParams();
  const [open, setOpen] = useState(false);

  const { data: playlist } = useQuery({
    queryKey: ["playlist", playlistId],
    queryFn: () => Playlists.get(playlistId!),
    enabled: !!playlistId,
  });
  const { data: scenarios, isLoading } = useQuery({
    queryKey: ["scenarios", playlistId],
    queryFn: () => Scenarios.list(playlistId!),
    enabled: !!playlistId,
  });

  if (!playlistId) return null;

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{playlist?.name ?? "…"}</h1>
          <p className="text-muted-foreground text-sm">
            {playlist?.description || "Scenario artefacts created with the editor."}
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus /> New scenario
        </Button>
      </div>

      {isLoading && <p className="mt-8 text-sm text-muted-foreground">Loading…</p>}

      {!isLoading && scenarios?.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-3 text-center">
          <Film className="size-10 text-muted-foreground" />
          <p className="text-muted-foreground">No scenarios yet. Create your first one.</p>
          <Button onClick={() => setOpen(true)}>
            <Plus /> New scenario
          </Button>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios?.map((s) => (
          <ScenarioCard key={s.id} scenario={s} />
        ))}
      </div>

      <NewScenarioDialog playlistId={playlistId} open={open} onOpenChange={setOpen} />
    </div>
  );
}

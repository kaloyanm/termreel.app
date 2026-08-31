import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useFlavours } from "@/hooks/use-flavours";
import { Scenarios } from "@/lib/api";

export function NewScenarioDialog({
  playlistId,
  open,
  onOpenChange,
}: {
  playlistId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [title, setTitle] = useState("");
  const { data: flavours } = useFlavours();
  const [flavour, setFlavour] = useState<string | undefined>(undefined);
  const selectedFlavour = flavour ?? flavours?.[0]?.id;
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: () =>
      Scenarios.create(playlistId, {
        title,
        docker: {
          flavour: selectedFlavour!,
          container_name: `ytdemo_${Date.now()}`,
          mount_host_path: "./demo-repo",
          mount_container_path: "/repo",
          workdir: "/repo",
        },
        typing: { base_cps: 14, jitter_pct: 0.35, default_pause_after: 1.5 },
        steps: [],
      }),
    onSuccess: (scenario) => {
      queryClient.invalidateQueries({ queryKey: ["scenarios", playlistId] });
      queryClient.invalidateQueries({ queryKey: ["playlist", playlistId] });
      toast.success("Scenario created — start editing");
      onOpenChange(false);
      setTitle("");
      navigate(`/app/scenarios/${scenario.id}`);
    },
    onError: () => toast.error("Failed to create scenario"),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New scenario</DialogTitle>
          <DialogDescription>
            Creates a draft artefact in this playlist. You'll add steps in the editor.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="scenario-title">Title</Label>
            <Input
              id="scenario-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Fix a race condition in a Go worker pool"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="scenario-flavour">Flavour</Label>
            <Select value={selectedFlavour} onValueChange={(v) => setFlavour(v ?? undefined)}>
              <SelectTrigger id="scenario-flavour" className="w-full">
                <SelectValue placeholder="Select a flavour" />
              </SelectTrigger>
              <SelectContent>
                {flavours?.map((f) => (
                  <SelectItem key={f.id} value={f.id}>
                    {f.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            disabled={!title.trim() || !selectedFlavour || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Creating…" : "Create & edit"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

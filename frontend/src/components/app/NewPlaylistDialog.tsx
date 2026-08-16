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
import { Textarea } from "@/components/ui/textarea";
import { Playlists } from "@/lib/api";

export function NewPlaylistDialog({
  projectId,
  open,
  onOpenChange,
}: {
  projectId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: () => Playlists.create(projectId, { name, description }),
    onSuccess: (playlist) => {
      queryClient.invalidateQueries({ queryKey: ["playlists", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success(`Playlist "${playlist.name}" created`);
      onOpenChange(false);
      setName("");
      setDescription("");
      navigate(`/app/playlists/${playlist.id}`);
    },
    onError: () => toast.error("Failed to create playlist"),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New playlist</DialogTitle>
          <DialogDescription>
            A playlist holds the scenario artefacts you build in the editor.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="playlist-name">Name</Label>
            <Input
              id="playlist-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Episode drafts"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="playlist-description">Description</Label>
            <Textarea
              id="playlist-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button disabled={!name.trim() || mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? "Creating…" : "Create playlist"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

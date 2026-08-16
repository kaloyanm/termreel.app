import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, FolderKanban, ListVideo } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Projects } from "@/lib/api";
import { NewProjectDialog } from "@/components/app/NewProjectDialog";

export default function ProjectsPage() {
  const [open, setOpen] = useState(false);
  const { data: projects, isLoading } = useQuery({ queryKey: ["projects"], queryFn: Projects.list });

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Projects</h1>
          <p className="text-muted-foreground text-sm">
            Every episode series lives inside a project.
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus /> New project
        </Button>
      </div>

      {isLoading && <p className="mt-8 text-sm text-muted-foreground">Loading…</p>}

      {!isLoading && projects?.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-3 text-center">
          <FolderKanban className="size-10 text-muted-foreground" />
          <p className="text-muted-foreground">No projects yet. Create your first one.</p>
          <Button onClick={() => setOpen(true)}>
            <Plus /> New project
          </Button>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects?.map((p) => (
          <Link key={p.id} to={`/app/projects/${p.id}`}>
            <Card className="h-full hover:border-primary/50 transition-colors">
              <CardHeader>
                <CardTitle>{p.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {p.description || "No description"}
                </CardDescription>
              </CardHeader>
              <CardFooter className="text-sm text-muted-foreground gap-1.5">
                <ListVideo className="size-4" />
                {p.playlist_count} playlist{p.playlist_count === 1 ? "" : "s"}
              </CardFooter>
            </Card>
          </Link>
        ))}
      </div>

      <NewProjectDialog open={open} onOpenChange={setOpen} />
    </div>
  );
}

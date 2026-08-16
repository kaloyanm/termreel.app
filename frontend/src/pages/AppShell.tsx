import { Link, Outlet, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Terminal, Plus, FolderKanban } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Projects } from "@/lib/api";
import { useState } from "react";
import { NewProjectDialog } from "@/components/app/NewProjectDialog";

export default function AppShell() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: Projects.list });

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <Link to="/" className="flex items-center gap-2 px-2 py-1.5 font-semibold">
            <Terminal className="size-5" />
            <span>termreel</span>
          </Link>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <div className="flex items-center justify-between px-2">
              <SidebarGroupLabel>Projects</SidebarGroupLabel>
              <Button
                size="icon"
                variant="ghost"
                className="size-6"
                onClick={() => setDialogOpen(true)}
              >
                <Plus className="size-4" />
              </Button>
            </div>
            <SidebarGroupContent>
              <SidebarMenu>
                {projects?.length === 0 && (
                  <p className="px-2 text-xs text-muted-foreground">No projects yet.</p>
                )}
                {projects?.map((p) => (
                  <SidebarMenuItem key={p.id}>
                    <SidebarMenuButton
                      isActive={p.id === projectId}
                      onClick={() => navigate(`/app/projects/${p.id}`)}
                    >
                      <FolderKanban />
                      <span>{p.name}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 border-b px-4">
          <SidebarTrigger />
        </header>
        <div className="flex-1 overflow-auto p-6">
          <Outlet />
        </div>
      </SidebarInset>
      <NewProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </SidebarProvider>
  );
}

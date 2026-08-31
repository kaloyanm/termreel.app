import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Terminal } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="border-b">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Terminal className="size-5" />
          <span>termreel</span>
        </Link>
        <nav className="flex items-center gap-6">
          <Link
            to="/use-cases"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Use Cases
          </Link>
          <Button render={<Link to="/app/projects" />}>Open app</Button>
        </nav>
      </div>
    </header>
  );
}

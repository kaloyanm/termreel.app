import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Jobs } from "@/lib/api";
import type { RenderJob } from "@/types";

export function JobLogDialog({ jobId, status }: { jobId: string; status: RenderJob["status"] }) {
  const [open, setOpen] = useState(false);
  const isActive = status === "queued" || status === "running";
  const scrollRef = useRef<HTMLPreElement>(null);

  const { data: log } = useQuery({
    queryKey: ["job-log", jobId],
    queryFn: () => Jobs.log(jobId),
    enabled: open,
    refetchInterval: open && isActive ? 2000 : false,
  });

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [log, open]);

  return (
    <>
      <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
        <FileText /> Logs
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Render log</DialogTitle>
          </DialogHeader>
          <pre
            ref={scrollRef}
            className="h-96 overflow-auto rounded-lg border bg-muted p-4 text-xs font-mono whitespace-pre-wrap"
          >
            {log || "No output yet."}
          </pre>
        </DialogContent>
      </Dialog>
    </>
  );
}

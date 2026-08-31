import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Terminal, FolderKanban, ListVideo, Wand2, Container, Film } from "lucide-react";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { SiteFooter } from "@/components/marketing/SiteFooter";

const steps = [
  {
    icon: Wand2,
    title: "Write a scenario",
    body: "Describe an episode in the interactive editor: which Docker image, which commands to type, which files to write.",
  },
  {
    icon: Container,
    title: "Real execution",
    body: "A real Docker container runs the commands. No faked terminal text — actual compiler errors, real output.",
  },
  {
    icon: Terminal,
    title: "Recorded, not filmed",
    body: "asciinema captures structured timing + text, so you can re-theme, re-speed, or re-render without re-running anything.",
  },
  {
    icon: Film,
    title: "Rendered to video",
    body: "One click turns the recording into a themed GIF and MP4, ready to drop into your editor with voiceover and music.",
  },
];

const features = [
  {
    icon: FolderKanban,
    title: "Projects",
    body: "Group episodes by product, course, or client. Unlimited playlists per project.",
  },
  {
    icon: ListVideo,
    title: "Playlists",
    body: "Every playlist holds the scenario artefacts you build with the editor — drafts and rendered videos together.",
  },
  {
    icon: Wand2,
    title: "Scenario editor",
    body: "A structured form for the exact YAML schema driver.py already understands — commands, comments, file writes, typing speed and jitter.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-svh flex flex-col">
      <SiteHeader />

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-24 text-center">
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-balance">
            Turn a scenario file into a real coding-session video
          </h1>
          <p className="mt-5 text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
            termreel is a web-based studio for the docker + asciinema + ffmpeg pipeline you
            already trust. Write the scenario, click render, get an MP4 — genuine terminal
            output every time.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Button size="lg" render={<Link to="/app/projects" />}>
              Start a project
            </Button>
            <Button size="lg" variant="outline" render={<a href="#how-it-works" />}>
              See how it works
            </Button>
          </div>
        </section>

        <section id="how-it-works" className="border-y bg-muted/30">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <h2 className="text-2xl font-semibold text-center">How it works</h2>
            <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {steps.map((s, i) => (
                <Card key={s.title} className="relative">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <div className="flex size-9 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                        {i + 1}
                      </div>
                      <s.icon className="size-5 text-muted-foreground" />
                    </div>
                    <CardTitle className="mt-2">{s.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{s.body}</CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-2xl font-semibold text-center">Built for series, not one-offs</h2>
          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-6">
            {features.map((f) => (
              <Card key={f.title}>
                <CardHeader>
                  <f.icon className="size-6 text-primary" />
                  <CardTitle className="mt-2">{f.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{f.body}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-24 text-center">
          <Card className="mx-auto max-w-2xl bg-primary text-primary-foreground border-none">
            <CardContent className="py-10">
              <h2 className="text-2xl font-semibold">Ready to record your next episode?</h2>
              <p className="mt-2 text-primary-foreground/80">
                No accounts, no billing — just create a project and start writing scenarios.
              </p>
              <Button size="lg" variant="secondary" className="mt-6" render={<Link to="/app/projects" />}>
                Open the app
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

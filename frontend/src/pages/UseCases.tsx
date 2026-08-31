import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Rocket,
  GraduationCap,
  Building2,
  Bug,
  BookOpen,
  Presentation,
  FileText,
  UserPlus,
  BarChart3,
  Share2,
} from "lucide-react";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { SiteFooter } from "@/components/marketing/SiteFooter";

const useCases = [
  {
    icon: Rocket,
    title: "Developer tool marketing",
    body: "Record \"install → first command → result\" episodes to embed on your own landing page, proving the tool actually works instead of a staged screen-recording.",
  },
  {
    icon: GraduationCap,
    title: "Technical course content",
    body: "Build a playlist per course, one scenario per lesson, so every video is reproducible — fix a typo in lesson 3 without re-recording the whole course.",
  },
  {
    icon: Building2,
    title: "Client & agency deliverables",
    body: "Produce coding-demo videos for multiple clients, using projects to keep each client's episodes and branding separate.",
  },
  {
    icon: Bug,
    title: "Bug-fix walkthroughs",
    body: "\"Here's the bug, here's the real error, here's the fix\" content for blog posts, changelogs, or postmortems, where the authenticity of the error output matters.",
  },
  {
    icon: BookOpen,
    title: "API & SDK documentation",
    body: "Real curl or SDK calls against a running service, showing actual JSON responses instead of hand-typed fake output in docs.",
  },
  {
    icon: Presentation,
    title: "Conference talk prep",
    body: "Pre-record a \"live coding\" segment that's guaranteed to work — no live-demo risk — then play it back during a talk.",
  },
  {
    icon: FileText,
    title: "Release notes & changelogs",
    body: "\"What's new in v2.0\" episodes showing the new feature actually running, versioned alongside the release.",
  },
  {
    icon: UserPlus,
    title: "Internal onboarding",
    body: "Record \"how we set up this repo locally\" as a scenario new hires can watch, kept accurate because it's re-run in a real container each time it's updated.",
  },
  {
    icon: BarChart3,
    title: "Comparisons & benchmarks",
    body: "Before/after or tool-A-vs-tool-B episodes where real command output is the whole point — performance numbers, error rates.",
  },
  {
    icon: Share2,
    title: "Social & education clips",
    body: "Short single-scenario episodes — a \"one weird trick\" terminal tip — rendered as GIFs for tweets or shorts, using the same pipeline as longer course content.",
  },
];

export default function UseCases() {
  return (
    <div className="min-h-svh flex flex-col">
      <SiteHeader />

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-balance">
            What people build with termreel
          </h1>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
            Any time a coding-session video needs to show genuine terminal output — not
            typed-out fake text — and might need to be re-cut later without re-filming.
          </p>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-20">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {useCases.map((u) => (
              <Card key={u.title}>
                <CardHeader>
                  <u.icon className="size-6 text-primary" />
                  <CardTitle className="mt-2">{u.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{u.body}</CardDescription>
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

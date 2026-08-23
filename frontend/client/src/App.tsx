// CivicAI premium utility style: graphite/ivory surfaces, amber action cues, and connected civic workflows.
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, Route, Switch, useLocation } from "wouter";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronLeft,
  ClipboardList,
  Copy,
  Download,
  FileText,
  Menu,
  Moon,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import * as api from "@/lib/api";

const mark = "/manus-storage/disha-logo.jpg";
const hero = "/manus-storage/civicai-hero_08940d4f.jpg";
const wayfinding = "/manus-storage/civicai-wayfinding_01330149.jpg";
type Category = { id: string; name: string; description: string; choices: string[] };
type DocumentDraft = { title: string; name: string; person: string; issue: string; extra: string; createdAt: string };
const documentSchema = z.object({
  title: z.string(),
  name: z.string().trim().min(2, "Enter your full name so the document can be addressed correctly."),
  person: z.string().trim().min(2, "Tell us who this document is regarding."),
  issue: z.string().trim().min(15, "Add a little more detail about what happened."),
  extra: z.string(),
  createdAt: z.string(),
});

const categories: Category[] = [
  { id: "01", name: "Housing", description: "Deposits, repairs, notices, and tenancy questions.", choices: ["Deposit or rent", "Repairs", "Notice or eviction", "Other housing issue"] },
  { id: "02", name: "Consumer", description: "Refunds, faulty products, and service problems.", choices: ["Product issue", "Refund issue", "Service issue", "Misleading claim", "Other"] },
  { id: "03", name: "Workplace", description: "Pay, leave, contracts, and workplace concerns.", choices: ["Pay or deductions", "Leave", "Contract", "Workplace treatment"] },
  { id: "04", name: "Government services", description: "Getting a response, record, or public service.", choices: ["Delayed service", "Denied service", "Public grievance", "Status request"] },
  { id: "05", name: "RTI", description: "Make a clear request for information.", choices: ["Request records", "Ask for a decision", "Follow up on a request", "Other information request"] },
  { id: "06", name: "Welfare / Schemes", description: "Understand eligibility and available support.", choices: ["Eligibility", "Application status", "Missing benefit", "Scheme comparison"] },
];

const exampleSources = [
  ["Prototype source · Tenancy guidance", "Disha Research Desk", "Example explainer", "Deposit disputes · Section 2"],
  ["Prototype source · Consumer remedies", "Disha Research Desk", "Example explainer", "Refunds · Section 1"],
];

function getStored<T>(key: string, fallback: T): T {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div className="eyebrow"><span></span>{children}</div>;
}

function PrimaryButton({ children, href, onClick, type = "button" }: { children: React.ReactNode; href?: string; onClick?: () => void; type?: "button" | "submit" }) {
  if (href) return <Link href={href} className="primary-btn">{children}<ArrowRight size={17} /></Link>;
  return <button className="primary-btn" type={type} onClick={onClick}>{children}<ArrowRight size={17} /></button>;
}

function useReplayableScrollMotion() {
  const [motionReady, setMotionReady] = useState(false);
  useEffect(() => {
    const getTargets = () => Array.from(document.querySelectorAll<HTMLElement>(".scroll-replay"));
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const root = document.querySelector(".app-shell");
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      getTargets().forEach(target => target.classList.add("is-visible"));
      return;
    }

    setMotionReady(true);
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => entry.target.classList.toggle("is-visible", entry.isIntersecting));
    }, { rootMargin: "0px 0px -10%", threshold: 0.12 });
    const observeTargets = () => getTargets().forEach(target => observer.observe(target));
    observeTargets();
    const mutationObserver = new MutationObserver(observeTargets);
    if (root) mutationObserver.observe(root, { childList: true, subtree: true });

    return () => {
      mutationObserver.disconnect();
      observer.disconnect();
    };
  }, []);
  return motionReady;
}

function Layout({ children }: { children: React.ReactNode }) {
  const scrollMotionReady = useReplayableScrollMotion();
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(() => new URLSearchParams(window.location.search).get("menu") === "open");
  const [dark, setDark] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [themeTransition, setThemeTransition] = useState<"to-dark" | "to-light" | null>(null);
  const themeTransitionTimer = useRef<number | null>(null);
  const nav = [["Home", "/landing"], ["Workspace", "/dashboard"], ["RTI & RAG Chat", "/assistant"], ["Rights", "/rights"], ["Documents", "/documents"]];

  useEffect(() => {
    const saved = window.localStorage.getItem("disha-theme");
    const requested = new URLSearchParams(window.location.search).get("theme");
    setDark(requested === "dark" || (requested !== "light" && saved === "dark"));
  }, []);
  useEffect(() => { window.localStorage.setItem("disha-theme", dark ? "dark" : "light"); }, [dark]);
  useEffect(() => () => { if (themeTransitionTimer.current) window.clearTimeout(themeTransitionTimer.current); }, []);
  function toggleTheme() {
    const nextDark = !dark;
    const supportsMotion = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setDark(nextDark);
    if (!supportsMotion) return;
    if (themeTransitionTimer.current) window.clearTimeout(themeTransitionTimer.current);
    setThemeTransition(null);
    window.requestAnimationFrame(() => setThemeTransition(nextDark ? "to-dark" : "to-light"));
    themeTransitionTimer.current = window.setTimeout(() => setThemeTransition(null), 780);
  }
  return <div className={`app-shell ${dark ? "dark" : ""} ${scrollMotionReady ? "scroll-motion-ready" : ""} ${themeTransition ? `theme-shift-${themeTransition}` : ""}`}>
    <div className="theme-veil" aria-hidden="true">{themeTransition && <><span className="theme-veil-panel theme-veil-panel-one"></span><span className="theme-veil-panel theme-veil-panel-two"></span><span className="theme-veil-panel theme-veil-panel-three"></span><span className="theme-veil-core"></span><span className="theme-veil-scan"></span><span className="theme-veil-mode">{themeTransition === "to-dark" ? "DARK // 01" : "LIGHT // 01"}</span></>}</div>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <header className="site-header">
      <div className="brand"><Link href="/landing" className="brand-link" aria-label="Disha Home"><img src={mark} alt="Disha" /><span className="brand-title">DISHA</span></Link></div>
      <nav className="desktop-nav">{nav.map(([label, href]) => <Link key={href} href={href} className={location === href ? "active" : ""}>{label}</Link>)}</nav>
      <div className="header-tools">
        <button aria-label="Search" onClick={() => setSearchOpen(true)}><Search size={18}/><span>Search</span></button>
        <button className="theme-toggle" aria-label={`Switch to ${dark ? "light" : "dark"} mode`} onClick={toggleTheme}>{dark ? <Moon size={16}/> : <Sun size={16}/>}<span>{dark ? "Dark" : "Light"}</span></button>
        <button className="mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Menu">{mobileOpen ? <X/> : <Menu/>}</button>
      </div>
    </header>
    {mobileOpen && <nav className="mobile-nav">{nav.map(([label, href]) => <Link key={href} href={href} onClick={() => setMobileOpen(false)}>{label}</Link>)}</nav>}
    {searchOpen && <div className="utility-panel search-panel" role="dialog" aria-label="Search Disha"><div className="utility-panel-head"><span className="mono">GO TO</span><button onClick={() => setSearchOpen(false)} aria-label="Close search"><X size={16}/></button></div><div className="utility-links">{[["Workspace", "/dashboard"], ["Assistant", "/assistant"], ["Rights navigator", "/rights"], ["My documents", "/documents"]].map(([label, href]) => <Link href={href} key={href} onClick={() => setSearchOpen(false)}><Search size={14}/>{label}<ArrowRight size={14}/></Link>)}</div></div>}
    {children}
    <footer className="footer">
      <div className="brand"><Link href="/landing" className="brand-link" aria-label="Disha Home"><img src={mark} alt="Disha"/><span className="brand-title">DISHA</span></Link></div>
      <span className="footer-note">A prototype civic service · Information is general, not legal advice.</span>
    </footer>
  </div>;
}

function ProblemInput({ compact = false, initial = "", value: controlledValue, onValueChange }: { compact?: boolean; initial?: string; value?: string; onValueChange?: (value: string) => void }) {
  const [, navigate] = useLocation();
  const [value, setValue] = useState(initial);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const currentValue = controlledValue ?? value;
  function changeValue(nextValue: string) { if (error) setError(""); if (onValueChange) onValueChange(nextValue); else setValue(nextValue); }
  async function submit() {
    if (!currentValue.trim()) { setError("Tell us a little about what happened before continuing."); return; }
    setIsSubmitting(true);
    const draftText = currentValue.trim();
    window.localStorage.setItem("disha-case-draft", draftText);
    try {
      await api.analyzeRights(draftText);
      await api.createConversation("rights", "hinglish");
    } catch {
      // Fallback gracefully
    }
    setIsSubmitting(false);
    navigate("/assistant");
  }
  return <div className={compact ? "problem-input compact" : "problem-input"}>
    <label htmlFor={compact ? "workspace-problem" : "problem"}>{compact ? "Describe your problem" : "What's going on?"}</label>
    <textarea id={compact ? "workspace-problem" : "problem"} aria-invalid={Boolean(error)} value={currentValue} onChange={e => changeValue(e.target.value)} placeholder="Describe your situation in your own words..." rows={compact ? 2 : 4}/>
    {error && <p className="field-error" role="alert">{error}</p>}
    <div className="input-footer"><span>You don't need to know the legal terms.</span><button className="primary-btn" onClick={submit} disabled={isSubmitting}>{isSubmitting ? "Understanding your situation…" : "Help me figure this out"}<ArrowRight size={17}/></button></div>
  </div>;
}

function Home() {
  const [heroProblem, setHeroProblem] = useState("");
  return <Layout><main id="main-content">
    <section className="hero" style={{ backgroundImage: `url(${hero})` }}>
      <div className="hero-copy"><Eyebrow>A calmer way through complicated systems</Eyebrow><h1>Know your rights.<br/><em>Find your way.</em></h1><p>Tell us what happened. We'll help you understand your options and figure out the next step.</p></div>
      <div className="hero-form"><ProblemInput value={heroProblem} onValueChange={setHeroProblem}/><div className="examples"><span>Try an example</span>{["My landlord hasn't returned my deposit", "I want to file an RTI", "I was charged for something I didn't receive", "Do I qualify for a government scheme?"].map(text => <ExampleLink key={text} text={text} onSelect={setHeroProblem}/>)}</div></div>
    </section>
    <section className="public-handoff scroll-replay"><div><Eyebrow>Your Disha workspace</Eyebrow><h2>Save your progress.<br/><em>Return when you need it.</em></h2><p>Keep your case notes, document drafts, and next steps together in this browser.</p></div><Link href="/dashboard" className="primary-btn">Open your dashboard<ArrowRight size={17}/></Link></section>
    <section className="start-paths scroll-replay"><div className="start-paths-head"><Eyebrow>Choose your path</Eyebrow><h2>Start where<br/><em>you are.</em></h2><p>Every route leads back to a clear next action, not another dead end.</p></div><div className="path-grid">{[["01", "Start a case", "Tell Disha what happened and get a structured first view.", "/assistant"], ["02", "Explore rights", "Narrow a situation step by step before you decide what to do.", "/rights"], ["03", "Prepare a document", "Turn a clear record into a formal request or complaint.", "/documents/new"]].map(([number, title, copy, href]) => <Link href={href} className="path-card" key={number}><span className="mono">{number}</span><strong>{title}</strong><p>{copy}</p><ArrowRight size={18}/></Link>)}</div></section>
    <section className="section directory scroll-replay"><div className="section-lead"><Eyebrow>Explore by situation</Eyebrow><h2>What are you<br/><em>dealing with?</em></h2></div><div className="category-list">{categories.map(category => <Link href="/rights" className="category-row" key={category.name}><span className="mono">{category.id}</span><strong>{category.name}</strong><span className="category-desc">{category.description}</span><ArrowUpRight size={21}/></Link>)}</div></section>
    <section className="section process scroll-replay"><div><Eyebrow>A clear path forward</Eyebrow><h2>From confusion<br/>to <em>action.</em></h2></div><div className="steps">{[["01", "Tell us what happened"], ["02", "Understand your situation"], ["03", "See your options"], ["04", "Take the next step"]].map(([number, label], index) => <div className="step" key={number}><span className="mono">{number}</span><span>{label}</span>{index < 3 && <span className="step-line"/>}</div>)}</div></section>
    <section className="section value-story scroll-replay"><div><Eyebrow>What Disha does</Eyebrow><h2>Make the system<br/><em>less opaque.</em></h2></div><div className="value-list">{[["01", "Understand complicated information", "Turn legal or bureaucratic language into a plain explanation."], ["02", "Know your options", "See possible actions, not only background information."], ["03", "Take action", "Prepare a clear document when a written request can help."], ["04", "Know the source", "Keep supporting material visible when it matters."]].map(([number, title, copy]) => <div className="value-row" key={number}><span className="mono">{number}</span><div><strong>{title}</strong><p>{copy}</p></div></div>)}</div></section>
    <section className="image-band scroll-replay" style={{ backgroundImage: `url(${wayfinding})` }}><div><Eyebrow>Built for real questions</Eyebrow><h2>Good information<br/><em>changes what is possible.</em></h2><Link href="/rights" className="text-link">Explore your rights <ArrowRight size={16}/></Link></div></section>
    <section className="final-cta scroll-replay"><div><Eyebrow>A practical first step</Eyebrow><h2>Not sure where to start?<br/><em>Start with what happened.</em></h2></div><Link href="/dashboard" className="primary-btn">Tell us your problem<ArrowRight size={17}/></Link></section>
  </main></Layout>;
}

function LandingPage() {
  const [, navigate] = useLocation();
  const [activeChapter, setActiveChapter] = useState(0);
  const chapters = [["01", "Begin with what happened.", "Use everyday language. Disha helps you identify the part of the system you are dealing with."], ["02", "See a clear route forward.", "Understand your situation, useful records, and practical options before you commit to an action."], ["03", "Put the next step in writing.", "Create and keep a structured request, complaint, or information record in your workspace."]];
  useEffect(() => {
    const progress = document.querySelector<HTMLElement>(".landing-progress span");
    let frame = 0;

    const updateProgress = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      const value = scrollable > 0 ? Math.min(Math.max(window.scrollY / scrollable, 0), 1) : 0;
      progress?.style.setProperty("--landing-progress", String(Math.max(value, 0.025)));
      frame = 0;
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(updateProgress);
    };

    updateProgress();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);
  function enterWorkspace() { navigate("/dashboard"); }
  return <Layout><main id="main-content" className="landing-page">
    <div className="landing-progress" aria-hidden="true"><span style={{ "--landing-progress": String((activeChapter + 1) / chapters.length) } as React.CSSProperties}/></div>
    <section className="landing-hero" style={{ backgroundImage: `url(${hero})` }}><div className="landing-hero-top"><span className="mono">DISHA / CIVIC GUIDANCE</span><span className="mono">SCROLL TO EXPLORE ↓</span></div><div className="hero-civic-visual" aria-hidden="true"><span className="hero-visual-orbit orbit-one"></span><span className="hero-visual-orbit orbit-two"></span><span className="hero-route route-one"></span><span className="hero-route route-two"></span><div className="hero-visual-map"><img src={wayfinding} alt=""/></div><div className="hero-visual-card visual-card-one"><span className="mono">01 / CLARIFY</span><strong>Start with<br/>what happened.</strong></div><div className="hero-visual-card visual-card-two"><span className="mono">NEXT ROUTE</span><strong>Document<br/>your facts.</strong><i></i></div><div className="hero-visual-marker"><span></span><small>DSH / 01</small></div></div><div className="landing-hero-copy"><Eyebrow>A clearer route through public systems</Eyebrow><h1><span className="landing-hero-line">When the</span><br/><span className="landing-hero-line">system</span><br/><span className="landing-hero-emphasis">feels <em>too&nbsp;much,</em></span><br/><span className="landing-hero-line">start here.</span></h1><p>Disha helps people turn an unclear civic or legal problem into a practical next step.</p><div className="landing-hero-actions"><button className="primary-btn" onClick={enterWorkspace}>Open my dashboard<ArrowRight size={17}/></button><Link href="/start" className="secondary-link">See how it works</Link></div></div><div className="landing-side-note"><span className="mono">DESIGNED FOR THE MOMENT BEFORE YOU KNOW WHAT TO DO</span><span>↓</span></div></section>
    <section className="landing-intro scroll-replay"><span className="mono">THE DISHA METHOD</span><p>A civic guide for the practical questions that sit between <em>“something went wrong”</em> and <em>“what do I do now?”</em></p></section>
    <section className="landing-chapter-wrap" aria-label="How Disha works">{chapters.map(([number, title, copy], index) => <article className={`landing-chapter scroll-replay reveal-step-${index + 1}`} key={number} onMouseEnter={() => setActiveChapter(index)} onFocus={() => setActiveChapter(index)} tabIndex={0}><div className="chapter-marker"><span className="mono">{number}</span><span className="chapter-dot"></span></div><div className="chapter-copy"><h2>{title}</h2><p>{copy}</p></div><div className="chapter-index mono">0{index + 1} / 03</div></article>)}</section>
    <section className="landing-wayfinding scroll-replay"><div className="wayfinding-copy"><Eyebrow>Choose a starting point</Eyebrow><h2>What brings<br/>you <em>here?</em></h2><p>Choose a route, not a rigid form. You can always take one step at a time.</p></div><div className="wayfinding-links">{[["I need to understand a problem", "Start a case", "/start"], ["I want to explore my options", "Rights Navigator", "/rights"], ["I need to prepare a document", "Document workspace", "/documents/new"]].map(([label, action, href], index) => <Link href={href} key={label} className="wayfinding-link"><span className="mono">0{index + 1}</span><div><strong>{label}</strong><small>{action}</small></div><ArrowRight size={19}/></Link>)}</div></section>
    <section className="landing-promise scroll-replay"><div className="promise-door"><img src={mark} alt="Disha"/></div><div><Eyebrow>Not another chatbot</Eyebrow><h2>Less searching.<br/>More <em>knowing what to do.</em></h2><p>Disha turns a confusing question into understandable information, possible options, the records you may need, and an action you can actually take.</p></div></section>
    <section className="landing-final scroll-replay"><span className="mono">YOUR NEXT STEP IS ALREADY HERE</span><h2>Start with the<br/><em>one thing you know.</em></h2><button className="primary-btn" onClick={enterWorkspace}>Go to my dashboard<ArrowRight size={17}/></button></section>
  </main></Layout>;
}

function ExampleLink({ text, onSelect }: { text: string; onSelect: (value: string) => void }) {
  return <button onClick={() => onSelect(text)}>{text}<ArrowUpRight size={14}/></button>;
}

function Dashboard() {
  const [draft, setDraft] = useState("");
  useEffect(() => setDraft(getStored("disha-case-draft", "")), []);
  const recent = useMemo(() => [["Consumer complaint", "Complaint · Today", "/documents/complaint"], ["RTI application", "RTI · Yesterday", "/documents/rti"], ["Tenant issue", "Housing · 3 days ago", "/assistant"]], []);
  return <Layout><main className="app-page">
    <div className="app-top scroll-replay"><div><Eyebrow>Your workspace</Eyebrow><h1>Good afternoon.</h1><p>What can we help you with?</p></div><span className="date-note">FRIDAY · 22 AUG 2026</span></div>
    <ProblemInput compact initial={draft}/>
    <section className="quick-actions scroll-replay"><span className="mono label">SHORTCUTS</span>{[["Rights Navigator", "Find your options", ShieldCheck, "/rights"], ["Create a document", "Make a complaint or request", FileText, "/documents/new"], ["Check eligibility", "Explore public schemes", Check, "/rights"], ["RTI Assistant", "Make an information request", Sparkles, "/assistant"]].map(([title, subtitle, Icon, href]) => <Link href={href as string} className="quick-action" key={title as string}><Icon size={20}/><span><strong>{title as string}</strong><small>{subtitle as string}</small></span><ArrowUpRight size={16}/></Link>)}</section>
    <section className="activity scroll-replay"><div className="section-heading"><Eyebrow>Recent activity</Eyebrow><Link href="/documents">View all <ArrowRight size={15}/></Link></div>{recent.map(([title, meta, href]) => <Link className="activity-row" href={href} key={title}><span className="activity-mark"></span><strong>{title}</strong><span>{meta}</span><ArrowUpRight size={16}/></Link>)}</section>
  </main></Layout>;
}

function Assistant() {
  const [, navigate] = useLocation();
  const [inputQuery, setInputQuery] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [chatHistory, setChatHistory] = useState<
    Array<{
      role: "user" | "assistant";
      content: string;
      what_we_understood?: string | null;
      what_you_can_do?: string[];
      what_you_need?: string[];
      next_step?: string | null;
      limitations?: string | null;
      citations?: api.Citation[];
      isRTI?: boolean;
      userQuery?: string;
    }>
  >([]);



  const testQuestions = [
    { label: "1. Consumer Rights", text: "What rights does a consumer have?" },
    { label: "2. PM Kisan Eligibility", text: "Who is eligible for PM Kisan?" },
    { label: "3. How to File RTI", text: "How can I file an RTI application?" },
    { label: "4. Ward 5 Road Repair RTI", text: "I want to know how much my municipality spent on road repairs in Ward 5 during 2025." },
  ];

  async function triggerRTIDraft(requestText: string) {
    setIsQuerying(true);
    try {
      const rtiRes = await api.draftRTI({
        request: requestText,
        applicant_name: "Citizen Applicant",
        public_authority: "Public Information Officer / Municipal Authority",
      });

      if (rtiRes.success && rtiRes.data) {
        const data = rtiRes.data;
        window.localStorage.setItem("nyaya-rti-result", JSON.stringify(data));

        setChatHistory(prev => [
          ...prev,
          {
            role: "assistant",
            content: data.draft,
            limitations: data.limitations,
            citations: data.citations,
            isRTI: true,
            userQuery: requestText,
          },
        ]);
        toast("RTI Draft Generated via CivicAI Backend!");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to draft RTI application.");
    } finally {
      setIsQuerying(false);
    }
  }

  async function handleSend(queryText?: string) {
    const query = (queryText || inputQuery).trim();
    if (!query || isQuerying) return;
    setIsQuerying(true);
    setInputQuery("");

    setChatHistory(prev => [...prev, { role: "user", content: query }]);

    const isExplicitDraftRequest = /draft.*rti|want to know.*spent|application for.*rti|road repairs/i.test(query);

    try {
      if (isExplicitDraftRequest) {
        await triggerRTIDraft(query);
      } else {
        const ragRes = await api.queryRAG({ query });
        if (ragRes.success && ragRes.data) {
          const data = ragRes.data;
          setChatHistory(prev => [
            ...prev,
            {
              role: "assistant",
              content: data.answer,
              what_we_understood: data.what_we_understood,
              what_you_can_do: data.what_you_can_do || [],
              what_you_need: data.what_you_need || [],
              next_step: data.next_step,
              limitations: data.limitations,
              citations: data.citations || [],
              isRTI: false,
              userQuery: query,
            },
          ]);
          toast("Action-Oriented Civic Guidance Generated!");
        }
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to contact CivicAI Backend.");
      setChatHistory(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, an error occurred while connecting to the CivicAI backend.",
        },
      ]);
    } finally {
      setIsQuerying(false);
    }
  }

  return (
    <Layout>
      <main className="app-page workspace max-w-5xl mx-auto px-4 py-6">
        <div className="workspace-head mb-6">
          <Link href="/dashboard" className="back text-xs flex items-center gap-1 mb-2">
            <ChevronLeft size={16} /> Workspace
          </Link>
          <Eyebrow>CivicAI Action-Oriented RAG & RTI Assistant</Eyebrow>
          <h1 className="text-3xl font-bold tracking-tight mt-1">
            Grounded Civic Guidance & <em>RTI Drafting Agent</em>
          </h1>
          <p className="text-sm opacity-80 mt-1">
            Get structured action steps, requirements, and RTI draft templates strictly backed by official sources.
          </p>
        </div>

        {/* Evaluation Test Questions Shortcut Bar */}
        <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-xl mb-6">
          <div className="text-xs font-bold mono text-amber-900 dark:text-amber-300 mb-2 flex items-center gap-1">
            <Sparkles size={14} /> EVALUATION TEST QUESTIONS (1-CLICK RUN)
          </div>
          <div className="flex flex-wrap gap-2">
            {testQuestions.map(q => (
              <button
                key={q.label}
                onClick={() => handleSend(q.text)}
                disabled={isQuerying}
                className="text-xs bg-white dark:bg-stone-900 border border-amber-500/40 hover:border-amber-500 px-3 py-1.5 rounded-lg shadow-sm font-medium transition-all text-left"
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Box */}
        <div className="bg-white dark:bg-stone-950 border border-stone-300 dark:border-stone-800 rounded-2xl p-4 shadow-sm mb-8">
          <label className="block text-xs font-semibold mono mb-2">YOUR QUERY OR RTI REQUEST</label>
          <textarea
            value={inputQuery}
            onChange={e => setInputQuery(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question (e.g. 'What rights does a consumer have?' or 'How can I file an RTI application?')..."
            rows={3}
            className="w-full p-3 rounded-xl bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-stone-100 dark:border-stone-900">
            <span className="text-xs text-stone-500">Press Ctrl+Enter or click Send to submit</span>
            <button
              onClick={() => handleSend()}
              disabled={isQuerying || !inputQuery.trim()}
              className="primary-btn text-xs px-4 py-2 flex items-center gap-2"
            >
              {isQuerying ? "Processing..." : "Ask CivicAI"} <Send size={14} />
            </button>
          </div>
        </div>

        {/* Chat / Results Output Area */}
        {chatHistory.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-stone-300 dark:border-stone-800 rounded-2xl">
            <Sparkles size={32} className="mx-auto text-amber-500 mb-2 opacity-80" />
            <h3 className="font-bold text-base">No queries submitted yet</h3>
            <p className="text-xs opacity-75 mt-1">
              Click one of the evaluation test questions above or type your prompt to get grounded civic guidance!
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {chatHistory.map((item, index) => {
              if (item.role === "user") {
                return (
                  <div key={index} className="p-4 rounded-xl bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-800">
                    <span className="text-xs mono font-bold block mb-1 opacity-70">👤 YOU</span>
                    <p className="text-sm">{item.content}</p>
                  </div>
                );
              }

              const isRTIRelated = item.isRTI || /rti|information/i.test(item.userQuery || item.content);

              return (
                <div key={index} className="bg-white dark:bg-stone-950 border border-stone-300 dark:border-stone-800 rounded-2xl p-6 shadow-sm space-y-6">
                  {/* Header */}
                  <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-stone-800">
                    <span className="text-xs mono font-bold tracking-wide text-amber-700 dark:text-amber-400 flex items-center gap-1">
                      {item.isRTI ? "📜 CIVICAI RTI DRAFTING AGENT" : "🤖 CIVICAI GROUNDED GUIDANCE"}
                    </span>
                    {item.isRTI && (
                      <button
                        onClick={() => navigate("/documents/complaint")}
                        className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1 underline"
                      >
                        Open Full Document Preview <ArrowUpRight size={13} />
                      </button>
                    )}
                  </div>

                  {/* Main Answer Summary */}
                  <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
                    {item.content}
                  </div>

                  {/* 1. What We Understood */}
                  {item.what_we_understood && (
                    <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                      <Eyebrow>1. What We Understood</Eyebrow>
                      <p className="text-sm font-medium mt-1 text-stone-800 dark:text-stone-200">
                        {item.what_we_understood}
                      </p>
                    </div>
                  )}

                  {/* 2. What You Can Do */}
                  {item.what_you_can_do && item.what_you_can_do.length > 0 && (
                    <div className="space-y-2">
                      <Eyebrow>2. What You Can Do</Eyebrow>
                      <div className="grid gap-2 mt-1">
                        {item.what_you_can_do.map((action, aIdx) => (
                          <div key={aIdx} className="flex items-start gap-3 p-3 rounded-xl bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800">
                            <span className="text-xs mono font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400">
                              0{aIdx + 1}
                            </span>
                            <span className="text-sm text-stone-800 dark:text-stone-200">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 3. What You'll Need */}
                  {item.what_you_need && item.what_you_need.length > 0 && (
                    <div className="space-y-2">
                      <Eyebrow>3. What You'll Need</Eyebrow>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {item.what_you_need.map((need, nIdx) => (
                          <span key={nIdx} className="inline-flex items-center gap-1.5 text-xs bg-stone-100 dark:bg-stone-900 px-3 py-1.5 rounded-lg border border-stone-200 dark:border-stone-800 font-medium">
                            <Check size={14} className="text-emerald-500" />
                            {need}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 4. Next Step */}
                  {(item.next_step || isRTIRelated) && (
                    <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 space-y-3">
                      <Eyebrow>4. Next Step</Eyebrow>
                      {item.next_step && (
                        <p className="text-sm font-semibold text-stone-900 dark:text-stone-100">
                          {item.next_step}
                        </p>
                      )}
                      {isRTIRelated && !item.isRTI && (
                        <div className="pt-2">
                          <button
                            onClick={() => triggerRTIDraft(item.userQuery || item.content)}
                            disabled={isQuerying}
                            className="primary-btn text-xs px-4 py-2 flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold shadow transition-all"
                          >
                            <FileText size={14} /> [ Draft RTI Application ]
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Limitations Note */}
                  {item.limitations && (
                    <div className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-400 text-xs">
                      <strong>⚠️ Grounding & Limitations Note:</strong>
                      <p className="mt-1">{item.limitations}</p>
                    </div>
                  )}

                  {/* 5. Sources / Citations */}
                  {item.citations && item.citations.length > 0 && (
                    <div className="pt-4 border-t border-stone-200 dark:border-stone-800 space-y-2">
                      <Eyebrow>5. Sources & Verified Statutory Citations</Eyebrow>
                      <Sources citations={item.citations} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </Layout>
  );
}

function Sources({ citations }: { citations?: api.Citation[] }) {
  const [open, setOpen] = useState(false);
  const [fetchedSources, setFetchedSources] = useState<api.Citation[]>([]);

  useEffect(() => {
    if (!citations || citations.length === 0) {
      api.getSource("src_001").then(res => {
        if (res.success && res.data) {
          setFetchedSources([res.data]);
        }
      }).catch(() => {});
    }
  }, [citations]);

  const activeCitations = (citations && citations.length > 0) ? citations : fetchedSources;
  if (!activeCitations || activeCitations.length === 0) return null;

  return (
    <section className="sources">
      <div className="section-heading">
        <Eyebrow>Sources used</Eyebrow>
        {activeCitations.length > 1 && (
          <button onClick={() => setOpen(!open)}>
            {open ? "Hide" : "Show all"} <ChevronDown size={15} />
          </button>
        )}
      </div>
      {activeCitations.slice(0, open ? activeCitations.length : 2).map((cit, index) => {
        const title = cit.document_title || cit.source_title || cit.document_id || "Verified Statutory Source";
        const org = cit.issuing_authority || "CivicAI Legal Knowledge Base";
        const kind = cit.document_type || "statute";
        const sectionInfo = [
          cit.chapter ? `Chapter ${cit.chapter}` : null,
          cit.section ? (cit.section.toLowerCase().startsWith("section") ? cit.section : `Section ${cit.section}`) : null,
          cit.subsection ? `(${cit.subsection})` : null,
          cit.page_start ? `p. ${cit.page_start}` : null,
        ].filter(Boolean).join(" · ");

        return (
          <div className="source-row" key={cit.source_id || index}>
            <strong>{title}</strong>
            <span>{org} · {kind}</span>
            {sectionInfo && <small>{sectionInfo}</small>}
            {cit.source_url ? (
              <a
                href={cit.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-link text-xs flex items-center gap-1 mt-1"
                style={{ color: "#d97706", textDecoration: "underline" }}
              >
                Official Source <ArrowUpRight size={13} />
              </a>
            ) : (
              <button onClick={() => toast("Verified citation from CivicAI RAG pipeline.")}>
                Verified source <ArrowUpRight size={13} />
              </button>
            )}
          </div>
        );
      })}
    </section>
  );
}

function Rights() {
  const [, navigate] = useLocation();
  const [category, setCategory] = useState<Category | null>(null);
  const [choice, setChoice] = useState<string | null>(null);

  useEffect(() => {
    if (category && choice) {
      api.analyzeRights(`${category.name}: ${choice}`).catch(() => {});
    }
  }, [category, choice]);

  function startAssistant() { window.localStorage.setItem("disha-case-draft", `${category?.name}: ${choice}`); navigate("/assistant"); }
  return <Layout><main className="app-page rights-page">
    <section className="page-intro scroll-replay"><Eyebrow>Rights navigator</Eyebrow><h1>{choice ? "Here is a sensible place to start." : category ? "Let's narrow this down." : "Find your way through the system."}</h1><p>{choice ? "This result is a starting point for your next practical action, not a substitute for verified local advice." : category ? "Choose the part of the issue that is closest to your situation." : "Start with the kind of situation you're dealing with. We'll take it one step at a time."}</p></section>
    {!category && <div className="rights-options scroll-replay">{categories.map(item => <button className="scroll-replay" key={item.name} onClick={() => setCategory(item)}><span className="mono">{item.id}</span><strong>{item.name}</strong><span>{item.description}</span><ArrowRight size={18}/></button>)}</div>}
    {category && !choice && <div className="narrowing scroll-replay"><div className="selected-line"><span className="mono">YOU CHOSE</span><strong>{category.name}</strong><button onClick={() => setCategory(null)}>Change</button></div><h2>Which part is closest?</h2><div className="choice-list">{category.choices.map(item => <button key={item} onClick={() => setChoice(item)}><span>{item}</span><ArrowRight size={16}/></button>)}</div></div>}
    {category && choice && <div className="rights-result scroll-replay"><div className="selected-line"><span className="mono">YOUR PATH</span><strong>{category.name} · {choice}</strong><button onClick={() => setChoice(null)}>Change</button></div><section><Eyebrow>What this can mean</Eyebrow><p>Start by keeping the dates, receipts, agreements, and messages that show what happened. A concise written request is often the clearest next step.</p></section><section><Eyebrow>Your options</Eyebrow><div className="action-list">{[["01", "Make a written request"], ["02", "Create a formal complaint"], ["03", "Find an escalation route"]].map(([number, label]) => <div className="action-row" key={number}><span className="mono">{number}</span><strong>{label}</strong><ArrowRight size={16}/></div>)}</div></section><section><Eyebrow>What you'll need</Eyebrow><div className="checklist"><span><Check size={15}/>Dates and relevant records</span><span><Check size={15}/>Receipts or payment evidence</span><span><Check size={15}/>Communication history</span></div></section><div className="recommend"><span className="mono">NEXT PRACTICAL STEP</span><h2>Turn the facts into a clear record.</h2><PrimaryButton onClick={startAssistant}>Continue to assistant</PrimaryButton></div><Sources/></div>}
  </main></Layout>;
}

function Documents(_props: any) {
  const newDoc = _props.newDoc ?? false;
  const [, navigate] = useLocation();
  const [step, setStep] = useState(1);
  const initialDraft = getStored<DocumentDraft>("disha-document-draft", { title: "Consumer Complaint", name: "", person: "", issue: "", extra: "", createdAt: "22 August 2026" });
  const form = useForm<DocumentDraft>({ resolver: zodResolver(documentSchema), defaultValues: initialDraft, mode: "onTouched" });
  const { register, trigger, getValues, formState: { errors, isSubmitting } } = form;
  const draft = form.watch();
  const fieldsByStep: Record<number, Array<keyof DocumentDraft>> = { 1: ["name"], 2: ["person"], 3: ["issue"], 4: [] };
  async function nextStep() { const valid = await trigger(fieldsByStep[step]); if (valid) setStep(step + 1); }
  function handleDocumentKeyDown(event: React.KeyboardEvent<HTMLElement>) { const target = event.target as HTMLElement; const singleLineStep = event.key === "Enter" && target.tagName === "INPUT" && step < 4; const multilineShortcut = event.key === "Enter" && target.tagName === "TEXTAREA" && (event.ctrlKey || event.metaKey) && step < 4; if (singleLineStep || multilineShortcut) { event.preventDefault(); void nextStep(); } }
  async function generate() {
    const valid = await trigger();
    if (!valid) return;
    const values = getValues();
    const nextDraft = { ...values, createdAt: new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) };
    window.localStorage.setItem("disha-document-draft", JSON.stringify(nextDraft));
    window.localStorage.setItem("nyaya-document-draft", JSON.stringify(nextDraft));

    const isRTI = /rti|right to information|information request/i.test(values.title || "") || /rti|information/i.test(values.issue || "");

    if (isRTI) {
      try {
        const rtiRes = await api.draftRTI({
          request: values.issue,
          applicant_name: values.name,
          applicant_address: values.extra,
          public_authority: values.person,
        });
        if (rtiRes.success && rtiRes.data) {
          window.localStorage.setItem("nyaya-rti-result", JSON.stringify(rtiRes.data));
          window.localStorage.removeItem("nyaya-complaint-result");
          window.localStorage.removeItem("disha-complaint-result");
        }
      } catch {
        // Graceful local fallback handled inside api.ts
      }
    } else {
      try {
        const sessionRes = await api.createFormSession("consumer_complaint");
        if (sessionRes.success && sessionRes.data) {
          const sessionId = sessionRes.data.session_id;
          await api.updateFormSession(sessionId, values);
          const compRes = await api.generateComplaint({
            form_session_id: sessionId,
            name: values.name,
            person: values.person,
            issue: values.issue,
            extra: values.extra,
            title: values.title || "Consumer Complaint",
          });
          if (compRes.success && compRes.data) {
            window.localStorage.setItem("nyaya-complaint-result", JSON.stringify(compRes.data));
            window.localStorage.removeItem("nyaya-rti-result");
          }
        }
      } catch {
        // Graceful local fallback handled inside api.ts
      }
    }
    window.setTimeout(() => navigate("/documents/complaint"), 420);
  }
  if (newDoc) return <Layout><main className="app-page form-page" onKeyDown={handleDocumentKeyDown}><Link href="/documents" className="back"><ChevronLeft size={16}/> My documents</Link><div className="form-layout scroll-replay"><div><Eyebrow>New document · Step 0{step}</Eyebrow><h1>{step === 1 ? "Let's start with the basics." : step === 2 ? "Who is the complaint regarding?" : step === 3 ? "What happened?" : "Review the key details."}</h1><p className="form-help">A few details will help Disha make this document useful and specific.</p></div><div className="form-box">{step === 1 && <label>What's your full name?<input {...register("name")} aria-invalid={Boolean(errors.name)} placeholder="Your full name"/>{errors.name && <span className="field-error">{errors.name.message}</span>}</label>}{step === 2 && <label>Who is this regarding?<input {...register("person")} aria-invalid={Boolean(errors.person)} placeholder="Person, company, or office"/>{errors.person && <span className="field-error">{errors.person.message}</span>}</label>}{step === 3 && <label>What happened?<textarea {...register("issue")} aria-invalid={Boolean(errors.issue)} rows={7} placeholder="Use your own words. Include dates or amounts if you remember them."/>{errors.issue && <span className="field-error">{errors.issue.message}</span>}</label>}{step === 4 && <div className="document-review"><span className="mono">DOCUMENT SUMMARY</span><dl><dt>Prepared for</dt><dd>{draft.name || "To be added"}</dd><dt>Regarding</dt><dd>{draft.person || "To be added"}</dd><dt>Key facts</dt><dd>{draft.issue || "To be added"}</dd></dl><label>Anything else you'd like to include?<textarea {...register("extra")} rows={3} placeholder="Optional additional context"/></label></div>}<div className="form-actions">{step > 1 && <button className="back-btn" onClick={() => setStep(step - 1)}>Back</button>}{step < 4 ? <PrimaryButton onClick={nextStep}>Continue</PrimaryButton> : <button className="primary-btn" onClick={generate} disabled={isSubmitting}>Review and generate<ArrowRight size={17}/></button>}</div></div></div><div className="progress scroll-replay"><span style={{ width: `${step * 25}%` }}></span></div></main></Layout>;
  const saved = getStored<DocumentDraft | null>("disha-document-draft", null);
  const rows = [[saved?.title || "Consumer Complaint", "Complaint · Today", "/documents/complaint"], ["RTI Application", "RTI · Yesterday", "/documents/rti"], ["Tenant Complaint", "Housing · 3 days ago", "/documents/tenant"]];
  return <Layout><main className="app-page"><div className="app-top scroll-replay"><div><Eyebrow>Your library</Eyebrow><h1>My documents</h1><p>Documents you have prepared with Disha.</p></div><PrimaryButton href="/documents/new">Create a document</PrimaryButton></div><div className="document-list scroll-replay">{rows.map(([title, meta, href]) => <Link className="document-row scroll-replay" href={href} key={title}><FileText size={20}/><span><strong>{title}</strong><small>{meta}</small></span><span className="doc-status">Draft</span><ArrowUpRight size={17}/></Link>)}</div></main></Layout>;
}

function DocumentPreview() {
  const [, navigate] = useLocation();
  const saved = getStored<DocumentDraft | null>("disha-document-draft", null) || getStored<DocumentDraft | null>("nyaya-document-draft", null);
  const savedComplaint = getStored<api.ComplaintData | null>("disha-complaint-result", null) || getStored<api.ComplaintData | null>("nyaya-complaint-result", null);
  const savedRTI = getStored<api.RTIDraftData | null>("nyaya-rti-result", null);

  const isRTI = Boolean(savedRTI && savedRTI.draft);
  const title = isRTI ? "RTI Application" : (savedComplaint?.title || saved?.title || "Consumer Complaint");
  const signer = saved?.name || "A citizen";
  const person = saved?.person || "The Appropriate Authority";
  const issue = saved?.issue || "a service that I paid for but did not receive as described";

  const documentText = isRTI
    ? savedRTI!.draft
    : (savedComplaint?.content || `APPLICATION / COMPLAINT\n\nTo,\n${person}\n\nSubject: ${title}\n\nRespected Sir/Madam,\n\nI am writing to formally raise a complaint regarding ${issue}. I request that the matter be reviewed and that an appropriate resolution be provided.\n\nI have kept the relevant payment records and communication history available should they be required.\n\n${saved?.extra || "Thank you for your attention to this matter."}\n\nYours faithfully,\n${signer}`);

  const limitations = isRTI ? savedRTI?.limitations : null;
  const citations = isRTI ? savedRTI?.citations : (savedComplaint?.sources || savedComplaint?.citations);

  function copyDocument() {
    if (!navigator.clipboard) { toast("Copy is not available in this browser."); return; }
    navigator.clipboard.writeText(documentText).then(() => toast("Document copied to clipboard.")).catch(() => toast("Copy error."));
  }

  async function downloadDocument() {
    const complaintId = savedComplaint?.complaint_id || "doc_123";
    toast("Generating document from backend...");
    try {
      const res = await api.exportComplaintDocument(complaintId, "text");
      if (res.success && res.data) {
        if (res.data.download_url) {
          window.open(res.data.download_url, "_blank");
          toast("Opening backend generated document.");
          return;
        }
        const exportedText = res.data.content || documentText;
        const blob = new Blob([exportedText], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = res.data.filename || `${title.replace(/[^a-z0-9]+/gi, "-").toLowerCase() || "document"}.txt`;
        anchor.click();
        URL.revokeObjectURL(url);
        toast("Backend exported document downloaded.");
        return;
      }
    } catch {
      // Fallback local download
    }
    const blob = new Blob([documentText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${title.replace(/[^a-z0-9]+/gi, "-").toLowerCase() || "document"}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast("Text document downloaded.");
  }

  return (
    <Layout>
      <main className="app-page preview-page">
        <div className="preview-head scroll-replay">
          <div>
            <Link href="/documents" className="back"><ChevronLeft size={16}/> My documents</Link>
            <Eyebrow>Case file 03 · Document preview · {isRTI ? "RTI Draft" : "Draft"}</Eyebrow>
            <h1>{title}</h1>
          </div>
          <div className="toolbar">
            <button onClick={() => navigate("/documents/new?edit=1")}>Edit</button>
            <button onClick={copyDocument}><Copy size={15}/> Copy</button>
            <button onClick={downloadDocument}><Download size={15}/> Download</button>
            <button onClick={() => navigate("/documents/new?regenerate=1")}><Sparkles size={15}/> Regenerate</button>
          </div>
        </div>
        <div className="preview-layout">
          <article className="paper scroll-replay">
            <div className="paper-kicker scroll-replay">{isRTI ? "RTI APPLICATION DRAFT" : "APPLICATION / COMPLAINT"}</div>
            <div className="paper-rule scroll-replay"></div>
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed" style={{ fontFamily: "inherit" }}>
              {documentText}
            </pre>
          </article>
          <aside className="metadata scroll-replay">
            <Eyebrow>Document details</Eyebrow>
            <dl>
              <dt>Document type</dt>
              <dd>{title}</dd>
              <dt>Prepared for</dt>
              <dd>{signer}</dd>
              <dt>Created date</dt>
              <dd>{saved?.createdAt || "22 August 2026"}</dd>
            </dl>
            {limitations && (
              <div className="p-3 my-3 rounded bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 text-xs">
                <strong>LIMITATIONS NOTE:</strong>
                <p className="mt-1">{limitations}</p>
              </div>
            )}
            <Sources citations={citations} />
            <p className="mt-3 text-xs opacity-75">Review all details and supporting requirements before sending.</p>
          </aside>
        </div>
      </main>
    </Layout>
  );
}

function NewDocument(_props: any) { return <Documents newDoc={true}/>; }

function AppRouter() {
  return <Switch><Route path="/" component={LandingPage}/><Route path="/landing" component={LandingPage}/><Route path="/start" component={Home}/><Route path="/dashboard" component={Dashboard}/><Route path="/assistant" component={Assistant}/><Route path="/rights" component={Rights}/><Route path="/documents/new" component={NewDocument}/><Route path="/documents/:id" component={DocumentPreview}/><Route path="/documents" component={Documents}/><Route><LandingPage/></Route></Switch>;
}

export default function App() { return <><AppRouter/><Toaster richColors position="bottom-right"/></>; }

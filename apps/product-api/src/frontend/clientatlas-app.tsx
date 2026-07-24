"use client";

import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Database,
  Eye,
  FileText,
  FolderOpen,
  Gauge,
  History,
  Inbox,
  LayoutDashboard,
  Link2,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Menu,
  MoreVertical,
  PenLine,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  Trash2,
  TriangleAlert,
  Upload,
  Users,
  X
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import { createApiClient } from "@/frontend/api-client";
import {
  actionItems,
  conversations,
  documents,
  evidence,
  members,
  readinessItems,
  type DemoDocument
} from "@/frontend/demo-data";
import {
  getAccessToken,
  getSupabaseBrowserClient
} from "@/frontend/supabase-browser";

const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";
const apiClient = createApiClient({
  ...(process.env.NEXT_PUBLIC_AI_API_URL
    ? { aiBaseUrl: process.env.NEXT_PUBLIC_AI_API_URL }
    : {}),
  getAccessToken
});

type NavItem = Readonly<{
  href: string;
  icon: typeof LayoutDashboard;
  label: string;
}>;

const navItems: readonly NavItem[] = [
  { href: "/overview", icon: LayoutDashboard, label: "Overview" },
  { href: "/knowledge", icon: Database, label: "Knowledge" },
  { href: "/ask", icon: Bot, label: "Ask ClientAtlas" },
  { href: "/onboarding-brief", icon: ClipboardCheck, label: "Onboarding Brief" },
  { href: "/readiness-report", icon: BarChart3, label: "Readiness Report" },
  { href: "/action-plan", icon: CheckCircle2, label: "Action Plan" },
  { href: "/integrations", icon: Link2, label: "Integrations" },
  { href: "/members", icon: Users, label: "Members" },
  { href: "/settings", icon: Settings, label: "Settings" }
];

function pathIsActive(route: string, href: string) {
  const target = href.slice(1);
  return route === target || route.startsWith(`${target}/`);
}

function Initials({ value }: Readonly<{ value: string }>) {
  return (
    <span aria-hidden="true" className="avatar">
      {value}
    </span>
  );
}

function DemoBanner() {
  if (!demoMode) return null;
  return (
    <div className="demo-banner" role="status">
      <Eye aria-hidden="true" size={16} />
      <span>
        <strong>Synthetic read-only demonstration.</strong> All names and
        documents are fictional.
      </span>
    </div>
  );
}

function AppShell({
  children,
  route
}: Readonly<{ children: ReactNode; route: string }>) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeNavigationButton = useRef<HTMLButtonElement>(null);
  const openNavigationButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!mobileOpen) return;
    closeNavigationButton.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileOpen(false);
        openNavigationButton.current?.focus();
      }
    };
    document.body.addEventListener("keydown", closeOnEscape);
    return () => document.body.removeEventListener("keydown", closeOnEscape);
  }, [mobileOpen]);

  return (
    <div className="app-frame">
      <DemoBanner />
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-block">
          <Link aria-label="ClientAtlas overview" className="brand" href="/overview">
            <span className="brand-mark">CA</span>
            <span>
              <strong>ClientAtlas</strong>
              <small>Northstar Studio</small>
            </span>
          </Link>
          <button
            aria-label="Close navigation"
            className="icon-button mobile-only"
            onClick={() => setMobileOpen(false)}
            ref={closeNavigationButton}
            type="button"
          >
            <X aria-hidden="true" />
          </button>
        </div>

        <button
          className="button button-primary sidebar-create"
          disabled={demoMode}
          title={demoMode ? "Disabled in the read-only demonstration" : undefined}
          type="button"
        >
          <Plus aria-hidden="true" size={18} />
          New workspace
        </button>

        <nav
          aria-label="Workspace navigation"
          className="primary-nav"
          id="workspace-navigation"
        >
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                aria-current={pathIsActive(route, item.href) ? "page" : undefined}
                className={pathIsActive(route, item.href) ? "active" : ""}
                href={item.href}
                key={item.href}
                onClick={() => setMobileOpen(false)}
              >
                <Icon aria-hidden="true" size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <Link href="/system-error">
            <CircleHelp aria-hidden="true" size={20} />
            Help
          </Link>
          <Link href="/sign-in">
            <LogOut aria-hidden="true" size={20} />
            Sign out
          </Link>
        </div>
      </aside>

      {mobileOpen ? (
        <button
          aria-label="Close navigation"
          className="sidebar-scrim"
          onClick={() => setMobileOpen(false)}
          type="button"
        />
      ) : null}

      <header className="topbar">
        <button
          aria-controls="workspace-navigation"
          aria-expanded={mobileOpen}
          aria-label="Open navigation"
          className="icon-button mobile-only"
          onClick={() => setMobileOpen(true)}
          ref={openNavigationButton}
          type="button"
        >
          <Menu aria-hidden="true" />
        </button>
        <div className="workspace-switcher">
          <span>Northstar onboarding</span>
          <ChevronDown aria-hidden="true" size={16} />
        </div>
        <label className="global-search">
          <Search aria-hidden="true" size={18} />
          <span className="sr-only">Search workspace</span>
          <input placeholder="Search workspace…" type="search" />
        </label>
        <button aria-label="Help" className="icon-button" type="button">
          <CircleHelp aria-hidden="true" />
        </button>
        <button aria-label="Notifications" className="icon-button" type="button">
          <Bell aria-hidden="true" />
        </button>
        <Initials value="SC" />
      </header>

      <main className="main-content" id="main-content">
        {children}
      </main>
    </div>
  );
}

function PageHeading({
  actions,
  eyebrow,
  subtitle,
  title
}: Readonly<{
  actions?: ReactNode;
  eyebrow?: string;
  subtitle: string;
  title: string;
}>) {
  return (
    <header className="page-heading">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </header>
  );
}

function StatusBadge({
  children,
  tone = "neutral"
}: Readonly<{
  children: ReactNode;
  tone?: "danger" | "neutral" | "success" | "warning";
}>) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}

function OverviewScreen() {
  return (
    <>
      <PageHeading
        subtitle="Here is the evidence-backed status of the Northstar onboarding."
        title="Welcome back, Sarah"
      />

      <section aria-label="Workspace summary" className="metric-grid">
        <article className="metric-card readiness-card">
          <div className="card-title">
            <Gauge aria-hidden="true" />
            <h2>Readiness score</h2>
          </div>
          <div
            aria-label="Readiness score 82 percent"
            className="score-ring"
            role="img"
          >
            <strong>82%</strong>
          </div>
          <p>Two evidence gaps require attention before kickoff.</p>
        </article>
        <article className="metric-card">
          <div className="card-title">
            <TriangleAlert aria-hidden="true" className="danger-text" />
            <h2>Attention required</h2>
          </div>
          <strong className="metric-value">2</strong>
          <p>One failed source and one missing security addendum.</p>
          <Link className="text-link" href="/knowledge">
            Review documents <ArrowRight aria-hidden="true" size={16} />
          </Link>
        </article>
        <article className="metric-card">
          <div className="card-title">
            <CheckCircle2 aria-hidden="true" />
            <h2>Open action items</h2>
          </div>
          <strong className="metric-value">2</strong>
          <p>Tasks assigned across the client and delivery teams.</p>
          <Link className="text-link" href="/action-plan">
            View action plan <ArrowRight aria-hidden="true" size={16} />
          </Link>
        </article>
      </section>

      <section className="overview-lower">
        <div>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Evidence coverage</p>
              <h2>Readiness summary</h2>
            </div>
            <Link className="text-link" href="/readiness-report">
              View report
            </Link>
          </div>
          <div className="readiness-grid">
            {readinessItems.map((item) => (
              <article
                className={`readiness-item readiness-${item.status}`}
                key={item.label}
              >
                <div>
                  <span className="status-dot" />
                  <h3>{item.label}</h3>
                </div>
                <p>{item.detail}</p>
                <StatusBadge
                  tone={
                    item.status === "ready"
                      ? "success"
                      : item.status === "warning"
                        ? "warning"
                        : "danger"
                  }
                >
                  {item.status === "ready"
                    ? "Ready"
                    : item.status === "warning"
                      ? "Needs review"
                      : "Missing"}
                </StatusBadge>
              </article>
            ))}
          </div>
        </div>
        <section aria-label="Workspace activity" className="activity-card">
          <div className="card-title">
            <History aria-hidden="true" />
            <h2>Activity</h2>
          </div>
          <ol className="timeline">
            <li>
              <strong>Readiness report generated</strong>
              <span>10 minutes ago</span>
              <p>Evidence was validated across three synthetic sources.</p>
            </li>
            <li>
              <strong>Document indexed</strong>
              <span>1 hour ago</span>
              <p>Northstar_Implementation_Plan.docx is ready.</p>
            </li>
            <li>
              <strong>Ingestion needs attention</strong>
              <span>Yesterday</span>
              <p>A safe parser error was recorded for the security review.</p>
            </li>
          </ol>
        </section>
      </section>
    </>
  );
}

function DocumentDialog({
  document: sourceDocument,
  onClose
}: Readonly<{ document: DemoDocument; onClose: () => void }>) {
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeButton.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.body.addEventListener("keydown", onKeyDown);
    return () => document.body.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section
        aria-labelledby="document-dialog-title"
        aria-modal="true"
        className="modal document-modal"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <header className="modal-header">
          <div className="file-heading">
            <span className="file-icon">
              <FileText aria-hidden="true" />
            </span>
            <div>
              <h2 id="document-dialog-title">{sourceDocument.name}</h2>
              <StatusBadge
                tone={sourceDocument.state === "ready" ? "success" : "danger"}
              >
                {sourceDocument.state === "ready" ? "Indexed" : "Failed"}
              </StatusBadge>
            </div>
          </div>
          <button
            aria-label="Close document details"
            className="icon-button"
            onClick={onClose}
            ref={closeButton}
            type="button"
          >
            <X aria-hidden="true" />
          </button>
        </header>
        <div className="modal-body">
          <div className="details-grid">
            <div className="detail-panel">
              <h3>File details</h3>
              <dl>
                <div>
                  <dt>Size</dt>
                  <dd>{sourceDocument.size}</dd>
                </div>
                <div>
                  <dt>Pages</dt>
                  <dd>{sourceDocument.pages}</dd>
                </div>
                <div>
                  <dt>Type</dt>
                  <dd>{sourceDocument.type}</dd>
                </div>
                <div>
                  <dt>Chunks</dt>
                  <dd>{sourceDocument.chunks || "—"}</dd>
                </div>
              </dl>
            </div>
            <div className="detail-panel">
              <h3>Ownership and access</h3>
              <dl>
                <div>
                  <dt>Uploaded by</dt>
                  <dd>Sarah Chen</dd>
                </div>
                <div>
                  <dt>Upload date</dt>
                  <dd>{sourceDocument.uploadedAt}</dd>
                </div>
                <div>
                  <dt>Workspace</dt>
                  <dd>Northstar onboarding</dd>
                </div>
                <div>
                  <dt>Visibility</dt>
                  <dd>Workspace</dd>
                </div>
              </dl>
            </div>
          </div>
          <div className="detail-panel">
            <h3>Ingestion history</h3>
            <ol className="timeline compact-timeline">
              <li>
                <strong>
                  {sourceDocument.state === "ready"
                    ? "Indexing complete"
                    : "Processing stopped safely"}
                </strong>
                <span>{sourceDocument.uploadedAt}</span>
                <p>
                  {sourceDocument.state === "ready"
                    ? `${sourceDocument.chunks} evidence chunks are available for retrieval.`
                    : "The parser rejected an encrypted or unsupported document structure."}
                </p>
              </li>
              <li>
                <strong>File validated</strong>
                <p>Extension, content signature, MIME type, and size checked.</p>
              </li>
            </ol>
          </div>
        </div>
        <footer className="modal-footer">
          <button
            className="button button-danger-ghost"
            disabled={demoMode}
            type="button"
          >
            <Trash2 aria-hidden="true" size={18} />
            Delete document
          </button>
          <button className="button button-secondary" onClick={onClose} type="button">
            Close
          </button>
          <button className="button button-primary" disabled={demoMode} type="button">
            <RefreshCw aria-hidden="true" size={18} />
            Re-index
          </button>
        </footer>
      </section>
    </div>
  );
}

function KnowledgeScreen() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<DemoDocument | null>(null);
  const filtered = documents.filter((document) =>
    document.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <>
      <PageHeading
        actions={
          <>
            <button className="button button-secondary" disabled={demoMode} type="button">
              <FolderOpen aria-hidden="true" size={18} />
              Google Drive
            </button>
            <label
              aria-disabled={demoMode}
              className={`button button-primary ${demoMode ? "button-disabled" : ""}`}
            >
              <Upload aria-hidden="true" size={18} />
              Upload
              <input
                accept=".pdf,.docx"
                disabled={demoMode}
                hidden
                type="file"
              />
            </label>
          </>
        }
        subtitle="Manage PDF and DOCX evidence processed for onboarding."
        title="Knowledge library"
      />
      {demoMode ? (
        <p className="inline-notice">
          Upload and Google Drive import are disabled in this synthetic
          demonstration.
        </p>
      ) : null}
      <section className="table-card">
        <div className="table-toolbar">
          <label className="filter-input">
            <Search aria-hidden="true" size={18} />
            <span className="sr-only">Filter filenames</span>
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter filenames…"
              type="search"
              value={query}
            />
          </label>
          <span>{filtered.length} documents</span>
        </div>
        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Source</th>
                <th>Status</th>
                <th>Version</th>
                <th>Uploaded</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((document) => (
                <tr key={document.id}>
                  <td>
                    <button
                      className="file-button"
                      onClick={() => setSelected(document)}
                      type="button"
                    >
                      <FileText aria-hidden="true" size={19} />
                      {document.name}
                    </button>
                  </td>
                  <td>{document.type}</td>
                  <td>{document.source}</td>
                  <td>
                    <StatusBadge
                      tone={document.state === "ready" ? "success" : "danger"}
                    >
                      {document.state === "ready" ? "Ready" : "Failed"}
                    </StatusBadge>
                  </td>
                  <td>{document.version}</td>
                  <td>{document.uploadedAt}</td>
                  <td>
                    <button
                      aria-label={`Open details for ${document.name}`}
                      className="icon-button"
                      onClick={() => setSelected(document)}
                      type="button"
                    >
                      <MoreVertical aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <Inbox aria-hidden="true" />
            <h2>No matching documents</h2>
            <p>Try a different filename or clear the filter.</p>
            <button
              className="button button-secondary"
              onClick={() => setQuery("")}
              type="button"
            >
              Clear filter
            </button>
          </div>
        ) : null}
      </section>
      {selected ? (
        <DocumentDialog document={selected} onClose={() => setSelected(null)} />
      ) : null}
    </>
  );
}

function LoadingScreen({
  kind
}: Readonly<{ kind: "knowledge" | "overview" }>) {
  return (
    <>
      <PageHeading
        subtitle={
          kind === "overview"
            ? "Preparing the evidence-backed workspace summary."
            : "Loading the latest source and ingestion states."
        }
        title={kind === "overview" ? "Workspace overview" : "Knowledge library"}
      />
      <div aria-busy="true" aria-label="Loading content" className="skeleton-layout">
        <span className="sr-only">Loading content…</span>
        <div className="skeleton skeleton-wide" />
        <div className="skeleton-row">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
        <div className="skeleton skeleton-table" />
      </div>
    </>
  );
}

function KnowledgeEmptyScreen() {
  return (
    <>
      <PageHeading
        subtitle="Add the first supported document to create this workspace's evidence base."
        title="Knowledge library"
      />
      <section className="table-card">
        <div className="empty-state large-empty-state">
          <span className="state-icon">
            <FolderOpen aria-hidden="true" />
          </span>
          <h2>No documents yet</h2>
          <p>
            Upload a PDF or DOCX up to 25 MB, or select an explicitly permitted
            file through Google Drive.
          </p>
          <div className="page-actions">
            <button className="button button-secondary" disabled={demoMode} type="button">
              Google Drive
            </button>
            <button className="button button-primary" disabled={demoMode} type="button">
              <Upload aria-hidden="true" size={18} />
              Upload document
            </button>
          </div>
        </div>
      </section>
    </>
  );
}

function AskScreen() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(
    "Two milestones require attention. The technical approver must be confirmed before SSO configuration [1], and UAT must finish before the production readiness review [2]."
  );
  const [isResponding, setIsResponding] = useState(false);
  const [activeEvidence, setActiveEvidence] = useState("1");

  async function askQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) return;
    setIsResponding(true);
    setAnswer("");
    if (demoMode) {
      window.setTimeout(() => {
        setAnswer(
          "The workspace evidence identifies the missing technical approver as the immediate blocker [1]. It also shows that UAT completion is a dependency for the readiness review [2]."
        );
        setQuestion("");
        setIsResponding(false);
      }, 650);
      return;
    }

    const organizationId = window.sessionStorage.getItem(
      "clientatlas.organizationId"
    );
    const workspaceId = window.sessionStorage.getItem("clientatlas.workspaceId");
    if (!organizationId || !workspaceId) {
      setAnswer(
        "Select an authenticated organization and workspace before asking a question."
      );
      setIsResponding(false);
      return;
    }
    try {
      await apiClient.streamChat(
        organizationId,
        workspaceId,
        { question, top_k: 8 },
        (eventData) => {
          if (eventData.event === "answer") {
            const content = eventData.data.content;
            setAnswer(
              typeof content === "string"
                ? content
                : "ClientAtlas abstained because no supported answer was returned."
            );
          }
        }
      );
      setQuestion("");
    } catch {
      setAnswer(
        "ClientAtlas could not complete the request. Your question was not presented as a successful answer."
      );
    } finally {
      setIsResponding(false);
    }
  }

  return (
    <div className="chat-layout">
      <section aria-label="Recent inquiries" className="conversation-panel">
        <div className="panel-heading">
          <h1>Recent inquiries</h1>
          <button aria-label="New conversation" className="icon-button" type="button">
            <Plus aria-hidden="true" />
          </button>
        </div>
        <div className="conversation-list">
          {conversations.map((conversation, index) => (
            <button
              className={index === 0 ? "active" : ""}
              key={conversation}
              type="button"
            >
              {conversation}
            </button>
          ))}
        </div>
      </section>

      <section aria-label="Conversation" className="chat-panel">
        <div className="chat-messages" aria-live="polite">
          <div className="message message-user">
            Which onboarding milestones are currently at risk?
          </div>
          <div className="message-row">
            <span className="bot-avatar">
              <Bot aria-hidden="true" size={19} />
            </span>
            <div className="message message-assistant">
              {isResponding ? (
                <span className="responding">
                  <LoaderCircle aria-hidden="true" className="spin" />
                  Checking available evidence…
                </span>
              ) : (
                <p>{answer}</p>
              )}
              {!isResponding && answer ? (
                <div className="citation-actions">
                  {evidence.map((item) => (
                    <button
                      aria-label={`View citation ${item.id}: ${item.source}`}
                      className={activeEvidence === item.id ? "active" : ""}
                      key={item.id}
                      onClick={() => setActiveEvidence(item.id)}
                      type="button"
                    >
                      {item.id}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <form className="chat-composer" onSubmit={askQuestion}>
          <label htmlFor="chat-question">Ask a question about this workspace</label>
          <div>
            <textarea
              id="chat-question"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                demoMode
                  ? "Try a synthetic demo question…"
                  : "Ask ClientAtlas a question…"
              }
              rows={2}
              value={question}
            />
            <button
              aria-label="Send question"
              className="button button-primary square-button"
              disabled={!question.trim() || isResponding}
              type="submit"
            >
              <Send aria-hidden="true" size={19} />
            </button>
          </div>
          <small>
            Answers are plain text and may abstain when supporting evidence is
            insufficient.
          </small>
        </form>
      </section>

      <section aria-label="Citation evidence" className="evidence-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Citation {activeEvidence}</p>
            <h2>Source evidence</h2>
          </div>
          <BookOpen aria-hidden="true" />
        </div>
        {evidence
          .filter((item) => item.id === activeEvidence)
          .map((item) => (
            <article className="evidence-card" key={item.id}>
              <div className="file-heading">
                <span className="file-icon pdf-icon">
                  <FileText aria-hidden="true" />
                </span>
                <div>
                  <h3>{item.source}</h3>
                  <p>{item.locator}</p>
                </div>
              </div>
              <blockquote>{item.excerpt}</blockquote>
              <p className="evidence-note">
                Extracted text preview. Original-file opening requires a
                server-authorized signed URL.
              </p>
            </article>
          ))}
      </section>
    </div>
  );
}

function AskEmptyScreen() {
  return (
    <section className="ask-empty-screen">
      <span className="state-icon">
        <Bot aria-hidden="true" />
      </span>
      <h1>Ask ClientAtlas</h1>
      <p>
        Ask a question grounded in the documents available to this workspace.
        ClientAtlas will abstain when evidence is insufficient.
      </p>
      <div className="suggestion-grid">
        {[
          "What onboarding risks need attention?",
          "Which stakeholders are still missing?",
          "Summarize the confirmed implementation timeline."
        ].map((suggestion) => (
          <button key={suggestion} type="button">
            <Sparkles aria-hidden="true" size={17} />
            {suggestion}
          </button>
        ))}
      </div>
      <Link className="button button-primary" href="/ask">
        Open demo conversation
      </Link>
    </section>
  );
}

function EvidenceLink({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <button className="evidence-link" type="button">
      <Link2 aria-hidden="true" size={14} />
      {children}
    </button>
  );
}

function OnboardingBriefScreen() {
  const [editing, setEditing] = useState(false);
  const [savedMessage, setSavedMessage] = useState("");
  const [overview, setOverview] = useState(
    "Northstar is preparing a phased rollout of its customer onboarding platform, with a pilot focused on the enterprise implementation team."
  );

  return (
    <>
      <PageHeading
        actions={
          <>
            <button
              className="button button-secondary"
              onClick={() => setEditing((value) => !value)}
              type="button"
            >
              <PenLine aria-hidden="true" size={17} />
              {editing ? "Preview" : "Edit"}
            </button>
            <button className="button button-secondary" type="button">
              <History aria-hidden="true" size={17} />
              Version history
            </button>
            <button className="button button-primary" disabled={demoMode} type="button">
              <Sparkles aria-hidden="true" size={17} />
              Generate
            </button>
          </>
        }
        eyebrow="Northstar onboarding · Version 3"
        subtitle="Editable synthesis with evidence retained beside each claim."
        title="Onboarding brief"
      />

      <div className="alert alert-warning" role="status">
        <TriangleAlert aria-hidden="true" />
        <div>
          <strong>Missing evidence</strong>
          <p>
            Risks and dependencies need an additional source before final
            approval.
          </p>
        </div>
      </div>

      <article className="artifact-document">
        <section>
          <h2>Client overview</h2>
          {editing ? (
            <label>
              <span className="sr-only">Client overview</span>
              <textarea
                onChange={(event) => setOverview(event.target.value)}
                rows={4}
                value={overview}
              />
            </label>
          ) : (
            <p>{overview}</p>
          )}
          <EvidenceLink>Northstar_Client_Brief.pdf · p. 2</EvidenceLink>
        </section>
        <section>
          <h2>Business objectives</h2>
          <ul>
            <li>Reduce onboarding handoff time during the first quarter.</li>
            <li>Complete the pilot before the production readiness review.</li>
            <li>Provide traceable evidence for delivery decisions.</li>
          </ul>
          <EvidenceLink>Northstar_Client_Brief.pdf · p. 4</EvidenceLink>
        </section>
        <div className="artifact-columns">
          <section>
            <h2>Timeline</h2>
            <dl className="compact-list">
              <div>
                <dt>Pilot</dt>
                <dd>12 Aug 2026</dd>
              </div>
              <div>
                <dt>UAT complete</dt>
                <dd>28 Aug 2026</dd>
              </div>
              <div>
                <dt>Readiness review</dt>
                <dd>04 Sep 2026</dd>
              </div>
            </dl>
          </section>
          <section>
            <h2>Stakeholders</h2>
            <ul className="people-list">
              <li>
                <Initials value="SC" /> Sarah Chen · Sponsor
              </li>
              <li>
                <Initials value="MR" /> Marcus Reed · Delivery lead
              </li>
            </ul>
          </section>
        </div>
        <section className="missing-section">
          <h2>
            Dependencies <TriangleAlert aria-hidden="true" size={18} />
          </h2>
          <p>
            A technical approver must be nominated before the SSO workshop can
            be confirmed.
          </p>
        </section>
        <section>
          <h2>Open questions</h2>
          <ul>
            <li>Who owns the final technical approval?</li>
            <li>Which incident-response addendum applies to the pilot?</li>
          </ul>
        </section>
        {editing ? (
          <footer className="artifact-edit-footer">
            <span aria-live="polite">{savedMessage}</span>
            <button
              className="button button-secondary"
              onClick={() => setEditing(false)}
              type="button"
            >
              Cancel
            </button>
            <button
              className="button button-primary"
              disabled={demoMode}
              onClick={() => setSavedMessage("Saved as a new immutable version.")}
              type="button"
            >
              Save new version
            </button>
          </footer>
        ) : null}
      </article>
    </>
  );
}

function ReadinessReportScreen() {
  return (
    <>
      <PageHeading
        subtitle="Supported facts, missing information, and critical risks derived from workspace evidence."
        title="Readiness report"
      />
      <section className="report-layout">
        <article className="readiness-score-card">
          <p className="eyebrow">Overall readiness</p>
          <div
            aria-label="Overall readiness 82 percent"
            className="score-ring"
            role="img"
          >
            <strong>82%</strong>
          </div>
          <h2>Mostly prepared</h2>
          <p>Two evidence gaps require attention before kickoff.</p>
        </article>
        <div className="report-category-grid">
          {readinessItems.slice(0, 4).map((item) => (
            <article
              className={`report-category readiness-${item.status}`}
              key={item.label}
            >
              <div className="category-header">
                <h2>{item.label}</h2>
                <StatusBadge
                  tone={
                    item.status === "ready"
                      ? "success"
                      : item.status === "warning"
                        ? "warning"
                        : "danger"
                  }
                >
                  {item.status === "ready" ? "Confirmed" : "Needs review"}
                </StatusBadge>
              </div>
              <p>{item.detail}</p>
              <EvidenceLink>
                {item.status === "ready"
                  ? "View supporting evidence"
                  : "Review missing information"}
              </EvidenceLink>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function ActionPlanScreen() {
  return (
    <>
      <PageHeading
        actions={
          <button className="button button-primary" disabled={demoMode} type="button">
            <Plus aria-hidden="true" size={18} />
            Add action
          </button>
        }
        subtitle="Versioned tasks synthesized from readiness findings and supporting documents."
        title="Action plan"
      />
      <section className="table-card">
        <div className="table-toolbar">
          <strong>{actionItems.length} actions</strong>
          <span>Last generated 24 Jul 2026</span>
        </div>
        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Owner</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Due</th>
                <th>Evidence</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {actionItems.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.action}</strong>
                  </td>
                  <td>{item.owner}</td>
                  <td>
                    <StatusBadge
                      tone={item.priority === "High" ? "danger" : "warning"}
                    >
                      {item.priority}
                    </StatusBadge>
                  </td>
                  <td>{item.status}</td>
                  <td>{item.due}</td>
                  <td>
                    <EvidenceLink>{item.evidence}</EvidenceLink>
                  </td>
                  <td>{item.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function IntegrationsScreen() {
  return (
    <>
      <PageHeading
        subtitle="Manage the narrow external connections permitted for this workspace."
        title="Integrations"
      />
      <div className="integration-grid">
        <article className="integration-card">
          <div className="integration-heading">
            <span className="integration-icon google-drive-mark">GD</span>
            <div>
              <h2>Google Drive</h2>
              <StatusBadge tone="success">Connected in demo</StatusBadge>
            </div>
          </div>
          <dl className="connection-details">
            <div>
              <dt>Identity</dt>
              <dd>synthetic.user@example.test</dd>
            </div>
            <div>
              <dt>Scope</dt>
              <dd>
                <code>drive.file</code>
              </dd>
            </div>
            <div>
              <dt>Last import</dt>
              <dd>24 Jul 2026</dd>
            </div>
          </dl>
          <button className="button button-secondary" disabled={demoMode} type="button">
            Disconnect
          </button>
        </article>
        <article className="integration-card integration-deferred">
          <div className="integration-heading">
            <span className="integration-icon">N</span>
            <div>
              <h2>Notion</h2>
              <StatusBadge>Deferred</StatusBadge>
            </div>
          </div>
          <p>
            Notion is intentionally outside the V1 scope. This card documents the
            product roadmap without implying a working connector.
          </p>
          <button className="button button-secondary" disabled type="button">
            Not available in V1
          </button>
        </article>
      </div>
    </>
  );
}

function MembersScreen() {
  return (
    <>
      <PageHeading
        subtitle="Organization access is enforced by PostgreSQL row-level security."
        title="Members"
      />
      <section className="table-card">
        <div className="table-toolbar">
          <label className="filter-input">
            <Search aria-hidden="true" size={18} />
            <span className="sr-only">Search members</span>
            <input placeholder="Search members…" type="search" />
          </label>
          <span>{members.length} active members</span>
        </div>
        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Status</th>
                <th>
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.email}>
                  <td>
                    <div className="member-cell">
                      <Initials value={member.initials} />
                      <div>
                        <strong>{member.name}</strong>
                        <span>{member.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <select
                      aria-label={`Role for ${member.name}`}
                      defaultValue={member.role}
                      disabled={demoMode || member.role === "owner"}
                    >
                      <option value="owner">Owner</option>
                      <option value="admin">Admin</option>
                      <option value="editor">Editor</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </td>
                  <td>
                    <StatusBadge tone="success">{member.status}</StatusBadge>
                  </td>
                  <td>
                    <button
                      aria-label={`Member actions for ${member.name}`}
                      className="icon-button"
                      disabled={demoMode}
                      type="button"
                    >
                      <MoreVertical aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="inline-notice">
        <ShieldCheck aria-hidden="true" />
        <span>
          Roles are owner, admin, editor, and viewer. Email invitations are not
          exposed in V1; administrators add an existing authenticated user.
        </span>
      </div>
    </>
  );
}

function SettingsScreen() {
  return (
    <>
      <PageHeading
        subtitle="Review workspace identity, privacy routing, and active-data deletion."
        title="Workspace settings"
      />
      <div className="settings-layout">
        <section className="settings-card">
          <h2>Workspace</h2>
          <label>
            Workspace name
            <input
              defaultValue="Northstar onboarding"
              disabled={demoMode}
              type="text"
            />
          </label>
          <label>
            Description
            <textarea
              defaultValue="Synthetic workspace for demonstrating evidence-backed client onboarding."
              disabled={demoMode}
              rows={4}
            />
          </label>
        </section>
        <section className="settings-card">
          <div className="card-title">
            <LockKeyhole aria-hidden="true" />
            <h2>AI privacy mode</h2>
          </div>
          <div className="privacy-options">
            <label className="privacy-option">
              <input
                defaultChecked={!demoMode}
                disabled={demoMode}
                name="privacy-mode"
                type="radio"
              />
              <span>
                <strong>Local confidential</strong>
                <small>
                  Routes model work to the configured local Ollama service.
                </small>
              </span>
            </label>
            <label className="privacy-option">
              <input
                defaultChecked={demoMode}
                disabled={demoMode}
                name="privacy-mode"
                type="radio"
              />
              <span>
                <strong>Synthetic demonstration</strong>
                <small>
                  Only fictional material may use the free Gemini adapter.
                  Unpaid-service data may be reviewed or used for product
                  improvement under provider terms.
                </small>
              </span>
            </label>
          </div>
          <p className="security-copy">
            The server enforces provider routing. This control cannot override
            workspace privacy policy from the browser.
          </p>
        </section>
        <section className="settings-card danger-zone">
          <h2>Active-data deletion</h2>
          <p>
            Deletion removes active application records, chunks, vectors, and
            cached results. Infrastructure-provider retention limitations still
            apply.
          </p>
          <button className="button button-danger-ghost" disabled={demoMode} type="button">
            <Trash2 aria-hidden="true" size={18} />
            Review deletion
          </button>
        </section>
      </div>
    </>
  );
}

type AuthVariant = "recover" | "sign-in" | "sign-up" | "verify";

function AuthScreen({ variant }: Readonly<{ variant: AuthVariant }>) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const details = {
    recover: {
      button: "Send recovery link",
      subtitle: "We will send a secure recovery link to your email.",
      title: "Recover your account"
    },
    "sign-in": {
      button: "Sign in",
      subtitle: "Continue to your evidence-backed onboarding workspace.",
      title: "Welcome back"
    },
    "sign-up": {
      button: "Create account",
      subtitle: "Start a private local workspace or explore synthetic data.",
      title: "Create your account"
    },
    verify: {
      button: "Resend verification email",
      subtitle: "Check your inbox and verify your address to continue.",
      title: "Verify your email"
    }
  }[variant];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "");
    const password = String(form.get("password") ?? "");
    const supabase = getSupabaseBrowserClient();
    try {
      if (!supabase || demoMode) {
        if (variant === "sign-in" || variant === "sign-up") {
          router.push(variant === "sign-up" ? "/onboarding/organization" : "/overview");
        } else {
          setMessage("Synthetic demonstration: no email was sent.");
        }
        return;
      }
      if (variant === "sign-in") {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password
        });
        if (error) throw error;
        router.push("/overview");
      } else if (variant === "sign-up") {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        router.push("/verify-email");
      } else if (variant === "recover") {
        const { error } = await supabase.auth.resetPasswordForEmail(email);
        if (error) throw error;
        setMessage("Check your inbox for the next step.");
      } else {
        const { error } = await supabase.auth.resend({
          email,
          type: "signup"
        });
        if (error) throw error;
        setMessage("A new verification email was requested.");
      }
    } catch {
      setMessage("We could not complete that request. Check your details and retry.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page" id="main-content">
      <DemoBanner />
      <section className="auth-card">
        <Link className="auth-brand" href="/">
          <span className="brand-mark">CA</span>
          ClientAtlas
        </Link>
        <header>
          <h1>{details.title}</h1>
          <p>{details.subtitle}</p>
        </header>
        <form onSubmit={submit}>
          <label>
            Email address
            <input
              autoComplete="email"
              name="email"
              placeholder="you@example.com"
              required
              type="email"
            />
          </label>
          {variant === "sign-in" || variant === "sign-up" ? (
            <label>
              Password
              <input
                autoComplete={
                  variant === "sign-in" ? "current-password" : "new-password"
                }
                minLength={8}
                name="password"
                required
                type="password"
              />
            </label>
          ) : null}
          {variant === "sign-in" ? (
            <div className="form-meta">
              <Link href="/recover-password">Forgot password?</Link>
            </div>
          ) : null}
          <button className="button button-primary" disabled={busy} type="submit">
            {busy ? <LoaderCircle aria-hidden="true" className="spin" /> : null}
            {details.button}
          </button>
          <p aria-live="polite" className="form-message">
            {message}
          </p>
        </form>
        {variant === "sign-in" ? (
          <p>
            New to ClientAtlas? <Link href="/sign-up">Create an account</Link>
          </p>
        ) : null}
        {variant === "sign-up" ? (
          <p>
            Already have an account? <Link href="/sign-in">Sign in</Link>
          </p>
        ) : null}
      </section>
    </main>
  );
}

function OnboardingScreen({
  step
}: Readonly<{ step: "documents" | "members" | "organization" | "workspace" }>) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const steps = [
    ["organization", "Organization"],
    ["workspace", "Workspace"],
    ["members", "Members"],
    ["documents", "Documents"]
  ] as const;
  const index = steps.findIndex(([key]) => key === step);

  async function next(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setMessage("");
    try {
      if (!demoMode) {
        if (step === "organization") {
          const response = (await apiClient.createOrganization({
            name: String(form.get("name") ?? ""),
            slug: String(form.get("slug") ?? "")
          })) as { data?: { id?: string } };
          if (!response.data?.id) throw new Error("organization_id_missing");
          window.sessionStorage.setItem(
            "clientatlas.organizationId",
            response.data.id
          );
        } else if (step === "workspace") {
          const organizationId = window.sessionStorage.getItem(
            "clientatlas.organizationId"
          );
          if (!organizationId) throw new Error("organization_required");
          const privacyMode = String(form.get("privacyMode"));
          const response = (await apiClient.createWorkspace(organizationId, {
            description: String(form.get("description") ?? ""),
            name: String(form.get("name") ?? ""),
            privacyMode:
              privacyMode === "synthetic_demo"
                ? "synthetic_demo"
                : "local_confidential"
          })) as { data?: { id?: string } };
          if (!response.data?.id) throw new Error("workspace_id_missing");
          window.sessionStorage.setItem(
            "clientatlas.workspaceId",
            response.data.id
          );
        } else if (step === "members" && form.get("userId")) {
          const organizationId = window.sessionStorage.getItem(
            "clientatlas.organizationId"
          );
          if (!organizationId) throw new Error("organization_required");
          const requestedRole = String(form.get("role"));
          const role =
            requestedRole === "admin" || requestedRole === "editor"
              ? requestedRole
              : "viewer";
          await apiClient.setMembership(organizationId, {
            role,
            userId: String(form.get("userId"))
          });
        } else if (step === "documents") {
          const organizationId = window.sessionStorage.getItem(
            "clientatlas.organizationId"
          );
          const workspaceId = window.sessionStorage.getItem(
            "clientatlas.workspaceId"
          );
          const file = form.get("document");
          if (
            organizationId &&
            workspaceId &&
            file instanceof File &&
            file.size > 0
          ) {
            await apiClient.uploadSource(organizationId, workspaceId, file);
          }
        }
      }
    } catch {
      setMessage(
        "We could not save this step. Review the fields and authenticated workspace, then retry."
      );
      setBusy(false);
      return;
    }
    const target = steps[index + 1]?.[0];
    router.push(target ? `/onboarding/${target}` : "/overview");
    setBusy(false);
  }

  return (
    <main className="onboarding-page" id="main-content">
      <Link className="onboarding-brand" href="/">
        <span className="brand-mark">CA</span>
        ClientAtlas
      </Link>
      <ol aria-label="Setup progress" className="stepper">
        {steps.map(([key, label], itemIndex) => (
          <li
            aria-current={key === step ? "step" : undefined}
            className={
              itemIndex < index ? "complete" : itemIndex === index ? "active" : ""
            }
            key={key}
          >
            <span>{itemIndex < index ? <Check aria-hidden="true" /> : itemIndex + 1}</span>
            {label}
          </li>
        ))}
      </ol>
      <section className="onboarding-card">
        {step === "organization" ? (
          <>
            <header>
              <p className="eyebrow">Step 1 of 4</p>
              <h1>Create your organization</h1>
              <p>Your organization is the top-level tenant boundary.</p>
            </header>
            <form onSubmit={next}>
              <label>
                Organization name
                <input name="name" placeholder="Northstar Studio" required />
              </label>
              <label>
                URL slug
                <input
                  name="slug"
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  placeholder="northstar-studio"
                  required
                />
                <small>Lowercase letters, numbers, and hyphens only.</small>
              </label>
              <OnboardingActions busy={busy} first />
              <p aria-live="polite" className="form-message">
                {message}
              </p>
            </form>
          </>
        ) : null}
        {step === "workspace" ? (
          <>
            <header>
              <p className="eyebrow">Step 2 of 4</p>
              <h1>Create your first workspace</h1>
              <p>Use one workspace for each client onboarding engagement.</p>
            </header>
            <form onSubmit={next}>
              <label>
                Workspace name
                <input name="name" placeholder="Northstar onboarding" required />
              </label>
              <label>
                Description
                <textarea
                  name="description"
                  placeholder="What is the purpose of this workspace?"
                  rows={4}
                />
              </label>
              <fieldset>
                <legend>Privacy mode</legend>
                <label className="choice-row">
                  <input
                    defaultChecked
                    name="privacyMode"
                    type="radio"
                    value="local_confidential"
                  />
                  <span>
                    <strong>Local confidential</strong>
                    <small>Use local Ollama for confidential documents.</small>
                  </span>
                </label>
                <label className="choice-row">
                  <input
                    name="privacyMode"
                    type="radio"
                    value="synthetic_demo"
                  />
                  <span>
                    <strong>Synthetic demonstration</strong>
                    <small>Fictional content only.</small>
                  </span>
                </label>
              </fieldset>
              <OnboardingActions busy={busy} />
              <p aria-live="polite" className="form-message">
                {message}
              </p>
            </form>
          </>
        ) : null}
        {step === "members" ? (
          <>
            <header>
              <p className="eyebrow">Step 3 of 4</p>
              <h1>Add an existing member</h1>
              <p>
                V1 membership administration uses the authenticated user UUID.
              </p>
            </header>
            <form onSubmit={next}>
              <label>
                User UUID
                <input
                  name="userId"
                  placeholder="00000000-0000-4000-8000-000000000000"
                  type="text"
                />
              </label>
              <label>
                Role
                <select defaultValue="viewer" name="role">
                  <option value="admin">Admin</option>
                  <option value="editor">Editor</option>
                  <option value="viewer">Viewer</option>
                </select>
              </label>
              <OnboardingActions busy={busy} skip />
              <p aria-live="polite" className="form-message">
                {message}
              </p>
            </form>
          </>
        ) : null}
        {step === "documents" ? (
          <>
            <header>
              <p className="eyebrow">Step 4 of 4</p>
              <h1>Add your first document</h1>
              <p>Upload a PDF or DOCX up to 25 MB, or skip for now.</p>
            </header>
            <form onSubmit={next}>
              <label className="upload-dropzone">
                <Upload aria-hidden="true" />
                <strong>Choose a PDF or DOCX</strong>
                <span>Maximum file size: 25 MB</span>
                <input accept=".pdf,.docx" name="document" type="file" />
              </label>
              <OnboardingActions busy={busy} skip />
              <p aria-live="polite" className="form-message">
                {message}
              </p>
            </form>
          </>
        ) : null}
      </section>
    </main>
  );
}

function OnboardingActions({
  busy,
  first = false,
  skip = false
}: Readonly<{ busy: boolean; first?: boolean; skip?: boolean }>) {
  return (
    <footer className="onboarding-actions">
      {first ? <span /> : (
        <button
          className="button button-ghost"
          onClick={() => window.history.back()}
          type="button"
        >
          <ArrowLeft aria-hidden="true" size={17} />
          Back
        </button>
      )}
      {skip ? (
        <button className="button button-ghost" disabled={busy} type="submit">
          Skip for now
        </button>
      ) : null}
      <button className="button button-primary" disabled={busy} type="submit">
        {busy ? <LoaderCircle aria-hidden="true" className="spin" /> : null}
        Continue <ArrowRight aria-hidden="true" size={17} />
      </button>
    </footer>
  );
}

function PermissionDeniedScreen() {
  return (
    <div className="state-page">
      <span className="state-icon danger-state">
        <LockKeyhole aria-hidden="true" />
      </span>
      <h1>Access denied</h1>
      <p>
        You do not have permission to view this workspace. Return to an
        organization where you have an active membership.
      </p>
      <Link className="button button-primary" href="/overview">
        Return to overview
      </Link>
    </div>
  );
}

function SystemErrorScreen() {
  return (
    <div className="state-page">
      <span className="state-icon danger-state">
        <AlertCircle aria-hidden="true" />
      </span>
      <h1>We could not load this page</h1>
      <p>
        Retry the request. If the problem continues, share the safe reference
        below without including documents or access tokens.
      </p>
      <code>Reference: CA-DEMO-7F2A</code>
      <button
        className="button button-primary"
        onClick={() => window.location.reload()}
        type="button"
      >
        <RefreshCw aria-hidden="true" size={18} />
        Try again
      </button>
    </div>
  );
}

function WorkspaceScreen({ route }: Readonly<{ route: string }>) {
  const screen = useMemo(() => {
    switch (route) {
      case "knowledge":
        return <KnowledgeScreen />;
      case "knowledge/loading":
        return <LoadingScreen kind="knowledge" />;
      case "knowledge/empty":
        return <KnowledgeEmptyScreen />;
      case "ask":
        return <AskScreen />;
      case "ask/empty":
        return <AskEmptyScreen />;
      case "overview/loading":
        return <LoadingScreen kind="overview" />;
      case "onboarding-brief":
        return <OnboardingBriefScreen />;
      case "readiness-report":
        return <ReadinessReportScreen />;
      case "action-plan":
        return <ActionPlanScreen />;
      case "integrations":
        return <IntegrationsScreen />;
      case "members":
        return <MembersScreen />;
      case "settings":
        return <SettingsScreen />;
      case "permission-denied":
        return <PermissionDeniedScreen />;
      case "system-error":
        return <SystemErrorScreen />;
      default:
        return <OverviewScreen />;
    }
  }, [route]);

  return <AppShell route={route}>{screen}</AppShell>;
}

export function ClientAtlasApp({ route }: Readonly<{ route: string }>) {
  if (route === "sign-in") return <AuthScreen variant="sign-in" />;
  if (route === "sign-up") return <AuthScreen variant="sign-up" />;
  if (route === "recover-password") return <AuthScreen variant="recover" />;
  if (route === "verify-email") return <AuthScreen variant="verify" />;
  if (route.startsWith("onboarding/")) {
    const requested = route.split("/")[1];
    const step =
      requested === "workspace" ||
      requested === "members" ||
      requested === "documents"
        ? requested
        : "organization";
    return <OnboardingScreen step={step} />;
  }
  return <WorkspaceScreen route={route} />;
}

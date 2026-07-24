export type DocumentState =
  | "queued"
  | "parsing"
  | "chunking"
  | "embedding"
  | "ready"
  | "failed"
  | "deleting";

export type DemoDocument = Readonly<{
  id: string;
  name: string;
  type: "PDF" | "DOCX";
  source: "Direct upload" | "Google Drive";
  state: DocumentState;
  version: string;
  uploadedAt: string;
  pages: number;
  chunks: number;
  size: string;
}>;

export const documents: readonly DemoDocument[] = [
  {
    chunks: 84,
    id: "northstar-brief",
    name: "Northstar_Client_Brief.pdf",
    pages: 18,
    size: "2.4 MB",
    source: "Direct upload",
    state: "ready",
    type: "PDF",
    uploadedAt: "24 Jul 2026",
    version: "v2"
  },
  {
    chunks: 61,
    id: "northstar-plan",
    name: "Northstar_Implementation_Plan.docx",
    pages: 13,
    size: "680 KB",
    source: "Google Drive",
    state: "ready",
    type: "DOCX",
    uploadedAt: "24 Jul 2026",
    version: "v1"
  },
  {
    chunks: 0,
    id: "security-review",
    name: "Northstar_Security_Review.pdf",
    pages: 9,
    size: "1.1 MB",
    source: "Google Drive",
    state: "failed",
    type: "PDF",
    uploadedAt: "23 Jul 2026",
    version: "v1"
  }
];

export const readinessItems = [
  {
    detail: "Core product, operating model, and business context are supported.",
    label: "Business context",
    status: "ready"
  },
  {
    detail: "Success measures and the first-quarter targets are documented.",
    label: "Goals and objectives",
    status: "ready"
  },
  {
    detail: "A technical approver still needs to be identified.",
    label: "Stakeholders",
    status: "warning"
  },
  {
    detail: "Pilot, UAT, and go-live milestones are documented.",
    label: "Timeline",
    status: "ready"
  },
  {
    detail: "The incident-response addendum is not present in the workspace.",
    label: "Security and compliance",
    status: "missing"
  },
  {
    detail: "Salesforce and SSO dependencies are confirmed.",
    label: "Integrations",
    status: "ready"
  }
] as const;

export const actionItems = [
  {
    action: "Confirm technical approver",
    due: "29 Jul",
    evidence: "Northstar_Client_Brief.pdf · p. 7",
    id: "a1",
    notes: "Required before security sign-off.",
    owner: "Sarah Chen",
    priority: "High",
    status: "Not started"
  },
  {
    action: "Schedule SSO configuration workshop",
    due: "31 Jul",
    evidence: "Northstar_Implementation_Plan.docx · Security",
    id: "a2",
    notes: "Include the identity platform owner.",
    owner: "Marcus Reed",
    priority: "High",
    status: "In progress"
  },
  {
    action: "Validate pilot success criteria",
    due: "02 Aug",
    evidence: "Northstar_Client_Brief.pdf · p. 11",
    id: "a3",
    notes: "Review with customer success.",
    owner: "Ava Patel",
    priority: "Medium",
    status: "Complete"
  }
] as const;

export const members = [
  {
    email: "sarah.chen@example.test",
    initials: "SC",
    name: "Sarah Chen",
    role: "owner",
    status: "Active"
  },
  {
    email: "marcus.reed@example.test",
    initials: "MR",
    name: "Marcus Reed",
    role: "admin",
    status: "Active"
  },
  {
    email: "ava.patel@example.test",
    initials: "AP",
    name: "Ava Patel",
    role: "editor",
    status: "Active"
  },
  {
    email: "noah.williams@example.test",
    initials: "NW",
    name: "Noah Williams",
    role: "viewer",
    status: "Active"
  }
] as const;

export const conversations = [
  "Which milestones are at risk?",
  "Who owns the security review?",
  "What are the pilot success criteria?"
] as const;

export const evidence = [
  {
    excerpt:
      "The pilot begins on 12 August. UAT completion is required before the production readiness review.",
    id: "1",
    locator: "Page 11 · Delivery timeline",
    source: "Northstar_Client_Brief.pdf"
  },
  {
    excerpt:
      "The client must nominate a technical approver before SSO configuration and the final security sign-off.",
    id: "2",
    locator: "Security and access",
    source: "Northstar_Implementation_Plan.docx"
  }
] as const;

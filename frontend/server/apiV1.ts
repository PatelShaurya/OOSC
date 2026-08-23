import { Router } from "express";

export const apiV1Router = Router();

// In-memory data storage for stateful mock persistence
const conversationsStore = new Map<string, any>();
const formSessionsStore = new Map<string, any>();
const complaintsStore = new Map<string, any>();

// Initialize default sample data
conversationsStore.set("conv_123", {
  conversation_id: "conv_123",
  title: "Damaged phone complaint",
  service: "rights",
  language: "hinglish",
  created_at: "2026-08-22T10:00:00Z",
  updated_at: "2026-08-22T10:00:00Z",
  messages: [
    {
      id: "msg_1",
      role: "user",
      content: "Mera phone damaged aaya hai",
      created_at: "2026-08-22T10:01:00Z",
    },
    {
      id: "msg_2",
      role: "assistant",
      content: "Aapke case mein defective product se related consumer remedies available ho sakte hain...",
      sources: [
        {
          id: "src_001",
          title: "Consumer Protection Act",
          section: "Section X",
          page: 12,
          url: "https://example.gov.in/document",
        },
      ],
      created_at: "2026-08-22T10:01:02Z",
    },
  ],
});

complaintsStore.set("complaint_123", {
  complaint_id: "complaint_123",
  title: "Consumer Complaint",
  content: `APPLICATION / COMPLAINT\n\nTo,\nXYZ Electronics\n\nSubject: Consumer Complaint\n\nRespected Sir/Madam,\n\nI am writing to formally raise a complaint regarding Phone screen was damaged when delivered. I request that the matter be reviewed and that an appropriate resolution be provided.\n\nI have kept the relevant payment records and communication history available should they be required.\n\nThank you for your attention to this matter.\n\nYours faithfully,\nRahul`,
  status: "generated",
  sources: [
    {
      id: "src_001",
      title: "Consumer Protection Act",
      section: "Section X",
      page: 12,
      url: "https://example.gov.in/document",
    },
  ],
  created_at: new Date().toISOString(),
});

// Middleware for token checking helper
function getUserFromHeader(authHeader?: string) {
  if (!authHeader) {
    return { id: "user_123", name: "Rahul", email: "rahul@example.com" };
  }
  return { id: "user_123", name: "Rahul", email: "rahul@example.com" };
}

// 3. Health
apiV1Router.get("/health", (_req, res) => {
  res.json({
    success: true,
    data: {
      status: "ok",
      version: "1.0.0",
    },
  });
});

// 4. Current User
apiV1Router.get("/me", (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader && process.env.NODE_ENV === "production_strict") {
    return res.status(401).json({
      success: false,
      error: {
        code: "UNAUTHORIZED",
        message: "Not authenticated",
      },
    });
  }
  const user = getUserFromHeader(authHeader);
  res.json({
    success: true,
    data: user,
  });
});

// 5.1 Create Conversation
apiV1Router.post("/chat/conversations", (req, res) => {
  const { service = "rights", language = "hinglish" } = req.body || {};
  const conversation_id = `conv_${Date.now()}`;
  const now = new Date().toISOString();

  const conversation = {
    conversation_id,
    service,
    language,
    title: `${service.charAt(0).toUpperCase() + service.slice(1)} conversation`,
    created_at: now,
    updated_at: now,
    messages: [],
  };

  conversationsStore.set(conversation_id, conversation);

  res.status(201).json({
    success: true,
    data: {
      conversation_id,
      service,
      language,
      created_at: now,
    },
  });
});

// 5.2 List Conversations
apiV1Router.get("/chat/conversations", (_req, res) => {
  const list = Array.from(conversationsStore.values()).map(conv => ({
    conversation_id: conv.conversation_id,
    title: conv.title,
    service: conv.service,
    language: conv.language,
    updated_at: conv.updated_at,
  }));

  res.json({
    success: true,
    data: list,
  });
});

// 5.3 Get Conversation
apiV1Router.get("/chat/conversations/:conversation_id", (req, res) => {
  const { conversation_id } = req.params;
  const conversation = conversationsStore.get(conversation_id);

  if (!conversation) {
    return res.status(404).json({
      success: false,
      error: {
        code: "CONVERSATION_NOT_FOUND",
        message: `Conversation ${conversation_id} not found`,
      },
    });
  }

  res.json({
    success: true,
    data: conversation,
  });
});

// 5.4 Send Chat Message
apiV1Router.post("/chat/conversations/:conversation_id/messages", (req, res) => {
  const { conversation_id } = req.params;
  const { message } = req.body || {};

  if (!message || !message.trim()) {
    return res.status(400).json({
      success: false,
      error: {
        code: "INVALID_REQUEST",
        message: "Message content is required",
      },
    });
  }

  const conversation = conversationsStore.get(conversation_id);
  const now = new Date().toISOString();

  const userMsg = {
    id: `msg_${Date.now()}_u`,
    role: "user",
    content: message,
    created_at: now,
  };

  const isDeposit = /deposit|landlord|rent/i.test(message);
  const isConsumer = /phone|defective|product|seller|refund/i.test(message);

  const assistantContent = isDeposit
    ? "Aapke security deposit dispute ke case mein, landlord ko deduct kiya gaya amount explain karna hoga or deposit refund karna hoga. Aap formal written request bhej sakte hain."
    : isConsumer
    ? "Aapke case mein defective product se related consumer remedies available ho sakte hain. Defective product ke liye replacement ya refund claim kiya ja sakta hai."
    : "Aapke case mein relevant civic or legal guidelines apply hoti hain. Important records maintain karein aur initial written request prepare karein.";

  const assistantMsgId = `msg_${Date.now()}_a`;
  const assistantMsg = {
    message_id: assistantMsgId,
    role: "assistant",
    content: assistantContent,
    sources: [
      {
        id: "src_001",
        title: isDeposit ? "Tenancy Rights & Security Deposit Rules" : "Consumer Protection Act",
        section: isDeposit ? "Section 2" : "Section X",
        page: isDeposit ? 5 : 12,
        url: "https://example.gov.in/document",
      },
    ],
    suggested_actions: [
      "Send a written request or complaint",
      "Keep purchase receipts and communication records",
      "Escalate to consumer forum if unresolved",
    ],
  };

  if (conversation) {
    conversation.messages.push(userMsg, {
      id: assistantMsgId,
      role: "assistant",
      content: assistantContent,
      sources: assistantMsg.sources,
      created_at: now,
    });
    conversation.updated_at = now;
  }

  res.json({
    success: true,
    data: assistantMsg,
  });
});

// 6. Rights Navigator - Analyze
apiV1Router.post("/rights/analyze", (req, res) => {
  const { problem = "", language = "en" } = req.body || {};

  const isDeposit = /deposit|landlord|rent|tenant/i.test(problem);
  const isConsumer = /phone|product|seller|refund|defective|service|charged/i.test(problem);
  const isWorkplace = /pay|leave|contract|work|salary/i.test(problem);

  const summary = isDeposit
    ? "Your landlord may need to return your deposit or justify any deductions with clear receipts."
    : isConsumer
    ? "You may have consumer remedies related to defective goods or deficient services under consumer rights."
    : isWorkplace
    ? "Employers are obligated to honor wage agreements and employment notice terms."
    : "You may have administrative or legal remedies depending on the specific agreement and records available.";

  const rights = isDeposit
    ? [
        {
          title: "Right to return of security deposit",
          description: "Landlords cannot make arbitrary deductions without proof of damage beyond reasonable wear and tear.",
        },
        {
          title: "Right to written statement of deductions",
          description: "Tenant is entitled to an itemized list of any cost deducted from the deposit.",
        },
      ]
    : isConsumer
    ? [
        {
          title: "Right related to defective goods",
          description: "Consumers have a legal right to seek repair, replacement, or refund for defective items.",
        },
        {
          title: "Right to redressal against unfair trade practices",
          description: "Protection against misleading claims or refusal to honor statutory warranties.",
        },
      ]
    : [
        {
          title: "Right to administrative grievance review",
          description: "Citizens have the right to submit formal complaints and receive written responses.",
        },
      ];

  const action_plan = [
    "Contact the entity formally in writing specifying your request",
    "Gather and organize payment records, invoices, and communication history",
    "Escalate through the appropriate public grievance portal or consumer forum",
  ];

  const sources = [
    {
      id: isDeposit ? "src_002" : "src_001",
      title: isDeposit ? "Model Tenancy Act & State Rent Rules" : "Consumer Protection Act",
      section: isDeposit ? "Section 13" : "Section X",
      page: isDeposit ? 8 : 12,
      url: "https://example.gov.in/document",
    },
  ];

  res.json({
    success: true,
    data: {
      summary,
      rights,
      action_plan,
      sources,
    },
  });
});

// 7.1 List Forms
apiV1Router.get("/forms", (_req, res) => {
  res.json({
    success: true,
    data: [
      {
        id: "consumer_complaint",
        name: "Consumer Complaint",
        description: "Create a formal consumer complaint for defective goods or services.",
        category: "consumer_rights",
      },
      {
        id: "rti_application",
        name: "RTI Application",
        description: "Request official public records under the Right to Information Act.",
        category: "rti",
      },
      {
        id: "tenant_complaint",
        name: "Tenant Deposit Request",
        description: "Draft a formal request for security deposit refund or repair explanation.",
        category: "housing",
      },
    ],
  });
});

// 7.2 Get Form Definition
apiV1Router.get("/forms/:form_id", (req, res) => {
  const { form_id } = req.params;

  const definitions: Record<string, any> = {
    consumer_complaint: {
      id: "consumer_complaint",
      name: "Consumer Complaint",
      fields: [
        { id: "name", label: "Your Full Name", type: "text", required: true },
        { id: "person", label: "Opposite Party (Company / Seller)", type: "text", required: true },
        { id: "issue", label: "Describe your problem", type: "textarea", required: true },
        { id: "extra", label: "Additional context (Optional)", type: "textarea", required: false },
      ],
    },
    rti_application: {
      id: "rti_application",
      name: "RTI Application",
      fields: [
        { id: "name", label: "Applicant Name", type: "text", required: true },
        { id: "person", label: "Public Authority / Office", type: "text", required: true },
        { id: "issue", label: "Information requested", type: "textarea", required: true },
        { id: "extra", label: "Period or Reference No.", type: "text", required: false },
      ],
    },
    tenant_complaint: {
      id: "tenant_complaint",
      name: "Tenant Deposit Request",
      fields: [
        { id: "name", label: "Tenant Name", type: "text", required: true },
        { id: "person", label: "Landlord / Manager Name", type: "text", required: true },
        { id: "issue", label: "Property address and deposit details", type: "textarea", required: true },
        { id: "extra", label: "Bank details for refund", type: "text", required: false },
      ],
    },
  };

  const formDef = definitions[form_id] || definitions["consumer_complaint"];

  res.json({
    success: true,
    data: formDef,
  });
});

// 7.3 Create Form Session
apiV1Router.post("/forms/:form_id/sessions", (req, res) => {
  const { form_id } = req.params;
  const session_id = `form_session_${Date.now()}`;

  const session = {
    session_id,
    form_id,
    status: "in_progress",
    data: {},
    missing_fields: ["name", "person", "issue"],
    progress: {
      completed: 0,
      total: 3,
    },
    created_at: new Date().toISOString(),
  };

  formSessionsStore.set(session_id, session);

  res.status(201).json({
    success: true,
    data: {
      session_id,
      form_id,
      status: "in_progress",
    },
  });
});

// 7.4 Get Form Session
apiV1Router.get("/forms/sessions/:session_id", (req, res) => {
  const { session_id } = req.params;
  const session = formSessionsStore.get(session_id);

  if (!session) {
    return res.status(404).json({
      success: false,
      error: {
        code: "FORM_SESSION_NOT_FOUND",
        message: `Form session ${session_id} not found`,
      },
    });
  }

  res.json({
    success: true,
    data: session,
  });
});

// 7.5 Conversational Form Assistant
apiV1Router.post("/forms/sessions/:session_id/messages", (req, res) => {
  const { session_id } = req.params;
  const { message = "" } = req.body || {};

  const session = formSessionsStore.get(session_id) || {
    session_id,
    form_id: "consumer_complaint",
    status: "in_progress",
    data: {},
    missing_fields: ["issue"],
    progress: { completed: 2, total: 3 },
  };

  const extracted: Record<string, string> = {};
  if (message.includes("naam") || message.includes("Name")) {
    extracted.name = message.split(" ").slice(1).join(" ") || "Rahul";
  }

  session.data = { ...session.data, ...extracted };
  formSessionsStore.set(session_id, session);

  res.json({
    success: true,
    data: {
      message: "Could you please elaborate on what happened and what outcome you are requesting?",
      extracted_fields: session.data,
      missing_fields: session.missing_fields,
      progress: session.progress,
      sources: [],
    },
  });
});

// 7.6 Update Form Session
apiV1Router.patch("/forms/sessions/:session_id", (req, res) => {
  const { session_id } = req.params;
  const { data: updatedData = {} } = req.body || {};

  let session = formSessionsStore.get(session_id);
  if (!session) {
    session = {
      session_id,
      form_id: "consumer_complaint",
      status: "in_progress",
      data: {},
      missing_fields: [],
      progress: { completed: 3, total: 3 },
    };
  }

  session.data = { ...session.data, ...updatedData };
  session.status = "completed";
  formSessionsStore.set(session_id, session);

  res.json({
    success: true,
    data: {
      session_id,
      status: "completed",
      data: session.data,
    },
  });
});

// 8.1 Generate Complaint
apiV1Router.post("/complaints/generate", (req, res) => {
  const { form_session_id, language = "en", name, person, issue, extra, title: customTitle } = req.body || {};

  const session = formSessionsStore.get(form_session_id);
  const sessionData = session?.data || {};

  const signerName = name || sessionData.name || "A citizen";
  const targetPerson = person || sessionData.person || "The Appropriate Authority";
  const problemIssue = issue || sessionData.issue || "a service that I paid for but did not receive as described";
  const extraNotes = extra || sessionData.extra || "Thank you for your attention to this matter.";
  const title = customTitle || "Consumer Complaint";

  const complaint_id = `complaint_${Date.now()}`;
  const content = `APPLICATION / COMPLAINT\n\nTo,\n${targetPerson}\n\nSubject: ${title}\n\nRespected Sir/Madam,\n\nI am writing to formally raise a complaint regarding ${problemIssue}. I request that the matter be reviewed and that an appropriate resolution be provided.\n\nI have kept the relevant payment records and communication history available should they be required.\n\n${extraNotes}\n\nYours faithfully,\n${signerName}`;

  const complaintObj = {
    complaint_id,
    title,
    content,
    status: "generated",
    sources: [
      {
        id: "src_001",
        title: "Consumer Protection Act",
        section: "Section X",
        page: 12,
        url: "https://example.gov.in/document",
      },
    ],
  };

  complaintsStore.set(complaint_id, complaintObj);

  res.status(201).json({
    success: true,
    data: complaintObj,
  });
});

// 8.2 Get Complaint
apiV1Router.get("/complaints/:complaint_id", (req, res) => {
  const { complaint_id } = req.params;
  const complaint = complaintsStore.get(complaint_id) || complaintsStore.get("complaint_123");

  if (!complaint) {
    return res.status(404).json({
      success: false,
      error: {
        code: "COMPLAINT_NOT_FOUND",
        message: `Complaint ${complaint_id} not found`,
      },
    });
  }

  res.json({
    success: true,
    data: complaint,
  });
});

// 9. Sources
apiV1Router.get("/sources/:source_id", (req, res) => {
  const { source_id } = req.params;

  const sourcesMap: Record<string, any> = {
    src_001: {
      id: "src_001",
      title: "Consumer Protection Act",
      document_type: "law",
      section: "Section X",
      page: 12,
      url: "https://example.gov.in/document",
      excerpt: "Under the Consumer Protection Act, consumers have the right to file grievances regarding defective goods or deficient services.",
    },
    src_002: {
      id: "src_002",
      title: "Model Tenancy Act & State Rent Rules",
      document_type: "statute",
      section: "Section 13",
      page: 8,
      url: "https://example.gov.in/document",
      excerpt: "Security deposit shall be refunded to the tenant within one month after vacating the premises, subject to reasonable deduction for damages.",
    },
  };

  const source = sourcesMap[source_id] || sourcesMap["src_001"];

  res.json({
    success: true,
    data: source,
  });
});

// 10. Documents
apiV1Router.get("/documents/:document_id", (req, res) => {
  const { document_id } = req.params;

  res.json({
    success: true,
    data: {
      id: document_id,
      title: "Consumer Complaint",
      type: "consumer_complaint",
      status: "ready",
      download_url: `https://example.gov.in/documents/${document_id}.pdf`,
    },
  });
});

// 11. RAG Query
apiV1Router.post("/query", (req, res) => {
  const { query = "", top_k = 5, candidate_k = 10, document_type } = req.body || {};

  if (!query || !query.trim()) {
    return res.status(400).json({
      success: false,
      error: {
        code: "INVALID_REQUEST",
        message: "Query is required",
      },
    });
  }

  const isConsumer = /consumer|product|defective|refund|seller|service|charged|warranty/i.test(query);
  const isRTI = /rti|right to information|information act|public authority|pio|transparency/i.test(query);
  const isScheme = /scheme|pm kisan|kisan|eligibility|benefit|welfare|subsidy|pension|ration|bpl/i.test(query);
  const isHousing = /deposit|landlord|tenant|rent|housing|eviction|tenancy/i.test(query);
  const isWorkplace = /pay|salary|leave|contract|work|employer|labour|labor/i.test(query);

  let answer: string;
  let limitations: string | null = null;
  let citations: any[];

  if (isConsumer) {
    answer = "Under the Consumer Protection Act, 2019, consumers have several key rights:\n\n1. **Right to be protected** against marketing of goods and services which are hazardous to life and property.\n2. **Right to be informed** about the quality, quantity, potency, purity, standard and price of goods or services.\n3. **Right to choose** from a variety of goods and services at competitive prices.\n4. **Right to be heard** and assured that consumer interests will receive due consideration.\n5. **Right to seek redressal** against unfair or restrictive trade practices or exploitation.\n6. **Right to consumer education** about consumer rights and responsibilities.\n\nConsumers can file complaints at the District, State or National Consumer Disputes Redressal Commission depending on the value of goods or services.";
    citations = [
      {
        source_id: "src_cpa_001",
        document_id: "doc_cpa_2019",
        document_title: "Consumer Protection Act, 2019",
        document_type: "law",
        issuing_authority: "Ministry of Consumer Affairs, Government of India",
        chapter: "Chapter II",
        section: "Section 2(9)",
        page_start: 3,
        page_end: 5,
        source_url: "https://consumeraffairs.nic.in/acts-and-rules/consumer-protection",
      },
      {
        source_id: "src_cpa_002",
        document_id: "doc_cpa_2019",
        document_title: "Consumer Protection Act, 2019",
        document_type: "law",
        issuing_authority: "Ministry of Consumer Affairs, Government of India",
        chapter: "Chapter IV",
        section: "Section 34-37",
        page_start: 18,
        page_end: 22,
        source_url: "https://consumeraffairs.nic.in/acts-and-rules/consumer-protection",
      },
    ];
  } else if (isRTI) {
    answer = "The Right to Information Act, 2005 empowers citizens to request information from public authorities.\n\n**Key provisions:**\n\n1. **Who can file**: Any citizen of India can file an RTI application.\n2. **Fee**: ₹10 for Central Government bodies. State fees may vary.\n3. **Time limit**: The Public Information Officer (PIO) must respond within **30 days** of receiving the application.\n4. **First Appeal**: If you don't receive a response or are dissatisfied, you can file a **first appeal within 30 days** to the First Appellate Authority.\n5. **Second Appeal**: A second appeal can be filed with the Central/State Information Commission within **90 days**.\n\nThe Act covers all public authorities including government bodies, public sector undertakings, and organizations substantially financed by the government.";
    citations = [
      {
        source_id: "src_rti_001",
        document_id: "doc_rti_2005",
        document_title: "Right to Information Act, 2005",
        document_type: "law",
        issuing_authority: "Ministry of Personnel, Public Grievances and Pensions",
        chapter: "Chapter II",
        section: "Section 6",
        subsection: "6(1)",
        page_start: 4,
        page_end: 5,
        source_url: "https://rti.gov.in/rti-act.pdf",
      },
      {
        source_id: "src_rti_002",
        document_id: "doc_rti_2005",
        document_title: "Right to Information Act, 2005",
        document_type: "law",
        issuing_authority: "Ministry of Personnel, Public Grievances and Pensions",
        chapter: "Chapter V",
        section: "Section 19",
        page_start: 10,
        page_end: 11,
        source_url: "https://rti.gov.in/rti-act.pdf",
      },
    ];
  } else if (isScheme) {
    const isPMKisan = /pm kisan|kisan/i.test(query);
    if (isPMKisan) {
      answer = "**PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)** provides income support of ₹6,000 per year to eligible farmer families, paid in three equal installments of ₹2,000 each.\n\n**Eligibility:**\n- All landholding farmer families with cultivable land are eligible.\n- The benefit is given to families where the land is in the name of the farmer.\n\n**Exclusions:**\n- Institutional landholders\n- Farmer families where one or more members belong to higher economic status (e.g., income tax payers, professionals like doctors, engineers, lawyers, CAs)\n- Retired pensioners with monthly pension of ₹10,000 or more\n- Former and current holders of constitutional posts\n\n**How to apply**: Through the local patwari/revenue officer, or through the PM-KISAN portal.";
      limitations = "The retrieved sources do not contain information about the appeal process for PM-KISAN rejection. For rejection appeals, please contact your local agriculture office or the PM-KISAN helpline (155261).";
      citations = [
        {
          source_id: "src_pmk_001",
          document_id: "doc_pmkisan_guidelines",
          document_title: "PM-KISAN Scheme Operational Guidelines",
          document_type: "scheme_faq",
          issuing_authority: "Ministry of Agriculture & Farmers Welfare",
          section: "Eligibility Criteria",
          page_start: 2,
          page_end: 4,
          source_url: "https://pmkisan.gov.in/",
        },
      ];
    } else {
      answer = "There are several government welfare schemes available for eligible citizens. To help you better, please specify which scheme you are interested in (e.g., PM-KISAN, MGNREGA, PM Awas Yojana, Ayushman Bharat, etc.) or describe your situation so we can identify relevant schemes for you.";
      limitations = "The query is broad. Please specify a particular scheme for detailed eligibility information and application process.";
      citations = [];
    }
  } else if (isHousing) {
    answer = "Your landlord is required to return the security deposit within a reasonable period after vacating the premises, typically within one month. Any deductions must be justified with documented proof of damage beyond normal wear and tear.\n\n**Your rights:**\n1. Right to a written statement of any deductions made from the deposit.\n2. Right to dispute unreasonable deductions.\n3. Right to take the matter to a rent authority or civil court if the deposit is not returned.\n\n**Recommended steps:**\n1. Send a written request for the deposit refund.\n2. Keep copies of the rental agreement and payment records.\n3. If unresolved, approach the local Rent Authority or file a civil suit.";
    citations = [
      {
        source_id: "src_mta_001",
        document_id: "doc_model_tenancy_act",
        document_title: "Model Tenancy Act, 2021",
        document_type: "law",
        issuing_authority: "Ministry of Housing and Urban Affairs",
        chapter: "Chapter III",
        section: "Section 13",
        page_start: 8,
        page_end: 10,
        source_url: "https://mohua.gov.in/",
      },
    ];
  } else if (isWorkplace) {
    answer = "Under Indian labour laws, employees have rights regarding wages, working conditions, and employment terms.\n\n**Key rights include:**\n1. Right to timely payment of wages (Payment of Wages Act, 1936).\n2. Right to minimum wages (Minimum Wages Act, 1948).\n3. Right to leave and holidays.\n4. Protection against unfair dismissal.\n\nIf your employer is violating these rights, you can approach the Labour Commissioner or file a complaint with the labour court.";
    citations = [
      {
        source_id: "src_lab_001",
        document_id: "doc_labour_code",
        document_title: "Code on Wages, 2019",
        document_type: "law",
        issuing_authority: "Ministry of Labour and Employment",
        section: "Section 17",
        page_start: 12,
        page_end: 14,
        source_url: "https://labour.gov.in/",
      },
    ];
  } else {
    answer = "Based on your query, here is what we can share:\n\nCitizens have the right to seek administrative remedies through formal grievance mechanisms. A clear written request is often the most effective first step. Keep all relevant documents, receipts, and communication records organized.\n\nIf your question is about a specific civic or legal topic, try describing your situation in more detail, or choose from these categories:\n- Consumer rights\n- Housing/tenancy\n- RTI (Right to Information)\n- Government schemes\n- Workplace issues";
    limitations = "The query could not be matched to a specific legal domain. Please provide more context or specify the topic area for a more targeted response.";
    citations = [];
  }

  res.json({
    success: true,
    data: {
      query,
      answer,
      limitations,
      citations,
    },
  });
});

// 12. RTI Draft
apiV1Router.post("/rti/draft", (req, res) => {
  const {
    request: rtiRequest = "",
    applicant_name,
    address,
    public_authority,
  } = req.body || {};

  if (!rtiRequest || !rtiRequest.trim()) {
    return res.status(400).json({
      success: false,
      error: {
        code: "INVALID_REQUEST",
        message: "RTI request description is required",
      },
    });
  }

  const nameField = applicant_name || "[Applicant Name]";
  const addressField = address || "[Applicant Address]";
  const authorityField = public_authority || "[Name of the Public Authority]";

  const draft = `APPLICATION UNDER THE RIGHT TO INFORMATION ACT, 2005

To,
The Public Information Officer,
${authorityField}

Subject: Request for Information under RTI Act, 2005

Respected Sir/Madam,

I, ${nameField}, resident of ${addressField}, would like to seek the following information under the Right to Information Act, 2005:

1. ${rtiRequest.trim()}

I am an Indian citizen and this request is being made under Section 6(1) of the Right to Information Act, 2005.

I am willing to pay the prescribed fee for obtaining this information. Please provide the information in writing or in electronic format as applicable.

If the requested information is held by or relates to another public authority, I request that this application be transferred to the concerned authority under Section 6(3) of the Act within the prescribed time.

I request you to provide the above information within 30 days as stipulated under Section 7(1) of the RTI Act, 2005.

Thanking you,

Yours faithfully,
${nameField}
${addressField}
Date: [Date]

Encl: Fee of ₹10 (Ten Rupees) by [Indian Postal Order / Demand Draft / Cash]`;

  const limitations = applicant_name && address && public_authority
    ? null
    : "Some fields in this draft are marked as placeholders (e.g., [Applicant Name], [Applicant Address], [Name of the Public Authority]). Please fill in the actual details before submitting the application.";

  res.status(201).json({
    success: true,
    data: {
      draft,
      limitations,
      citations: [
        {
          source_id: "src_rti_draft_001",
          document_id: "doc_rti_2005",
          document_title: "Right to Information Act, 2005",
          document_type: "law",
          issuing_authority: "Ministry of Personnel, Public Grievances and Pensions",
          chapter: "Chapter II",
          section: "Section 6",
          subsection: "6(1)",
          page_start: 4,
          page_end: 5,
          source_url: "https://rti.gov.in/rti-act.pdf",
        },
        {
          source_id: "src_rti_draft_002",
          document_id: "doc_rti_2005",
          document_title: "Right to Information Act, 2005",
          document_type: "law",
          issuing_authority: "Ministry of Personnel, Public Grievances and Pensions",
          chapter: "Chapter III",
          section: "Section 7",
          subsection: "7(1)",
          page_start: 6,
          page_end: 7,
          source_url: "https://rti.gov.in/rti-act.pdf",
        },
      ],
    },
  });
});

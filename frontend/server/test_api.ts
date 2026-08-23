import express from "express";
import { apiV1Router } from "./apiV1";

const app = express();
app.use(express.json());
app.use("/api/v1", apiV1Router);

const server = app.listen(0, async () => {
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 3000;
  const baseUrl = `http://localhost:${port}/api/v1`;

  async function check(name: string, path: string, method: string = "GET", body: any = null) {
    const opts: RequestInit = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${baseUrl}${path}`, opts);
    const json: any = await res.json();
    console.log(`[TEST] ${name} ${method} ${path} -> Status: ${res.status}, Success: ${json.success}`);
    if (!json.success) {
      console.error(`  Error:`, json.error);
      process.exit(1);
    }
    return json;
  }

  try {
    await check("Health", "/health");
    await check("Me", "/me");
    await check("Create Conversation", "/chat/conversations", "POST", { service: "rights", language: "hinglish" });
    await check("List Conversations", "/chat/conversations");
    await check("Get Conversation", "/chat/conversations/conv_123");
    await check("Send Chat Message", "/chat/conversations/conv_123/messages", "POST", { message: "Mera phone damaged aaya hai" });
    await check("Analyze Rights", "/rights/analyze", "POST", { problem: "I bought a defective phone and the seller refuses replacement." });
    await check("List Forms", "/forms");
    await check("Get Form Def", "/forms/consumer_complaint");
    const sessionRes = await check("Create Form Session", "/forms/consumer_complaint/sessions", "POST");
    const sessionId = sessionRes.data.session_id;
    await check("Get Form Session", `/forms/sessions/${sessionId}`);
    await check("Form Session Message", `/forms/sessions/${sessionId}/messages`, "POST", { message: "Mera naam Rahul hai" });
    await check("Update Form Session", `/forms/sessions/${sessionId}`, "PATCH", { data: { name: "Rahul", issue: "Damaged phone screen" } });
    const compRes = await check("Generate Complaint", "/complaints/generate", "POST", { form_session_id: sessionId });
    const complaintId = compRes.data.complaint_id;
    await check("Get Complaint", `/complaints/${complaintId}`);
    await check("Get Source", "/sources/src_001");
    await check("Get Document", "/documents/doc_123");
    console.log("\n=======================================================");
    console.log("  ALL 17 CIVICAI API V1 ENDPOINTS PASSED VERIFICATION!");
    console.log("=======================================================\n");
  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    server.close();
  }
});

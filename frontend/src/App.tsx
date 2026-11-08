import { FormEvent, useEffect, useState, type ReactNode } from "react";
import { api, errorMessage, kycProcessingTimeoutMs, Order, Product, Profile, Quote } from "./api";

type View = "home" | "advisor" | "catalogue" | "recommendations" | "feasibility" | "quote" | "kyc" | "orders" | "operations";
type Message = { role: string; content: string };
type WorkspaceRole = "customer" | "sales" | "kyc_reviewer" | "partner";
type Lead = { lead_id: string; business_name: string; contact_name: string; contact_phone: string; city: string; segment: string; status: string; created_at: string; archived_at?: string | null };

const initialProfile: Profile = { business_type: "", segment: "", city_tier: 0 as 1 | 2, employees: 0, sites: 0, gstin_active: false };

function App() {
  const [view, setView] = useState<View>("home");
  const [role, setRole] = useState<WorkspaceRole>((localStorage.getItem("bizflow_workspace") as WorkspaceRole) || "customer");
  const [notice, setNotice] = useState("");
  const [leadId, setLeadId] = useState(localStorage.getItem("bizflow_lead") ?? "");
  const [profile, setProfile] = useState<Profile>(initialProfile);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [order, setOrder] = useState<Order | null>(null);

  const flash = (message: string) => { setNotice(message); window.setTimeout(() => setNotice(""), 5000); };
  const go = (next: View) => setView(next);
  function changeWorkspace(next: WorkspaceRole) {
    setRole(next);
    localStorage.setItem("bizflow_workspace", next);
    setView(next === "partner" ? "operations" : next === "customer" ? "home" : "operations");
  }
  function selectLead(id: string) {
    setLeadId(id);
    localStorage.setItem("bizflow_lead", id);
    setProfile(initialProfile);
    setRecommendation(null);
    setQuote(null);
    setOrder(null);
    setView("advisor");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => go("home")}><span className="brand-mark">A</span><span>Accel <b>BizFlow</b></span></button>
        <nav className="topnav">
          {role === "customer" ? <><button className={view === "home" ? "active" : ""} onClick={() => go("home")}>Overview</button><button className={view === "catalogue" ? "active" : ""} onClick={() => go("catalogue")}>Catalogue</button><button className={view === "orders" ? "active" : ""} onClick={() => go("orders")}>Tracker</button></> : <button className="active" onClick={() => go("operations")}>{role === "sales" ? "Sales desk" : role === "kyc_reviewer" ? "Review queue" : "Operations"}</button>}
        </nav>
        <div className="role-switch"><span>Demo workspace</span><select value={role} onChange={(e) => changeWorkspace(e.target.value as WorkspaceRole)}><option value="customer">Customer</option><option value="sales">Sales</option><option value="kyc_reviewer">KYC reviewer</option><option value="partner">Partner ops</option></select></div>
      </header>
      {notice && <div className="toast">{notice}</div>}
      <main>
        {view === "home" && <Home leadId={leadId} onStart={() => go("advisor")} onSelectLead={selectLead} flash={flash} />}
        {view === "advisor" && <Advisor leadId={leadId} profile={profile} setProfile={setProfile} onProfile={(p) => { setProfile(p); go("recommendations"); }} flash={flash} />}
        {view === "catalogue" && <Catalogue flash={flash} />}
        {view === "recommendations" && <Recommendations profile={profile} recommendation={recommendation} setRecommendation={setRecommendation} onQuote={(q) => { setQuote(q); go("feasibility"); }} flash={flash} />}
        {view === "feasibility" && <Feasibility quote={quote} onContinue={() => go("quote")} flash={flash} />}
        {view === "quote" && <QuoteBuilder profile={profile} quote={quote} setQuote={setQuote} onAccepted={(q) => { setQuote(q); go("kyc"); }} flash={flash} />}
        {view === "kyc" && <Kyc quote={quote} onOrder={(o) => { setOrder(o); go("orders"); }} flash={flash} />}
        {view === "orders" && <Orders order={order} setOrder={setOrder} flash={flash} />}
        {view === "operations" && <Operations role={role} flash={flash} />}
      </main>
      <footer><span>Accel BizFlow v2.0</span><span>Prototype services are simulated and use synthetic data.</span></footer>
    </div>
  );
}

function Home({ leadId, onStart, onSelectLead, flash }: { leadId: string; onStart: () => void; onSelectLead: (id: string) => void; flash: (s: string) => void }) {
  const [form, setForm] = useState({ business_name: "", contact_name: "", contact_phone: "", city: "", segment: "Professional offices" });
  const [leads, setLeads] = useState<Lead[]>([]);
  const [showForm, setShowForm] = useState(!leadId);
  const [saving, setSaving] = useState(false);
  async function refresh() { try { const { data } = await api.get("/leads"); setLeads(data); } catch (error) { flash(errorMessage(error)); } }
  useEffect(() => { refresh(); }, []);
  async function submit(e: FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      const { data } = await api.post("/leads", form);
      onSelectLead(data.lead_id); flash(`Lead ${data.lead_id} created. Your discovery session is ready.`);
      onStart();
    } catch (error) { flash(errorMessage(error)); } finally { setSaving(false); refresh(); }
  }
  async function archive(id: string) { try { await api.post(`/leads/${id}/archive`); if (id === leadId) localStorage.removeItem("bizflow_lead"); await refresh(); flash("Lead archived. Its linked records remain available for audit."); } catch (error) { flash(errorMessage(error)); } }
  async function remove(id: string) {
    if (!window.confirm("Permanently delete this unlinked draft lead? Linked records can only be archived.")) return;
    try { await api.delete(`/leads/${id}`); await refresh(); flash("Lead permanently deleted."); } catch (error) { flash(errorMessage(error)); }
  }
  return <section className="hero-grid">
    <div className="hero-copy"><div className="eyebrow">MSME acquisition, connected</div><h1>Move from business need to activation with confidence.</h1><p className="lede">BizFlow brings discovery, eligible products, transparent quotes, verification and fulfilment into one guided journey.</p><div className="hero-actions"><button className="button primary" onClick={() => document.getElementById("lead-form")?.scrollIntoView({ behavior: "smooth" })}>Start onboarding <span>→</span></button><button className="button ghost" onClick={async () => { try { await api.post("/assistance", { stage: "landing", lead_id: leadId || null, reason: "Customer requested specialist help before onboarding." }); flash("Specialist request created and sent to Partner Ops."); } catch (e) { flash(errorMessage(e)); } }}>Talk to a specialist</button></div><div className="trust-row"><span><i className="dot green" />Deterministic eligibility</span><span><i className="dot blue" />Transparent pricing</span><span><i className="dot amber" />Human handoff</span></div></div>
    <div className="hero-panel"><div className="panel-kicker">A clearer path for your business</div><div className="journey"><JourneyStep n="01" title="Discover" text="Tell us what your business needs." active /><JourneyStep n="02" title="Configure" text="See only eligible products and bundles." /><JourneyStep n="03" title="Activate" text="Verify, pay and track installation." /></div><div className="panel-foot"><span className="status-pill simulated">SIMULATED SERVICES</span><span>Built for synthetic case data</span></div></div>
    <div id="lead-form" className="card lead-card"><div><div className="eyebrow">My business leads</div><h2>Manage onboarding journeys</h2><p className="muted">Each lead has an independent discovery context and persisted records.</p><button className="button primary" onClick={() => setShowForm(true)}>+ New lead</button></div><div className="lead-list">{leads.map(lead => <div className="lead-row" key={lead.lead_id}><div><b>{lead.business_name}</b><span>{lead.segment} · {lead.city}</span><small>{lead.status} · created {new Date(lead.created_at).toLocaleDateString()}</small></div><div className="lead-actions"><button className="text-button" onClick={() => { onSelectLead(lead.lead_id); onStart(); }}>Continue</button><button className="text-button" onClick={() => archive(lead.lead_id)}>Archive</button><button className="text-button danger-text" onClick={() => remove(lead.lead_id)}>Delete</button></div></div>)}{leads.length === 0 && <Empty title="No active leads" text="Create a lead to begin a separate customer journey." />}</div>{showForm && <form onSubmit={submit} className="form-grid lead-form"><Field label="Business name"><input required value={form.business_name} onChange={e => setForm({ ...form, business_name: e.target.value })} placeholder="e.g. Balaji Dental Care" /></Field><Field label="Contact name"><input required value={form.contact_name} onChange={e => setForm({ ...form, contact_name: e.target.value })} placeholder="Your name" /></Field><Field label="Phone"><input required value={form.contact_phone} onChange={e => setForm({ ...form, contact_phone: e.target.value })} placeholder="+91 98..." /></Field><Field label="City"><input required value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} placeholder="Jaipur" /></Field><Field label="Business segment"><select value={form.segment} onChange={e => setForm({ ...form, segment: e.target.value })}><option>Professional offices</option><option>Multi-site businesses</option><option>Micro retail and services</option><option>Small manufacturers</option></select></Field><button disabled={saving} className="button primary form-submit">{saving ? "Creating…" : "Create lead & start discovery →"}</button></form>}</div>
  </section>;
}

function JourneyStep({ n, title, text, active }: { n: string; title: string; text: string; active?: boolean }) { return <div className={`journey-step ${active ? "current" : ""}`}><span>{n}</span><div><b>{title}</b><small>{text}</small></div></div>; }
function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}</label>; }

function Advisor({ leadId, profile, setProfile, onProfile, flash }: { leadId: string; profile: Profile; setProfile: (p: Profile) => void; onProfile: (p: Profile) => void; flash: (s: string) => void }) {
  const sessionKey = `bizflow_session_${leadId}`;
  const [sessionId, setSessionId] = useState(localStorage.getItem(sessionKey) ?? "");
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!leadId) return;
    if (!sessionId) api.post("/advisor/sessions", { lead_id: leadId }).then(({ data }) => { setSessionId(data.session_id); localStorage.setItem(sessionKey, data.session_id); }).catch(e => flash(errorMessage(e)));
    else api.get(`/advisor/sessions/${sessionId}`).then(({ data }) => { setMessages(data.messages); if (data.profile) setProfile(data.profile); }).catch(e => flash(errorMessage(e)));
  }, [leadId]);
  async function send(e?: FormEvent) {
    e?.preventDefault(); if (!text.trim() || !sessionId) return; const value = text; setText(""); setMessages(m => [...m, { role: "user", content: value }]); setLoading(true);
    try { const { data } = await api.post(`/advisor/sessions/${sessionId}/messages`, { message: value }); setMessages(m => [...m, { role: "assistant", content: data.reply }]); if (data.profile) setProfile(data.profile); } catch (error) { flash(errorMessage(error)); } finally { setLoading(false); }
  }
  const ready = Boolean(profile.business_type && profile.segment && profile.city_tier && profile.employees && profile.sites);
  return <section className="workspace"><PageHeader eyebrow="Guided discovery" title="Tell us about your business" description="Use English, Hindi or Hinglish. BizFlow extracts information, then the backend validates every recommendation." /><div className="two-col"><div className="card chat-card"><div className="chat-head"><div><b>BizFlow advisor</b><span>Structured discovery • local provider fallback available</span></div><span className="live-dot">● Online</span></div><div className="chat-body">{messages.length === 0 && <div className="welcome-message"><span className="avatar">A</span><div><b>Namaste — tell me about your business.</b><p>For example: “I run a clinic in Jaipur with 12 employees and one location.”</p></div></div>}{messages.map((m, i) => <div key={i} className={`message ${m.role}`}><span className="avatar">{m.role === "user" ? "You" : "A"}</span><div>{m.content}</div></div>)}{loading && <div className="message assistant"><span className="avatar">A</span><div className="typing">Thinking <i /> <i /> <i /></div></div>}</div><form onSubmit={send} className="chat-input"><input value={text} onChange={e => setText(e.target.value)} placeholder="Describe your business or answer the next question…" /><button className="button primary" disabled={loading}>Send</button></form></div><ProfilePanel profile={profile} ready={ready} onContinue={() => onProfile(profile)} /></div></section>;
}

function ProfilePanel({ profile, ready, onContinue }: { profile: Profile; ready: boolean; onContinue: () => void }) { return <aside className="card profile-panel"><div className="panel-title"><span>What we understand</span><span className="status-pill">LIVE</span></div><div className="profile-list"><ProfileRow label="Business type" value={profile.business_type || "Missing"} /><ProfileRow label="Segment" value={profile.segment || "Missing"} /><ProfileRow label="City tier" value={profile.city_tier ? `Tier ${profile.city_tier}` : "Missing"} /><ProfileRow label="Employees" value={profile.employees ? String(profile.employees) : "Missing"} /><ProfileRow label="Locations" value={profile.sites ? String(profile.sites) : "Missing"} /><ProfileRow label="GSTIN" value={profile.gstin_active ? "Active" : ready ? "Not available" : "Missing"} /></div><div className="panel-note">Values are validated by the backend before recommendations are generated.</div><button disabled={!ready} className="button secondary full" onClick={onContinue}>Review eligible products →</button></aside>; }
function ProfileRow({ label, value }: { label: string; value: string }) { return <div className="profile-row"><span>{label}</span><b>{value || "Missing"}</b></div>; }

function Catalogue({ flash }: { flash: (s: string) => void }) {
  const [products, setProducts] = useState<Product[]>([]); const [query, setQuery] = useState(""); const [category, setCategory] = useState("All");
  useEffect(() => { api.get("/catalog/products").then(r => setProducts(r.data.products)).catch(e => flash(errorMessage(e))); }, []);
  const categories = ["All", ...Array.from(new Set(products.map(p => p.category)))];
  const shown = products.filter(p => (category === "All" || p.category === category) && `${p.product_name} ${p.description} ${p.product_id}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="workspace"><PageHeader eyebrow="Catalogue intelligence" title="Products built for business" description="Every product below comes from the live catalogue service. Eligibility is assessed separately for your profile." /><div className="toolbar"><input className="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search products…" /><div className="filter-tabs">{categories.map(c => <button className={category === c ? "selected" : ""} key={c} onClick={() => setCategory(c)}>{c}</button>)}</div></div><div className="product-grid">{shown.map(p => <ProductCard key={p.product_id} product={p} />)}</div>{shown.length === 0 && <Empty title="No products found" text="Try another search or category." />}</section>;
}
function ProductCard({ product: p }: { product: Product }) { return <article className="product-card"><div className="product-top"><span className="product-id">{p.product_id}</span><span className="category">{p.category}</span></div><h3>{p.product_name}</h3><p>{p.description || "Business service from the Accel catalogue."}</p><div className="price">₹{p.price_min_inr_per_month.toLocaleString()}–₹{p.price_max_inr_per_month.toLocaleString()} <small>/ month</small></div><div className="product-meta"><span>{p.unit}</span><span>{p.min_contract_months} mo contract</span><span>Setup ₹{p.one_time_setup_inr.toLocaleString()}</span></div><div className="requirements">{p.requires_gstin && <span>GSTIN required</span>}{p.requires_one_of.length > 0 && <span>Requires {p.requires_one_of.join(", ")}</span>}</div></article>; }

function Feasibility({ quote, onContinue, flash }: { quote: Quote | null; onContinue: () => void; flash: (s: string) => void }) {
  const [location, setLocation] = useState("Jaipur");
  const [result, setResult] = useState<{ status: string; reason: string; scheduling_available: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  async function check() {
    setLoading(true);
    try {
      const { data } = await api.post("/feasibility/check", { locations: [location] });
      setResult(data.sites[0]);
    } catch (error) { flash(errorMessage(error)); } finally { setLoading(false); }
  }
  return <section className="workspace"><PageHeader eyebrow="Simulated feasibility" title="Check service feasibility" description="This simulated response is not a live network-coverage guarantee." /><div className="card feasibility-card"><div className="inline-form"><input value={location} onChange={e => setLocation(e.target.value)} placeholder="Service location" /><button className="button primary" onClick={check} disabled={loading}>{loading ? "Checking…" : "Check feasibility"}</button></div>{result && <div className={`result ${result.status.toLowerCase()}`}><b>{result.status.split("_").join(" ")}</b><p>{result.reason}</p><small>{result.scheduling_available ? "Scheduling can continue." : "Human assistance is required before scheduling."}</small>{!result.scheduling_available && <button className="button ghost full" onClick={async () => { try { await api.post("/assistance", { stage: "feasibility", lead_id: localStorage.getItem("bizflow_lead"), reason: result.reason }); flash("Feasibility assistance request created."); } catch (e) { flash(errorMessage(e)); } }}>Request human assistance</button>}</div>}<button className="button secondary" onClick={onContinue} disabled={!result || !quote}>Continue to quote →</button></div></section>;
}

function Recommendations({ profile, recommendation, setRecommendation, onQuote, flash }: { profile: Profile; recommendation: any; setRecommendation: (v: any) => void; onQuote: (q: Quote) => void; flash: (s: string) => void }) {
  const [loading, setLoading] = useState(false);
  async function evaluate() { setLoading(true); try { const { data } = await api.post("/recommendations/evaluate", { profile }); setRecommendation(data); } catch (e) { flash(errorMessage(e)); } finally { setLoading(false); } }
  useEffect(() => { if (!recommendation) evaluate(); }, []);
  const eligible: Product[] = recommendation?.eligible_products?.map((x: any) => x.product) ?? [];
  async function choose(ids: string[]) { try { const quantities = new Map((recommendation.eligible_products ?? []).map((d: any) => [d.product.product_id, d.recommended_quantity ?? 1])); const { data } = await api.post("/quotes", { profile, items: ids.map(product_id => ({ product_id, quantity: quantities.get(product_id) ?? 1 })) }); onQuote(data); } catch (e) { flash(errorMessage(e)); } }
  return <section className="workspace"><PageHeader eyebrow="Deterministic recommendations" title="A bundle that fits your business" description="The backend checks segment, city tier, employees, sites, GSTIN and product dependencies." action={<button className="button secondary" onClick={evaluate}>{loading ? "Rechecking…" : "Re-evaluate"}</button>} />{recommendation ? <><div className="bundle-grid">{recommendation.bundles.map((b: any, i: number) => <div className={`bundle-card ${i === 1 ? "featured" : ""}`} key={b.name}><div className="bundle-label">{i === 1 && <span className="recommended">BEST MATCH</span>}<span>{b.name}</span></div><h3>{b.name === "essential" ? "Start with the essentials" : b.name === "recommended" ? "A balanced business setup" : "Ready for scale"}</h3><ul>{b.product_ids.map((id: string) => <li key={id}><span className="check">✓</span>{eligible.find(p => p.product_id === id)?.product_name ?? id}</li>)}</ul><button className={`button ${i === 1 ? "primary" : "secondary"} full`} onClick={() => choose(b.product_ids)}>Build this quote →</button></div>)}</div><div className="card decisions"><div className="panel-title"><span>Eligibility decisions</span><span className="muted">{recommendation.eligible_products.length} eligible · {recommendation.ineligible_products.length} unavailable</span></div><div className="decision-table">{[...(recommendation.eligible_products ?? []), ...(recommendation.ineligible_products ?? [])].map((d: any) => <div className="decision-row" key={d.product.product_id}><span className={d.eligible ? "check" : "cross"}>{d.eligible ? "✓" : "×"}</span><b>{d.product.product_name}</b><span className="muted">{d.eligible ? `Recommended quantity: ${d.recommended_quantity}` : d.reasons.join(" ")}</span></div>)}</div></div></> : <Loading text="Evaluating your business profile…" />}</section>;
}

function QuoteBuilder({ profile, quote, setQuote, onAccepted, flash }: { profile: Profile; quote: Quote | null; setQuote: (q: Quote | null) => void; onAccepted: (q: Quote) => void; flash: (s: string) => void }) {
  const [ids, setIds] = useState<string[]>(quote?.items.map(i => i.product_id) ?? []); const [saving, setSaving] = useState(false);
  async function save() { setSaving(true); try { const { data } = quote ? await api.patch(`/quotes/${quote.quote_id}/items`, { items: ids.map(product_id => ({ product_id, quantity: quote.items.find(i => i.product_id === product_id)?.quantity ?? 1 })) }) : await api.post("/quotes", { profile, items: ids.map(product_id => ({ product_id, quantity: 1 })) }); setQuote(data); } catch (e) { flash(errorMessage(e)); } finally { setSaving(false); } }
  async function accept() { if (!quote) return; try { const { data } = await api.post(`/quotes/${quote.quote_id}/accept`); setQuote(data); onAccepted(data); } catch (e) { flash(errorMessage(e)); } }
  if (!quote) return <section className="workspace"><PageHeader eyebrow="Quote builder" title="Your quote is waiting" description="Choose a bundle from Recommendations to create a backend-calculated quote." /><div className="empty-card"><span className="empty-icon">₹</span><h2>No quote selected</h2><p>Return to recommendations and choose a valid bundle.</p></div></section>;
  return <section className="workspace"><PageHeader eyebrow={`Quote ${quote.quote_id}`} title="A transparent commercial proposal" description="All totals below are returned by the versioned pricing service." /><div className="quote-layout"><div className="card quote-lines"><div className="panel-title"><span>Line items</span><span className="status-pill">{quote.status}</span></div>{quote.items.map(item => <div className="quote-line" key={item.product_id}><div><b>{item.product_name}</b><span>{item.product_id} · quantity {item.quantity} · {item.min_contract_months}-month contract</span></div><strong>₹{item.monthly_total_inr}<small>/mo</small></strong></div>)}<div className="quote-note">Pricing version: {quote.pricing_version}. Accepted quotes are immutable.</div></div><div className="card quote-summary"><span className="eyebrow">Quote summary</span><div className="total-row"><span>Monthly recurring</span><strong>₹{quote.monthly_total_inr}</strong></div><div className="total-row"><span>One-time setup</span><strong>₹{quote.setup_total_inr}</strong></div><div className="divider" /><button className="button primary full" disabled={quote.status === "ACCEPTED"} onClick={accept}>{quote.status === "ACCEPTED" ? "Quote accepted" : "Accept quote →"}</button><button className="button secondary full" disabled={saving || quote.status === "ACCEPTED"} onClick={save}>{saving ? "Saving…" : "Recalculate through backend"}</button></div></div></section>;
}

function Kyc({ quote, onOrder, flash }: { quote: Quote | null; onOrder: (o: Order) => void; flash: (s: string) => void }) {
  const [applicant, setApplicant] = useState(""); const [consented, setConsented] = useState(false); const [status, setStatus] = useState<any>(null); const [fileName, setFileName] = useState("K01_gst_certificate.png"); const [upload, setUpload] = useState<File | null>(null); const [processing, setProcessing] = useState(false);
  async function create() { try { const { data } = await api.post("/kyc/cases", { applicant_id: applicant || `APP-${Date.now()}`, granted: false }); setApplicant(data.applicant_id); } catch (e) { flash(errorMessage(e)); } }
  async function consent() { try { await api.post(`/kyc/cases/${applicant}/consent`, { applicant_id: applicant, granted: true }); setConsented(true); flash("Purpose-specific consent recorded."); } catch (e) { flash(errorMessage(e)); } }
  async function process() { setProcessing(true); try { const { data } = await api.post(`/kyc/cases/${applicant}/documents`, { document_type: "gst_certificate", file_name: fileName }, { timeout: kycProcessingTimeoutMs }); setStatus(data); if (quote?.status === "ACCEPTED") { const orderResponse = await api.post("/orders", { quote_id: quote.quote_id, applicant_id: applicant, location: "Jaipur" }); onOrder(orderResponse.data); } } catch (e) { flash(errorMessage(e)); } finally { setProcessing(false); } }
  async function processUpload() { if (!upload) return; setProcessing(true); try { const body = new FormData(); body.append("document_type", "gst_certificate"); body.append("file", upload); const { data } = await api.post(`/kyc/cases/${applicant}/documents/upload`, body, { timeout: kycProcessingTimeoutMs }); setStatus(data); } catch (e) { flash(errorMessage(e)); } finally { setProcessing(false); } }
  return <section className="workspace"><PageHeader eyebrow="Smart KYC" title="Verify your business, privately" description="Synthetic documents are processed locally. Low-confidence results are routed to human review, never silently rejected." /><div className="kyc-layout"><div className="card kyc-main">{!applicant ? <div className="kyc-start"><span className="step-number">01</span><h2>Open a verification case</h2><p>We will request only the documents needed to support your onboarding.</p><button className="button primary" onClick={create}>Start KYC case →</button></div> : <><div className="kyc-case-id">Case <b>{applicant}</b></div><div className="consent-box"><div><b>Purpose-specific consent</b><p>I consent to local processing of my business documents for onboarding verification.</p></div><button className={`toggle ${consented ? "on" : ""}`} onClick={consent}>{consented ? "Consented" : "Give consent"}</button></div><div className="doc-list">{["gst_certificate", "udyam_certificate", "address_proof", "signatory_id"].map((doc, i) => <div className={`doc-row ${i === 0 ? "active" : ""}`} key={doc}><span className="doc-icon">▤</span><div><b>{doc.split("_").join(" ")}</b><small>{i === 0 ? "Selected synthetic specimen" : "Required document"}</small></div>{i === 0 && <select value={fileName} onChange={e => setFileName(e.target.value)}><option>K01_gst_certificate.png</option><option>K04_gst_certificate.png</option><option>K07_gst_certificate.png</option><option>K01_address_proof.png</option></select>}</div>)}</div><div className="inline-form"><button disabled={!consented || processing} className="button primary" onClick={process}>{processing ? "Processing locally…" : "Process selected specimen"}</button><input type="file" accept=".png,.jpg,.jpeg" onChange={e => setUpload(e.target.files?.[0] ?? null)} /><button disabled={!consented || !upload || processing} className="button secondary" onClick={processUpload}>Upload document</button></div>{status && <div className={`result ${status.status.toLowerCase()}`}><b>{status.status.split("_").join(" ")}</b><p>{status.reason}</p>{status.status !== "VERIFIED" && <button className="button ghost full" onClick={async () => { try { await api.post("/assistance", { stage: "kyc", applicant_id: applicant, lead_id: localStorage.getItem("bizflow_lead"), reason: status.reason }); flash("KYC assistance request created for reviewer follow-up."); } catch (e) { flash(errorMessage(e)); } }}>Request reviewer assistance</button>}</div>}</>}</div><aside className="card kyc-side"><div className="eyebrow">Your privacy</div><h3>Built for trust</h3><ul className="clean-list"><li>Documents stay in private local storage.</li><li>Raw identity data is not sent to the advisor.</li><li>Every decision has an auditable reason.</li><li>Manual review is available for exceptions.</li></ul></aside></div></section>;
}

function Orders({ order, setOrder, flash }: { order: Order | null; setOrder: (o: Order) => void; flash: (s: string) => void }) {
  const [orderId, setOrderId] = useState(order?.order_id ?? "");
  async function load() { try { const { data } = await api.get(`/orders/${orderId}`); setOrder(data); } catch (e) { flash(errorMessage(e)); } }
  async function pay(outcome: "SUCCESS" | "FAILURE") { if (!order) return; try { const { data } = await api.post(`/orders/${order.order_id}/payment`, { outcome }); setOrder(data); } catch (e) { flash(errorMessage(e)); } }
  async function transition(newState: string) { if (!order) return; try { const { data } = await api.post(`/orders/${order.order_id}/transition`, { new_state: newState, reason: `Customer advanced from ${order.status}.`, actor: "customer-demo" }); setOrder(data); } catch (e) { flash(errorMessage(e)); } }
  async function schedule() { if (!order) return; try { const { data } = await api.post(`/orders/${order.order_id}/installation`, { location: "Jaipur" }); setOrder(data); } catch (e) { flash(errorMessage(e)); } }
  const next = order && ({ QUOTE_ACCEPTED: "KYC_PENDING", KYC_PENDING: "KYC_VERIFIED", KYC_VERIFIED: "FEASIBILITY_CLEARED", FEASIBILITY_CLEARED: "PAYMENT_PENDING", PAYMENT_FAILED: "PAYMENT_PENDING", PAYMENT_CONFIRMED: "INSTALLATION_SCHEDULED", INSTALLATION_SCHEDULED: "INSTALLATION_IN_PROGRESS", INSTALLATION_IN_PROGRESS: "SERVICE_INSTALLED", SERVICE_INSTALLED: "ACTIVATED" } as Record<string, string>)[order.status];
  return <section className="workspace"><PageHeader eyebrow="Activation tracker" title="See every next step" description="The tracker is derived from persisted order events. Payment and installation are simulated." />{!order ? <div className="card lookup-card"><h2>Retrieve an order</h2><p className="muted">Enter the order ID returned after creation.</p><div className="inline-form"><input value={orderId} onChange={e => setOrderId(e.target.value)} placeholder="Order ID" /><button className="button primary" onClick={load}>Load tracker</button></div></div> : <div className="tracker-layout"><div className="card tracker-card"><div className="tracker-head"><div><span className="eyebrow">Order {order.order_id}</span><h2>{order.status.split("_").join(" ")}</h2></div><span className="status-pill">{order.payment_status}</span></div><div className="timeline">{order.events.map((event, i) => <div className="timeline-item" key={`${event.at}-${i}`}><span className="timeline-dot" /><div><b>{event.new_state.split("_").join(" ")}</b><p>{event.reason}</p><small>{new Date(event.at).toLocaleString()} · {event.actor}</small></div></div>)}</div></div><aside className="card payment-card"><span className="eyebrow">Next action</span><h3>Move this order forward</h3><p className="muted">Actions call the persisted backend state machine.</p>{next && next === "PAYMENT_PENDING" && <button className="button secondary full" onClick={() => transition(next)}>Prepare payment</button>}{next && next !== "PAYMENT_PENDING" && next !== "INSTALLATION_SCHEDULED" && <button className="button secondary full" onClick={() => transition(next)}>Advance to {next.split("_").join(" ")}</button>}{order.status === "PAYMENT_PENDING" && <><button className="button primary full" onClick={() => pay("SUCCESS")}>Simulate success</button><button className="button danger full" onClick={() => pay("FAILURE")}>Simulate failure</button></>}{order.status === "PAYMENT_CONFIRMED" && <button className="button primary full" onClick={schedule}>Schedule installation</button>}{order.status === "PAYMENT_FAILED" && <button className="button primary full" onClick={() => transition("PAYMENT_PENDING")}>Retry payment</button>}</aside></div>}</section>;
}

function Operations({ role, flash }: { role: string; flash: (s: string) => void }) {
  const [queue, setQueue] = useState<any>(null); const [funnel, setFunnel] = useState<any>(null); const [loading, setLoading] = useState(true);
  useEffect(() => {
    const queueRequest = role === "sales"
      ? api.get("/sales/queue")
      : role === "kyc_reviewer"
        ? api.get("/partner/queue", { params: { case_type: "kyc" } })
        : api.get("/partner/queue");
    Promise.all([queueRequest, api.get("/analytics/funnel")]).then(([q, f]) => {
      setQueue(q.data); setFunnel(f.data);
    }).catch(e => flash(errorMessage(e))).finally(() => setLoading(false));
  }, [role]);
  if (loading) return <section className="workspace"><Loading text="Loading operations workspace…" /></section>;
  async function assign(item: any) {
    try {
      const token = (await api.post("/auth/token", { identity: "partner-demo", role: "partner" })).data.access_token;
      localStorage.setItem("bizflow_token", token);
      await api.post("/partner/assignments", { case_type: item.case_type, case_id: item.case_id, owner: "partner-demo" });
      setQueue((await api.get("/partner/queue")).data);
      flash(`Case ${item.case_id} assigned to partner-demo.`);
    } catch (error) { flash(errorMessage(error)); }
  }
  const historical = funnel?.historical_baseline;
  const workspaceTitle = role === "sales" ? "Sales desk" : role === "kyc_reviewer" ? "KYC review queue" : "Exceptions, queues and evidence";
  const workspaceDescription = role === "sales" ? "Review persisted live cases, discovery status and follow-up work." : role === "kyc_reviewer" ? "Review KYC and onboarding exceptions before they reach activation." : `Workspace role: ${role}. Historical case data and live prototype records are shown separately.`;
  return <section className="workspace"><PageHeader eyebrow={`${role} workspace`} title={workspaceTitle} description={workspaceDescription} /><div className="metric-grid"><Metric label="Historical leads" value={historical?.leads ?? "Not available"} note="Case baseline" /><Metric label="Activations" value={historical?.activated ?? "Not available"} note="Historical baseline" /><Metric label="Conversion" value={historical ? `${(historical.conversion_rate * 100).toFixed(2)}%` : "Not available"} note="Not a forecast" /><Metric label="Open cases" value={queue?.total ?? 0} note={role === "sales" ? "Live lead follow-ups" : role === "kyc_reviewer" ? "KYC exceptions" : "Live prototype queue"} /></div><div className="card ops-table"><div className="panel-title"><span>{role === "sales" ? "Sales follow-up queue" : role === "kyc_reviewer" ? "KYC exception queue" : "Partner queue"}</span><span className="status-pill">LIVE PROTOTYPE</span></div>{queue?.items?.length ? queue.items.map((item: any) => <div className="ops-row" key={`${item.case_type}-${item.case_id}`}><span className={`priority ${item.priority}`}>{item.priority}</span><b>{role === "sales" ? item.business_name : item.case_type}</b><span>{role === "sales" ? `${item.contact_name} · ${item.city}` : item.case_id}</span><span className="muted">{item.status} · {item.owner}</span>{role === "partner" && <button className="text-button" onClick={() => assign(item)}>Assign to me →</button>}{role === "sales" && <button className="text-button" onClick={() => flash(`Follow-up opened for ${item.business_name}.`)}>Open lead →</button>}</div>) : <Empty title="Queue is clear" text="No current operational exceptions." />}</div></section>;
}
function Metric({ label, value, note }: { label: string; value: string | number; note: string }) { return <div className="metric-card"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>; }
function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) { return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>; }
function Loading({ text }: { text: string }) { return <div className="loading-card"><span className="spinner" />{text}</div>; }
function Empty({ title, text }: { title: string; text: string }) { return <div className="empty-state"><b>{title}</b><span>{text}</span></div>; }

export default App;
